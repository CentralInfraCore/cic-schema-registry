# StorageAdapter

**Réteg:** `general/storage/` — adapter kontraktus
**Kind:** `AdapterContract` (`domain: cic:storage:StorageResource`)

## Mit ír le ténylegesen ez a fájl

Ez NEM egy konkrét provider implementációja — ez az **interfész-szerződés**,
amit BÁRMELYIK konkrét storage-adapter implementációnak (Proxmox API,
NetApp ONTAP REST, AWS EBS API, stb.) teljesítenie kell, hogy egy
`StorageResource`-t ki tudjon szolgálni. Három művelete van:

| Művelet | Mit csinál | Kapcsolódás a `StorageResource`-hoz |
|---|---|---|
| `observe` | Volume állapotának lekérdezése, platform-specifikus értékek normalizálása | kimenete → `StorageResource.state_surface` |
| `apply` | Config alkalmazása, idempotens (csak a diff-et viszi át) | bemenete ← `StorageResource.config_surface` |
| `watch` | Folyamatos állapotfigyelés, event stream | kimenete → `StorageResource.notification_surface` |

Ez a három hivatkozás (`ref: StorageResource.state_surface` stb.) egy
**köztes erősségű kapcsolat** a két fájl között: nem típus-beágyazás (nem
veszi át a `StorageResource` mezőit), de nem is puszta névhivatkozás —
konkrét surface-re mutat, dotted-path formában. Ezt a `registrylib`
jelenleg NEM ellenőrzi (csak az `identity.base`/`reference_target`
pin-eket) — ismert, dokumentált rés.

## A három backend, amit lefed

`hypervisor` (Proxmox Storage API, libvirt storage pool, qemu-img),
`san` (NetApp ONTAP REST, Pure Storage API, iSCSI target), `cloud`
(AWS EBS API, GCP Persistent Disk API, Azure Disk API — `known_providers:
[aws, gcp, azure, hcloud, do, ovh, oci]`). Ezek **dokumentációs** mezők
(`protocol_examples`) — nem séma-szinten validált enumok, csak jelzik,
milyen valós rendszerek felelnek meg egy-egy backend-nek.

## `capability_declaration.known_implementations`

Konkrét, valós termékek (`proxmox-storage`, `netapp-ontap`, `aws-ebs`, stb.)
és az általuk ténylegesen támogatott capability-k listája — **illusztratív**
jellegű (dokumentálja, mit tud a valóságban egy adott implementáció), és
**nem azonos** a `storage-resource.yaml` saját
`binding_surface.adapter_capabilities.known_adapters` mezőjével (az
backend-enkénti, ez pedig konkrét-termék-enkénti bontás) — a kettő
egymástól függetlenül tud karban maradni, ez nem hiba, csak két különböző
célú capability-lista.

## Eredet / provenance / aláírás-ellenőrzés

Byte-azonos másolat a `cic-storage` repó `storage/@v0.1.2` tag-jéből
(`schemas/adapters/storage-adapter.yaml`), egyetlen ponton módosítva:
`metadata.version` a release verziójára (`v0.1.2`) lett állítva. Ugyanabban
a release bundle-ben van, mint a `storage-resource` — ugyanaz a kettős
aláírás (szerzői + CICSourceCA), ténylegesen `openssl`-lel ellenőrizve
(lásd `storage-resource/README.md` "Eredet / provenance" szakasza a
részletekért, mindkettőre ugyanaz vonatkozik).

**⚠ Fájlonkénti aláírás még nincs implementálva** ebben a registry-ben —
ez a fájl NEM hordoz saját `release`/`cic_countersign` blokkot.
