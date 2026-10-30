# The server runner — a deterministic program on the production server, driven by an orders repository · v2
### 28 October 2026 · v2 on 30 October: the orders repository, file-exchange bridge · proven on a real project (a web application under Docker Compose and two self-contained HTML pages)

*For a project whose deliverable runs **on a server the owner administers**. The PL deploys there themselves, on the
owner's “go”, without anyone dropping a file or running a command. The rest of the method does not change: the PL
briefs, accepts and deploys; the server runner executes; the owner decides and validates on screen.*

> **Optional module.** No production server, or hosting that already deploys from Git: **skip this guide.** The
> deliverable is then handed over to the owner as is (method §4).

*The reference implementation is in `templates/server-runner/` (at the root of the public repository, not translated).
Its code, its identifiers and its documentation are **in French**. It is read alongside this guide; it is not a
prerequisite: another program that keeps the same rules will do.*

---

## 1. When to use it, when not to

**Yes**: an application or files served by a machine you administer (a VM, a dedicated server, a machine at home),
where an accepted deliverable must today be dropped then launched by hand.

**No**:
- shared hosting, or a platform that already deploys from Git (Pages, PaaS): the push is enough;
- a deliverable that is not served (a PDF, an archive people download): it is handed over;
- a server you do not administer (no root, no systemd).

**What it changes**: the owner no longer drops anything. They say “go”, and validate on screen. The PL sees production
(version served, health, backup, counts) without the owner relaying a command output.

## 2. The roles, and the rule

| | does | does not |
|---|---|---|
| **PL** (cloud) | accepts, asks for the “go”, pushes the order, reads the report, tells the owner, merges after validation | never connects to the server; never restores a database |
| **Server runner** (the program; in a project, often “the deployer”) | pulls the orders, runs only its whitelist, checks health, rolls back when it is safe, pushes its report | decides nothing; never runs a command written in an order |
| **Owner** | installs once; says “go” naming the action; validates on screen; decides after a failure that touches the data | no longer drops anything, no longer runs anything, except as a fallback |
| **Dev** | builds the deliverable, as always | **never reads or writes the orders repository** |

**The rule: no AI in the deployment path.** Deployment is a deterministic program: same inputs, same result. **An agent
on a production server, if there is one, is bounded** — no secrets, no database writes, no root: a dedicated account
outside the `docker` group; `sudo` limited to a list (the server runner, reading the logs, the state of the containers, a
database client under a read-only role); the secrets file unreadable to it; never in a no-permissions mode, never
launched alone by a scheduled task. It calls the server runner, it does not replace it. *Why*: an agent with full
rights reads the secrets and the database, on a machine that goes out freely, and it reads content that users drop
(logs, titles, nicknames) — a booby-trapped text would be talking to an agent that can do anything.

## 3. The circuit, on the PL's side

```
PL (cloud)                       GitHub                           server
──────────                       ──────                           ──────
acceptance with no gap
owner: “go deployment v1.2.3”
pushes ordres/<id>.json  ──────► orders repository (private)
                                        ▲     │  every minute (systemd timer, outbound SSH)
                                        │     ▼
                                        │  server runner: new order? valid?
                                        │     ├─ fetches the commit (code repository: read-only key)
                                        │     ├─ backup read back, counts, deploys, health
                                        │     ├─ rolls back by itself when it is safe
                                        └─────┴─ pushes resultats/<id>.md
reads the report, tells the owner
“v1.2.3 served, health good,
  backup …, counts identical” ──► the owner validates on screen
merge into main
```

1. **An application that has users**: after an acceptance with no gap, the PL asks the owner for **a “go” that names the
   action** — “go deployment v1.2.3”, not “go” or “ok” — and quotes it word for word in the order's `go` field
   (lesson ④).
2. **They push `ordres/<id>.json`** to the orders repository. The identifier is `YYYY-MM-DD-NN`: **the next one in the
   repository, read after `git pull` and taken by the push** — push refused → `git pull`, next number, like a decision
   number. **An order is never written onto a file that exists**: the write refuses to overwrite (`set -o noclobber`
   before `cat >`, or an `[ -e ordres/<id>.json ]` test that stops everything) and, before the push,
   `git diff --cached --name-status` shows only **one line `A ordres/<id>.json`** — an `M` stops everything. A lesson learned the hard way:
   an identifier taken from a list read before the `git pull` overwrote, by `cat >`, the already-played order of
   another session; the push refused nothing (a modification, not an addition). An order is never rewritten: to
   correct, a new order.
3. **They read `resultats/<id>.md`**: one to two minutes normally. **Bounded wait** (a re-read every 20 to 30 s, a few
   minutes at most), **never an endless loop**; past the delay, they tell the owner and run `etat`.
4. **They tell the owner** the version served, the health, the backup taken and the counts before and after. The owner
   validates on screen; **then** the merge into `main`, as without a server runner. A failed report: the PL says so,
   with the backup's name; the database is restored only on the owner's decision, **by the manual procedure**.
5. **Static files with instant rollback** (a self-contained HTML page, no database and no restart): deployment
   **directly after acceptance, no go**; the owner then validates on screen.
6. **Rollback**: `revenir` — on go for the application, **refused after a migration**; without go for a static file.
7. **File operations** (dropping an archive, decompressing, switching a served folder): action `fichiers`, within
   **zones declared on the server side**, without go — except emptying the trash, the only real deletion, on go.
8. **Before a brief that touches production**, the PL runs `etat`: version served, containers, disk space, backups,
   counts. That is the probe, with no action from the owner.
9. **Data produced in a session** (a package of rendered pages, tomorrow tiles or maps) **to be served**: it goes through
   **the orders repository, which also serves as the file-exchange bridge** — never through the history of a public code
   repository (§5). The PL who produces it (never the dev):
   1. pushes it to the orders repository under `transfers/<domain>/<edition>/` — **a file of 95 MiB at most** —, after a
      `git pull`, and reads the full hash of the commit that carries it;
   2. **tells the owner what is going to be replaced** on the server, before the order that contains `basculer`;
   3. pushes a `fichiers` order (§7): `telecharger` **from the orders repository, at the 40-hex commit, sha256
      mandatory**, `decompresser` into a new folder, `basculer`;
   4. reads the report (bounded wait, point 3), tells the owner, who validates on screen;
   5. **removes the folder from the tree** by a commit once the report has succeeded: the history keeps the file, a partial
      copy at the commit reads only what is needed.

   Data produced **on the owner's PC** (captures, large backgrounds): `rsync` into `entree/` (§4), then a `fichiers` order.
   Data **published elsewhere** (a release, a known public repository, an authorized host): `telecharger` as for any file,
   without going through the bridge. *On the why — the options ruled out — and the step by step explained to the owner:
   `GUIDE.md` §2c.*

**Each PL who deploys attaches the orders repository with write access** at the start of the session. **The dev neither
reads nor writes it**: it is not in their command, and the dev prompt forbids it.

**The fallback**: when the server runner is down (or uninstalled), the deliverable is handed over to the owner as is,
under its exact name with its sha256, and the manual procedure of the code repository applies. Acceptance keeps
producing the archive: the fallback is always ready.

**Never a database restore by the server runner**: it is a manual procedure, written in the code repository, which
starts by backing up the present state.

## 4. Prerequisites

- **A Linux machine with systemd**, `git`, `python3` (3.11 or later for the reference implementation), and **outbound
  access to GitHub** (SSH, port 22).
- **Docker Compose** if there is an application; a **health route with no session** that returns the version served
  (`{"version": "1.2.3"}`), and a `VERSION` file at the root of the archive.
- **No inbound port.** The server fetches its orders; nobody gets in. The application's exposure (a tunnel, a proxy, a
  VPN) is none of the server runner's business.
- **Optional — dropping large files from the PC** (the PC route of the file-exchange bridge, §3 point 9): `rsync` over SSH
  into an `entree/` folder, with a restricted key
  (write-only, locked into that folder, no shell). You then need **a private path to the server's SSH port**: a VPN (for
  example Tailscale), a local network, or SSH exposed with key only. The network is named in the local runner's
  configuration (host, port, user), never in the method or in the code; changing it means changing the host and the
  firewall rule. **The firewall stays with the owner**: the installer does not touch it.
- **One-off root access** for installation (the host's web console or SSH): a single script to run.

## 5. The orders repository and the keys

**The orders repository**: a **private** repository, empty at creation, that the owner creates (`<owner>/<Project>-Orders`).

```
ordres/<id>.json                      written by the PL, never rewritten
resultats/<id>.md                     written by the server runner, one per order
transfers/<domain>/<edition>/…        the file-exchange bridge: written by the PL who produces the data, removed after use
LISEZ_MOI.md                          the order format (copy of docs/ORDRES.md from the implementation)
```

The folder names `ordres/` and `resultats/` stay in French: the reference implementation reads them. `transfers/` is a
convention of the method, not read by the program (see below). Written by the PL (the orders, the transfers) and by the
server (the reports), **never by the dev**. No secret, no production data in an order or in a report (the server filters
its logs before pushing them, §7).

**The file-exchange bridge — `transfers/`.** Data **produced in a cloud session** and to be served arrives through the
orders repository, under `transfers/<domain>/<edition>/` (`transfers/` and not `data/`: the server's zones often already
carry that name; the name is a convention of the method, the program only reads the path given by the order).
- **Who pushes there**: the PL who produces the data, never the dev. An edition has a new name, never rewritten.
- **Which key**: the same one, `cle_ordres`, that already reads the orders and pushes the reports; no extra key. Reading a
  file at a commit is done by a **partial copy of a single commit** (§13).
- **Which size**: **a file of 95 MiB at most** — the host refuses anything beyond 100 MB per file. Larger: split, or
  another route (the PC, an authorized host).
- **What becomes of the file**: once the report has succeeded, the PL removes the folder from the tree by a commit; the
  history keeps it. What is pushed is meant to be served: no secret, no personal data.
- **Point of attention — the runner's clone.** The runner keeps a clone of the orders repository, updated every minute.
  **If that clone is complete, the files pushed then removed stay in its history**, on the server's disk. The defence — a
  partial copy (without the files of `transfers/`), or `transfers/` outside the orders clone — **is decided at set-up**,
  from the inventory (§6); it is only quantified once the space has been measured.
- **Why not a separate repository**: one more deploy key, one more configuration line, one more repository to name in the
  handovers, for nothing the orders repository does not already bring (`GUIDE.md` §2c).

**The deploy keys**, generated on the server by the installer, **one per repository**:

| key | repository | right |
|---|---|---|
| `cle_ordres` | the orders repository | **write** (read the orders, push the reports) |
| `cle_app` | the application's code repository | **read-only** |

A deploy key is only valid for its repository: a compromised server rewrites neither the code, nor the batches, nor the
living docs. Static files come from **public** repositories, without a key. **A release attachment of a private
repository** cannot be read with a deploy key: it would need a fine-grained token, read-only, on the chosen repositories
only — to set only if a private release really serves as a source.

## 6. Installation, by a single script

**First a read-only probe** (lesson ⑤): the PL writes an inventory script that the owner drops and runs once — folder
and name of the Compose project (observed, not assumed), volumes and containers, what the folder holds outside the
archive (`.env`, `backups/`…), owner of the served folders, versions of the system, Git and Docker, disks and free
space, firewall, and, if there is a drop of files from the PC, SSH. The brief is based on its output.

**Then the installer** (`installer.sh` in the reference implementation), a single POSIX script, idempotent, to run as
root from the archive's folder:

```
sudo sh installer.sh
```

It checks the system, copies the program into a fresh folder of `/opt/deployeur/` (atomic switch of a link), writes the
configuration **only if it does not exist** and validates it, generates the two keys **only if they are missing**, checks
the published fingerprint of `github.com` before writing `known_hosts`, creates the missing zones and their trash, the
transfer account, sets up the systemd units and enables the timers; at the end, it shows the two public keys with the
instructions. **It touches neither the firewall, nor SSH, nor the Compose folder, nor Docker.**

**The values specific to the installation** are all in the “Valeurs de ce projet” (values of this project) block at the
top of the script, the only place where they appear — the program only knows the configuration:

| value | meaning |
|---|---|
| `PROJET`, `DOSSIER_COMPOSE`, `FICHIER_COMPOSE`, `SERVICE_APP`, `SERVICE_DB`, `CONTENEUR_DB` | the Compose project **as the inventory observed it** |
| `VOLUME_BASE`, `MONTAGE_BASE`, and the other irreplaceable volumes | what must never be lost (§8) |
| `PREFIXE_SAUVEGARDE`, `URL_SANTE`, `DELAI_SANTE_S`, `PLACE_MIN_DEPLOIEMENT_GO`, `SAUVEGARDES_GARDER` | backups, health, thresholds |
| `DEPOT_APPLICATION`, `DEPOT_ORDRES` | the two repositories (SSH addresses) |
| `TABLES_HISTOIRE` | the tables whose row count must never drop |
| `SUITES` | the static files: name, public repository, path in the repository, served folder and name |
| `ZONES`, `ZONE_TRANSFERT`, `PROPRIETAIRE_ZONES` | the zones of the file operations, the one that receives `entree/`, their owner |
| `DEPOTS_PUBLICS`, `HOTES_AUTORISES` | the authorized download sources |

**The owner, next**: on GitHub, **Settings → Deploy keys → Add deploy key**, twice — `cle_ordres` on the orders
repository **with** “Allow write access”, `cle_app` on the code repository **without**. Within a minute, the first run
finds the orders repository. Option: `sudo sh installer.sh --cle-transfert "<public key line of the PC>"` authorizes
dropping files from the PC.

**The script is tried before the server**: on a simulated machine (a test root, stand-ins for `systemctl`, `useradd`,
`docker`…), installation, reinstallation, update **and uninstallation included**; the reference implementation does it
in its tests (`INSTALLATEUR_PREFIXE`).

## 7. Orders and reports

An order is **a JSON object** in `ordres/<id>.json`: `id` (equal to the file name), `action`, `demande_par` (requested
by), and **exactly** the action's fields — an unknown or missing field refuses the order. The order is validated **in
full before any action**; a refusal moves nothing. An order is played only once; the orders of a queue are played one
at a time, in `id` order. **The protocol is neutral**: its action and field names do not name the project (lesson ①).
They are in French, as the reference implementation reads them.

**Two queues**, each with its own timer and lock, so that a long file operation never delays a deployment:
`deploiement` (`etat`, `adopter`, `deployer-application`, `deployer-suite`, `revenir`, `reprendre-file`) and `fichiers`
(`fichiers`). A **stopped** queue (after a failure that touches the data) refuses everything except `etat` and
`reprendre-file`. An order found “in progress” after an interruption becomes `interrompu` and **is never replayed**.

**`etat`** (state) — read-only, always accepted: version served, containers, project checks, commit served, migration
revision, counts of all tables, free space, latest backups, fingerprints of the served files, state of the queues,
recent orders.

```json
{"id": "2026-10-27-01", "action": "etat", "demande_par": "chef de projet"}
```

**`adopter`** (adopt) — declare, once, the commit already served: each file of its archive is compared with the served
folder; a single difference, refusal. No go.

```json
{"id": "2026-10-27-02", "action": "adopter", "demande_par": "chef de projet",
 "commit": "0123456789abcdef0123456789abcdef01234567"}
```

**`deployer-application`** (deploy the application) — on go. Preconditions (right project, space, commit present,
`VERSION` equal to `version`, no protected path in the archive); counts and revision before; **backup read back**;
laying down the files; build; recreation of the application service only; **health** (the route returns the expected
version, the log shows neither failure nor traceback); counts after. Failure without a migration: **automatic
rollback**. Failure after a migration: **no rollback**, queue stopped.

```json
{"id": "2026-10-27-03", "action": "deployer-application", "demande_par": "chef de projet",
 "commit": "0123456789abcdef0123456789abcdef01234567", "version": "1.2.3",
 "go": "“go deployment v1.2.3”, the owner, 27 October 10:42"}
```

**`deployer-suite`** (deploy a static file) — no go: downloaded at the commit, **sha256 from the acceptance checked**
(refusal if it differs, the served file intact); the old one becomes `<name>.prec<extension>`, the new one takes its
place by renaming.

```json
{"id": "2026-10-27-04", "action": "deployer-suite", "demande_par": "chef de projet", "suite": "suite-a",
 "commit": "0123456789abcdef0123456789abcdef01234567",
 "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
```

**`revenir`** (roll back) — the application on go (the previous commit, by the same path as the deployment; **refused if
a migration has been applied since**); a static file without go (the previous one becomes the served one again).

```json
{"id": "2026-10-27-05", "action": "revenir", "demande_par": "chef de projet", "cible": "application",
 "go": "“go rollback to the previous version”, the owner"}
```

```json
{"id": "2026-10-27-06", "action": "revenir", "demande_par": "chef de projet", "cible": "suite-a"}
```

**`reprendre-file`** (resume the queue) — reopen a stopped queue, on go, once the decision is made.

```json
{"id": "2026-10-27-07", "action": "reprendre-file", "demande_par": "chef de projet", "file": "deploiement",
 "go": "“go resume the deploiement queue”, the owner"}
```

**`fichiers`** (files) — 1 to 50 operations played in order; the first in error stops the order. Operations: `lister`
(list), `empreinte` (fingerprint), `creer-dossier` (create folder), `telecharger` (download: known public repository at a
commit, release of a known repository, authorized host, HTTPS only), `copier` (copy), `deplacer` (move), `decompresser`
(decompress `.tar`, `.tar.gz`, `.tgz`, `.zip` into a new folder), `basculer` (switch: a prepared folder replaces a
served folder), `mettre-a-la-corbeille` (move to trash), `vider-la-corbeille` (empty the trash, on go). **The zones are
declared on the server, never in the order**; every path is relative to a zone. **Nothing is erased** (everything goes
to `<zone>/_corbeille/<id>/`), **nothing is executed** (no execute bit set), **never a silent overwrite** (existing
target: refusal, unless `"si_existe": "remplacer"`, which moves the old one to the trash).

```json
{"id": "2026-10-27-08", "action": "fichiers", "demande_par": "chef de projet",
 "operations": [
   {"operation": "deplacer", "zone": "echange", "de": "entree/fond.tar.gz", "zone_vers": "donnees",
    "vers": "archives/fond.tar.gz"},
   {"operation": "decompresser", "zone": "donnees", "archive": "archives/fond.tar.gz", "vers": "cartes/fond-v2"},
   {"operation": "basculer", "zone": "donnees", "prepare": "cartes/fond-v2", "servi": "cartes/fond"}]}
```

**A package produced in a session, pushed to the orders repository** (§3 point 9) — `telecharger` from the orders
repository, **at the 40-hex commit, with the sha256** (mandatory for this source), then `decompresser` into a new folder and
`basculer`:

```json
{"id": "2026-10-27-11", "action": "fichiers", "demande_par": "chef de projet",
 "operations": [
   {"operation": "telecharger", "zone": "donnees", "chemin": "archives/pages-v2.tar.gz",
    "source": "github-prive:exemple/ordres@0123456789abcdef0123456789abcdef01234567:transfers/pages/v2/pages-v2.tar.gz",
    "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
   {"operation": "decompresser", "zone": "donnees", "archive": "archives/pages-v2.tar.gz", "vers": "pages/pages-v2"},
   {"operation": "basculer", "zone": "donnees", "prepare": "pages/pages-v2", "servi": "pages/pages"}]}
```

> **Coming in the reference implementation.** This form of source — the orders repository itself, private, read at the
> commit with the runner's key — **does not exist yet**: today the reference implementation only reads public repositories,
> releases and authorized hosts (`docs/ORDRES.md`). It arrives in its next version, in the form a first project built:
> the source `github-prive:<owner>/<repo>@<commit>:<path>`, sha256 mandatory, 95 MiB at most, for a repository declared
> in a `depots_prives` list of the configuration with its key — the orders repository is listed there with the key the
> runner already has for it. Until then, the PC route (`entree/`) or a source published elsewhere.

```json
{"id": "2026-10-27-09", "action": "fichiers", "demande_par": "chef de projet",
 "operations": [{"operation": "vider-la-corbeille", "zone": "donnees", "id_corbeille": "2026-10-20-03"}],
 "go": "“go empty the trash of order 2026-10-20-03”, the owner"}
```

**The report** — `resultats/<id>.md`, whose first line is `Statut : …` (in French, as written by the implementation):

| status | meaning |
|---|---|
| `réussi` (succeeded) | played to the end |
| `refusé` (refused) | validation, precondition or operation in error: nothing else moved than what it says |
| `échec, revenu` (failed, rolled back) | failure after the actions began; the rollback restored the previous state |
| `échec, file arrêtée` (failed, queue stopped) | failure that touches the data (migration applied, count dropped, rollback impossible); the queue waits for the owner's decision |
| `interrompu` (interrupted) | run cut off during the order; never replayed |
| `en cours` (in progress) | progress of a long operation |

Then come the order copied back, the times, the server runner's version; depending on the action, versions and commits
before and after, health, backup (names, sizes, checks), counts table by table (**drops in bold**), migration revision,
files laid down and unknown, free space; on failure, the step, the reason, what was put back and **what the owner must
decide**; finally the last lines of the application's log, **passed through the filter** (tokens, passwords, cookies,
URLs with secrets masked). Excerpt:

```markdown
Statut : réussi

# Compte rendu de l'ordre 2026-10-27-03

## Résumé

- version servie avant : 1.2.2 (commit 89abcdef…)
- révision de migration avant : 0039 ; après : 0039 (inchangée)
- version servie après : 1.2.3 (commit 01234567…) ; santé : bonne

## Sauvegarde

- monprojet_deploiement-0039_20261027-180003.dump (3.1 Mio ; 30 entrées TABLE DATA pour 29 tables)

## Comptes des tables

| table | avant | après |
|---|---:|---:|
| membres (histoire) | 120 | 120 |
```

The detail, field by field and with an example of each operation: `docs/ORDRES.md` of the implementation, copied as
`LISEZ_MOI.md` in the orders repository.

## 8. The data is never lost — the invariants

Non-negotiable; each has its test in the implementation and its check at acceptance. They hold for the database **and
for each irreplaceable volume** (files uploaded by users, raw uploads).

1. **The database service is never touched.** The server runner only runs the build and the recreation of the
   application service (`up -d --no-deps`); never `down`, never `-v`, never a removal or `prune` of a volume. These
   words are absent from the program, and a search in the code proves it.
2. **The right project or nothing.** Before any action, it checks that the volumes of the expected Compose project exist
   and carry its label, and that the running database container is indeed mounted on them. Otherwise: refusal. This is
   the defence against **the empty database**: Compose names the project after the folder, and a deployment into another
   folder would start a new database on new volumes. Hence also: **the same folder at every deployment**, never a folder
   per version.
3. **A backup at every deployment of the application**, migration or not: dump of the database and archive of the other
   volumes, checked non-empty and **read back** (`pg_restore --list`, archive read in full), **before** the build. Backup
   failure: no deployment.
4. **Counts before and after.** Read-only, the row count of the tables that carry the project's history (the users,
   their registrations, their content, the activity logs — the list is fixed at the brief, from the inventory). A count
   that drops stops the queue, even if health is good.
5. **Never an automatic restore.** The automatic rollback only puts back code, and only with no migration applied. A
   restore is done by hand, on the owner's decision, and starts by backing up the present state.
6. **A minimum retention**: the server runner's last three backups always stay, whatever the retention set elsewhere; a
   backup of another family is never purged by it. The full server backup, if there is one, remains the last net.
7. **The dry run proves it** (§9).

**Setting them for your project**: the volumes and the database mount point, recorded by the inventory (the reference
implementation expects three volumes — the database and two others; with fewer, adapt `deployeur/base.py`); the history
tables, chosen among those the application never empties by itself (a session or cache table does not belong there: its
count drops normally); the archive's **protected paths** — `.env` and `backups/` by default —, and any others, **run
against the real archive before briefing** (lesson ②).

## 9. The dry run, then the first real deployment

**The dry run** proves the whole chain **without changing anything**: the test commit is the one already served.

1. `etat`: version served, project checks compliant, counts, space, backups, queues “running”.
2. `adopter` of the served commit: all files identical, otherwise the differences listed and nothing kept.
3. `deployer-application` of **the same commit and the same version**, with a go: counts identical before and after,
   backup present and read back, service recreated, health good.
4. `revenir` the application, with a go: the full path replayed with no change.
5. A static file in a round trip: `deployer-suite` of the served file (its commit, its sha256), then `revenir`.
6. A few file operations in a zone: `creer-dossier`, `lister`, `mettre-a-la-corbeille`.
7. **What the operator sees**: if the owner drops or looks at files through a graphical tool (a web file manager), check
   that it sees `entree/` and the zones — a symbolic link may not be followed there (lesson ③).

The automatic rollback after a health failure is not tried in production: it is proven by the tests, on Docker
stand-ins.

**The first real deployment**: the next batch, through the circuit of §3 — named go, order, report read, validation on
screen, merge. The PL notes in the project's method that the order circuit is in service and that the hand-over becomes
the fallback.

## 10. Troubleshooting, uninstallation, back to manual drop

- **See what the program does**: the logs of the two services (`journalctl -u deployeur-deploiement.service`,
  `deployeur-fichiers.service`) and the list of timers. The PL, for their part, runs `etat`.
- **Order refused**: the report says why; nothing moved. Correct, send **a new order** (new `id`).
- **Order not played**: the file name equal to the `id`, pushed on `main` of the orders repository, the orders key
  declared **with** write access; the log says “dépôt d'ordres inaccessible” (orders repository unreachable) if the key
  or the network is missing.
- **Report missing**: a failed push is replayed at the next run; beyond the bounded wait, `etat`.
- **Health failure**: without a migration, the automatic rollback has happened (`échec, revenu`); the filtered log says
  why. The fix makes a batch of the next version.
- **Stopped queue**: the report of the faulty order names the cause and the backups; the owner decides (keep the new
  code, or restore by hand); then `reprendre-file` on go.
- **Disk space**: below the threshold, writes are refused; `vider-la-corbeille` (on go) is the only deletion.
- **Invalid configuration**: the program refuses to run and lists each problem; correct, check again
  (`python3 -m deployeur --verifier`).
- **Uninstall**: `sudo sh installer.sh --desinstaller` removes the units, the timers and the program; it **keeps** the
  configuration, the keys, the state, the zones and the transfer account, and says so.
- **Back to manual drop**: stop the timers (or uninstall), remove the two deploy keys on GitHub; the hand-over of the
  deliverable and the manual procedure resume, the project's method notes it. The orders repository stays, as history.

## 11. Security: what the model protects, what it does not

**It protects**:
- **the network surface**: no inbound port, no new exposed service; everything is outbound;
- **the code and the other repositories**: one key per repository, write access to the orders repository only;
- **against an arbitrary order**: a whitelist of actions, exact fields, no command composed from an order's content, a
  single module that launches processes, with no shell;
- **the data**: the invariants of §8;
- **the secrets**: the environment file stays on the server, outside the archive (protected path), never read by the
  program; any log text goes through the filter before being pushed;
- **the files**: zones declared on the server, paths resolved and links rejected if they leave the zone, decompression
  checked member by member, trash, no execute bit;
- **the drop from the PC**: a key that only opens `rsync` write-only, without deletion, into `entree/`.

**It does not protect**:
- **whoever can push to the orders repository deploys** — within the limits of the whitelist. It is the same level of
  trust as “the owner drops what the PL hands over”; it is held by limiting who has write access to that repository (the
  owner and the PL sessions they attach to it);
- **a bad but accepted commit**: the identity is the commit, and the gate is the acceptance, then the go;
- **the program itself**: it runs as root (Docker amounts to root). Hence a short program, read in full at acceptance,
  and its updates accepted like a batch;
- **an authorized external source** whose content changes: the sha256 only protects if it is given in the order;
- **disk or server failure**: the full server backup remains the last net;
- **filling up** `entree/` through the transfer key: the space thresholds refuse the following writes, they do not
  block the drop.

## 12. The lessons of going into service

1. **A brief that forbids names in the code must not impose them on the protocol.** The dev stopped, rightly, on action
   names that named the project: the protocol (actions, fields, formats) is neutral; proper names live in the
   configuration only.
2. **A protected-path pattern is run against the real archive before briefing.** `.env.*` caught `.env.example`, which
   the application ships in its archive, and blocked the adoption of the served commit.
3. **The dry run checks that the operator's graphical tool sees what is prepared for them**: a web file manager did not
   follow a symbolic link set up for it.
4. **The session's tooling can block the push of a production order on an ambiguous “go”**: ask for a go that names the
   action, and quote it in the order.
5. **A read-only probe before any script that modifies the system** (inventory, disk probe), and the script is tried on
   a simulated machine, rollback included.
6. **Data produced in a session arrives through the orders repository, not through one more repository.** A private data
   repository had been decided, then dropped the same evening: the orders repository, already read and already written,
   makes the bridge (`transfers/`); never the history of a public code repository, where every edition would stay forever.

## 13. The reference implementation

`templates/server-runner/` (at the root of the public repository): the program (`deployeur/`, Python, standard library
only), its systemd units (`systemd/`), the installer (`installer.sh`), an example configuration (`config.exemple.json`),
its documentation (`docs/INSTALLATION.md`, `docs/ORDRES.md`) and its tests (`tests/`, no network: a fake `docker`, a fake
HTTPS transport, local Git repositories; those of the installer need root and `ssh-keygen`).

- **Everything there is in French** — code, identifiers, messages, documentation, reports. Translating it is not needed
  to use it; the protocol is described in English in this guide.
- **All values are examples** (`monprojet`, `/srv/monprojet`, `exemple/application`, `exemple/ordres`, `suite-a`, the
  zones `donnees` and `echange`, `exemple.org`, the account `exploitant`): they are replaced in the “Valeurs de ce projet”
  block of `installer.sh`, and nowhere else.
- **The target stack**: Docker Compose, PostgreSQL, a JSON health route, static files pulled from public repositories.
  Another stack is adapted in `deployeur/application.py`, `deployeur/base.py` and `deployeur/commandes.py`, through a
  tooling batch, briefed by the PL, built by the dev, accepted by reading the whole program.
- **It does not yet have the private source of `telecharger`** — the one that reads a file of the orders repository at a
  commit, by a partial copy of a single commit, with the key the runner already holds for that repository (§5, §7): it
  arrives in its next version. The file-exchange bridge (§3 point 9) is described here; its “session” route only works with
  that version. The PC route (`entree/`) and the route of a source published elsewhere already work.
- **It is taken into one of the project's code repositories** (private), like any deliverable: versioned, with its
  `CHANGELOG`, its tests in the test bench, and its updates deployed by the installer.
