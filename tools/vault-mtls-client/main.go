// vault-mtls-client demonstrates completing a full mTLS handshake and a
// countersign request using a private key that never leaves Vault: the
// TLS ClientHello's CertificateVerify signature, and the countersign
// request's own "sign" field, are both produced by calling Vault Transit's
// /transit/sign endpoint through a custom crypto.Signer — the raw EC key
// bytes are never read into this process.
package main

import (
	"bytes"
	"crypto"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
)

// vaultSigner implements crypto.Signer by delegating every signature to a
// Vault Transit key. It never holds key material.
type vaultSigner struct {
	addr      string
	token     string
	keyName   string
	pub       crypto.PublicKey
	client    *http.Client
}

func (s *vaultSigner) Public() crypto.PublicKey { return s.pub }

func (s *vaultSigner) Sign(_ io.Reader, digest []byte, _ crypto.SignerOpts) ([]byte, error) {
	reqBody, _ := json.Marshal(map[string]any{
		"input":          base64.StdEncoding.EncodeToString(digest),
		"prehashed":      true,
		"hash_algorithm": "sha2-256",
	})
	url := fmt.Sprintf("%s/v1/transit/sign/%s", strings.TrimRight(s.addr, "/"), s.keyName)
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(reqBody))
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Vault-Token", s.token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("vault sign returned %d: %s", resp.StatusCode, body)
	}

	var out struct {
		Data struct {
			Signature string `json:"signature"`
		} `json:"data"`
		Errors []string `json:"errors"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, err
	}
	if len(out.Errors) > 0 {
		return nil, fmt.Errorf("vault: %s", strings.Join(out.Errors, "; "))
	}
	der, err := base64.StdEncoding.DecodeString(strings.TrimPrefix(out.Data.Signature, "vault:v1:"))
	if err != nil {
		return nil, err
	}
	return der, nil
}

func vaultCAPool(path string) *x509.CertPool {
	pool := x509.NewCertPool()
	b, err := os.ReadFile(path)
	if err != nil {
		log.Fatalf("reading %s: %v", path, err)
	}
	if !pool.AppendCertsFromPEM(b) {
		log.Fatalf("no certs found in %s", path)
	}
	return pool
}

func main() {
	// --- Vault holding the real developer identity key (cic-my-sign-key) ---
	devVaultAddr := os.Getenv("DEV_VAULT_ADDR")
	devVaultToken := os.Getenv("DEV_VAULT_TOKEN")
	devVaultCA := os.Getenv("DEV_VAULT_CA_FILE")
	devKeyName := envOr("DEV_VAULT_KEY_NAME", "cic-my-sign-key")
	certFile := os.Getenv("SIGNER_CERT_FILE")

	// --- countersign-server itself ---
	serverAddr := os.Getenv("COUNTERSIGN_ADDR")
	serverCAFile := os.Getenv("COUNTERSIGN_CA_FILE")
	buildHash := os.Getenv("BUILD_HASH") // base64, already computed
	documentJSON := envOr("DOCUMENT_JSON", `{"kind":"project","version":"vault-signer-e2e"}`)
	workflow := envOr("WORKFLOW", "vault-signer-e2e@v0")

	certPEM, err := os.ReadFile(certFile)
	if err != nil {
		log.Fatalf("reading signer cert: %v", err)
	}
	block, _ := pem.Decode(certPEM)
	if block == nil {
		log.Fatal("signer cert: no PEM block")
	}
	leaf, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		log.Fatalf("parsing signer cert: %v", err)
	}

	vaultHTTPClient := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{RootCAs: vaultCAPool(devVaultCA)},
		},
	}

	signer := &vaultSigner{
		addr:    devVaultAddr,
		token:   devVaultToken,
		keyName: devKeyName,
		pub:     leaf.PublicKey,
		client:  vaultHTTPClient,
	}

	// The countersign request's own "sign" field (application-level, not
	// TLS) — same Vault key, same delegation, produced explicitly here so
	// it is logged and inspectable rather than hidden inside the TLS lib.
	digest, err := base64.StdEncoding.DecodeString(buildHash)
	if err != nil {
		log.Fatalf("BUILD_HASH is not valid base64: %v", err)
	}
	sigDER, err := signer.Sign(nil, digest, crypto.SHA256)
	if err != nil {
		log.Fatalf("vault-signing build_hash failed: %v", err)
	}
	appSign := "vault:v1:" + base64.StdEncoding.EncodeToString(sigDER)
	fmt.Println("[*] application-level sign (build_hash), produced via Vault:", appSign)

	var document map[string]any
	if err := json.Unmarshal([]byte(documentJSON), &document); err != nil {
		log.Fatalf("DOCUMENT_JSON invalid: %v", err)
	}

	reqBody, _ := json.Marshal(map[string]any{
		"document":           document,
		"build_hash":         buildHash,
		"sign":               appSign,
		"signer_certificate": string(certPEM),
		"workflow":           workflow,
	})

	// --- The mTLS client cert whose PRIVATE KEY OPERATION never leaves Vault ---
	tlsCert := tls.Certificate{
		Certificate: [][]byte{leaf.Raw},
		PrivateKey:  signer,
		Leaf:        leaf,
	}

	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				Certificates: []tls.Certificate{tlsCert},
				RootCAs:      vaultCAPool(serverCAFile),
			},
		},
	}

	fmt.Println("[*] opening mTLS connection, TLS handshake signature also via Vault...")
	resp, err := client.Post("https://"+serverAddr+"/v1/countersign", "application/json", bytes.NewReader(reqBody))
	if err != nil {
		log.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	fmt.Printf("HTTP_STATUS=%d\n%s\n", resp.StatusCode, respBody)
}

func envOr(name, def string) string {
	if v := os.Getenv(name); v != "" {
		return v
	}
	return def
}
