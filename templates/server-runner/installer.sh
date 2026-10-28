#!/bin/sh
# Installateur du déployeur — POSIX sh, à lancer en root depuis le dossier de l'archive :
#     sudo sh installer.sh
#     sudo sh installer.sh --cle-transfert "<ligne de clé publique>"
#     sudo sh installer.sh --desinstaller
# Idempotent : on peut le relancer sans rien casser. Il ne touche ni au pare-feu, ni à SSH (sshd_config),
# ni au dossier Compose, ni à Docker. Il ne lance jamais de commande composée à partir d'un fichier lu.
set -eu

# ================================================================================================
# Valeurs de ce projet
# (seul endroit du dépôt où elles apparaissent ; le programme, lui, ne connaît que la configuration)
# ================================================================================================
# Valeurs d'EXEMPLE : à remplacer toutes par celles de votre serveur avant le premier lancement.
PROJET=monprojet
DOSSIER_COMPOSE=/srv/monprojet
FICHIER_COMPOSE=docker-compose.yml
SERVICE_APP=app
SERVICE_DB=db
CONTENEUR_DB=monprojet-db-1
VOLUME_BASE=monprojet_pgdata
MONTAGE_BASE=/var/lib/postgresql/data
# Les deux autres volumes irremplaçables (fichiers déposés par les utilisateurs, dépôts bruts)
VOLUME_ECUSSONS=monprojet_images
VOLUME_DEPOTS_BRUTS=monprojet_bruts
PREFIXE_SAUVEGARDE=monprojet
URL_SANTE=http://127.0.0.1:8000/api/version
DEPOT_APPLICATION=git@github.com:exemple/application.git
DEPOT_ORDRES=git@github.com:exemple/ordres.git
IDENTITE_GIT_NOM="Deployeur VM"
IDENTITE_GIT_COURRIEL=deployeur@localhost
# Une suite par ligne : nom|dépôt public|chemin dans le dépôt|dossier servi|nom du fichier servi
SUITES='suite-a|exemple/suite-a|dist/suite_a.html|/srv/suites|suite_a.html
suite-b|exemple/suite-b|dist/suite_b.html|/srv/suites|suite_b.html'
# Une zone par ligne : nom|chemin absolu|place minimale (Go)
ZONES='donnees|/srv/donnees|20
echange|/srv/donnees/echange|20'
ZONE_TRANSFERT=echange
# Compte propriétaire des zones que l'installateur crée et de entree/ (il doit exister ; sinon l'installateur s'arrête)
PROPRIETAIRE_ZONES=exploitant
DEPOTS_PUBLICS="exemple/suite-a exemple/suite-b exemple/outils"
HOTES_AUTORISES="exemple.org"
TABLES_HISTOIRE="membres groupes adhesions evenements inscriptions documents journal_activite"
PLACE_MIN_DEPLOIEMENT_GO=3
SAUVEGARDES_GARDER=10
DELAI_SANTE_S=180
# Lien posé s'il n'existe rien à ce chemin, pour que le gestionnaire de fichiers montre le dossier de transfert
LIEN_FICHIERS=/srv/outils/echange
# ================================================================================================
# Fin des valeurs de ce projet
# ================================================================================================

# Constantes de l'installateur
EMPREINTE_GITHUB='SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU'
COMPTE_TRANSFERT=transfert
OPT=/opt/deployeur
CONF=/etc/deployeur
ETAT=/var/lib/deployeur
UNITES="deployeur-deploiement.service deployeur-deploiement.timer deployeur-fichiers.service deployeur-fichiers.timer"
# Préfixe de racine, pour essayer l'installateur dans un dossier d'essai (vide en production)
P=${INSTALLATEUR_PREFIXE:-}

die() {
    printf 'ERREUR : %s\n' "$*" >&2
    exit 1
}

etape() {
    printf '\n== %s\n' "$*"
}

dit() {
    printf '   %s\n' "$*"
}

usage() {
    cat <<'FIN'
Usage : sudo sh installer.sh [--cle-transfert "<ligne de clé publique>"] [--desinstaller] [--aide]

  (sans option)       installe ou met à jour le déployeur ; relançable sans risque
  --cle-transfert     autorise une clé publique SSH (celle du PC) à déposer des fichiers dans entree/ — rien d'autre
  --desinstaller      arrête et retire les unités, les minuteurs et /opt/deployeur ;
                      garde /etc/deployeur, /var/lib/deployeur, les zones et le compte de transfert
FIN
}

CLE_TRANSFERT=""
CLE_DEMANDEE=0
MODE=installer
while [ $# -gt 0 ]; do
    case "$1" in
        --cle-transfert)
            [ $# -ge 2 ] || die "--cle-transfert attend une ligne de clé publique entre guillemets"
            CLE_TRANSFERT=$2
            CLE_DEMANDEE=1
            shift 2
            ;;
        --desinstaller)
            MODE=desinstaller
            shift
            ;;
        --aide | -h | --help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            die "option inconnue : $1"
            ;;
    esac
done

# Une valeur de configuration ne doit contenir ni guillemet, ni barre oblique inverse, ni saut de ligne.
sur() {
    sur_nom=$1
    sur_valeur=$2
    [ -n "$sur_valeur" ] || die "valeur vide : $sur_nom"
    case "$sur_valeur" in
        *'"'* | *\\*) die "caractère interdit dans $sur_nom" ;;
    esac
    case "$sur_valeur" in
        *'
'*) die "saut de ligne interdit dans $sur_nom" ;;
    esac
}

# Idem pour une valeur de plusieurs lignes (une entrée par ligne).
sur_lignes() {
    sur_nom=$1
    sur_valeur=$2
    [ -n "$sur_valeur" ] || die "valeur vide : $sur_nom"
    case "$sur_valeur" in
        *'"'* | *\\*) die "caractère interdit dans $sur_nom" ;;
    esac
}

depot_court() {
    # git@github.com:Proprietaire/Depot.git -> Proprietaire/Depot
    d=${1#git@github.com:}
    printf '%s' "${d%.git}"
}

# ------------------------------------------------------------------------------------------------
# Désinstallation
# ------------------------------------------------------------------------------------------------
if [ "$MODE" = desinstaller ]; then
    [ "$(id -u)" = 0 ] || die "à lancer en root (sudo sh installer.sh --desinstaller)"
    command -v systemctl >/dev/null 2>&1 || die "systemctl introuvable"
    etape "Désinstallation : unités et minuteurs"
    for t in deployeur-deploiement.timer deployeur-fichiers.timer; do
        systemctl disable --now "$t" >/dev/null 2>&1 || dit "minuteur $t déjà arrêté ou absent"
    done
    for u in $UNITES; do
        rm -f -- "$P/etc/systemd/system/$u"
    done
    systemctl daemon-reload
    etape "Désinstallation : le programme"
    rm -rf -- "${P}${OPT:?}"
    etape "Terminé"
    dit "Retiré : les quatre unités systemd et $OPT."
    dit "GARDÉ : $CONF (configuration et clés), $ETAT (état, miroir, archives), les zones et leur corbeille,"
    dit "        le compte « $COMPTE_TRANSFERT » et ses clés autorisées. À retirer à la main si on le souhaite."
    exit 0
fi

# ------------------------------------------------------------------------------------------------
# 1. Vérifications
# ------------------------------------------------------------------------------------------------
etape "1. Vérifications"
[ "$(id -u)" = 0 ] || die "à lancer en root (sudo sh installer.sh)"
if [ -r "$P/etc/os-release" ] && grep -Eq '^(ID|ID_LIKE)=.*debian' "$P/etc/os-release"; then
    dit "système : Debian (ou dérivé), ok"
else
    die "ce script est écrit pour Debian"
fi
command -v python3 >/dev/null 2>&1 || die "python3 introuvable"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || die "python3 3.11 ou plus récent requis"
dit "python3 : ok"
for c in git systemctl flock ssh-keygen ssh-keyscan; do
    command -v "$c" >/dev/null 2>&1 || die "commande introuvable : $c"
done
docker compose version >/dev/null 2>&1 || die "« docker compose » introuvable"
dit "git, docker compose, systemctl, flock, ssh-keygen, ssh-keyscan : ok"
# Valeurs du bloc « Valeurs de ce projet »
sur PROJET "$PROJET"
sur DOSSIER_COMPOSE "$DOSSIER_COMPOSE"
sur FICHIER_COMPOSE "$FICHIER_COMPOSE"
sur SERVICE_APP "$SERVICE_APP"
sur SERVICE_DB "$SERVICE_DB"
sur CONTENEUR_DB "$CONTENEUR_DB"
sur VOLUME_BASE "$VOLUME_BASE"
sur MONTAGE_BASE "$MONTAGE_BASE"
sur VOLUME_ECUSSONS "$VOLUME_ECUSSONS"
sur VOLUME_DEPOTS_BRUTS "$VOLUME_DEPOTS_BRUTS"
sur PREFIXE_SAUVEGARDE "$PREFIXE_SAUVEGARDE"
sur URL_SANTE "$URL_SANTE"
sur DEPOT_APPLICATION "$DEPOT_APPLICATION"
sur DEPOT_ORDRES "$DEPOT_ORDRES"
sur IDENTITE_GIT_NOM "$IDENTITE_GIT_NOM"
sur IDENTITE_GIT_COURRIEL "$IDENTITE_GIT_COURRIEL"
sur ZONE_TRANSFERT "$ZONE_TRANSFERT"
sur PROPRIETAIRE_ZONES "$PROPRIETAIRE_ZONES"
sur PLACE_MIN_DEPLOIEMENT_GO "$PLACE_MIN_DEPLOIEMENT_GO"
sur SAUVEGARDES_GARDER "$SAUVEGARDES_GARDER"
sur DELAI_SANTE_S "$DELAI_SANTE_S"
sur LIEN_FICHIERS "$LIEN_FICHIERS"
sur_lignes SUITES "$SUITES"
sur_lignes ZONES "$ZONES"
sur DEPOTS_PUBLICS "$DEPOTS_PUBLICS"
sur HOTES_AUTORISES "$HOTES_AUTORISES"
sur TABLES_HISTOIRE "$TABLES_HISTOIRE"

if command -v rsync >/dev/null 2>&1; then
    dit "rsync : déjà installé"
else
    dit "rsync manquant : installation par apt-get (seule action apt de l'installateur)"
    apt-get install -y rsync
fi
[ -x /usr/bin/rrsync ] || [ -x "$P/usr/bin/rrsync" ] || die "/usr/bin/rrsync introuvable après l'installation de rsync"
dit "rrsync : ok"

SOURCE=$(cd "$(dirname "$0")" && pwd)
if [ ! -d "$SOURCE/deployeur" ] || [ ! -d "$SOURCE/systemd" ] || [ ! -f "$SOURCE/VERSION" ]; then
    die "lancer l'installateur depuis le dossier de l'archive (deployeur/, systemd/ et VERSION attendus à côté)"
fi
VERSION=$(tr -d '[:space:]' <"$SOURCE/VERSION")
case "$VERSION" in
    '' | *[!0-9A-Za-z._-]*) die "fichier VERSION invalide" ;;
esac
dit "version à installer : $VERSION"
id -u "$PROPRIETAIRE_ZONES" >/dev/null 2>&1 \
    || die "le compte « $PROPRIETAIRE_ZONES » (propriétaire des zones et de entree/) n'existe pas sur cette machine"
dit "compte propriétaire des zones : $PROPRIETAIRE_ZONES (existe)"

# Chemin du dossier de transfert (zone de transfert + entree/)
ZONE_TRANSFERT_CHEMIN=""
while IFS='|' read -r nom chemin place; do
    [ -n "$nom" ] || continue
    sur "zone $nom" "$chemin"
    sur "place de la zone $nom" "$place"
    if [ "$nom" = "$ZONE_TRANSFERT" ]; then
        ZONE_TRANSFERT_CHEMIN=$chemin
    fi
done <<FIN
$ZONES
FIN
[ -n "$ZONE_TRANSFERT_CHEMIN" ] || die "la zone de transfert « $ZONE_TRANSFERT » n'est pas déclarée dans ZONES"
ENTREE="$ZONE_TRANSFERT_CHEMIN/entree"

# ------------------------------------------------------------------------------------------------
# 2. Le programme
# ------------------------------------------------------------------------------------------------
etape "2. Copie du programme dans $OPT"
# Le programme d'un passage en cours ne doit jamais être retiré sous lui : on copie dans un dossier neuf voisin
# ($VERSION.nouveau, ou $VERSION si c'est lui qui est en service), on bascule « courant » dessus par lien et renommage
# atomiques, et l'ancien dossier de la même version n'est retiré qu'à l'étape 10, une fois les deux verrous pris puis relâchés.
install -d -m 755 "$P$OPT"
ANCIEN=""
if [ -L "$P$OPT/courant" ]; then
    ANCIEN=$(readlink "$P$OPT/courant" || true)
fi
case "$ANCIEN" in
    "$VERSION") NEUF="$VERSION.nouveau" ;;
    *) NEUF=$VERSION ;;
esac
DEST="$P$OPT/$NEUF"
rm -rf -- "${DEST:?}"
install -d -m 755 "$DEST"
cp -R "$SOURCE/deployeur" "$SOURCE/systemd" "$DEST/"
for f in config.exemple.json VERSION README.md CHANGELOG.md; do
    [ -f "$SOURCE/$f" ] && cp "$SOURCE/$f" "$DEST/$f"
done
[ -d "$SOURCE/docs" ] && cp -R "$SOURCE/docs" "$DEST/"
find "$DEST" -depth -name '__pycache__' -type d -exec rm -rf {} +
chown -R root:root "$DEST"
chmod -R go-w "$DEST"
ln -sfn "$NEUF" "$P$OPT/courant.nouveau"
mv -T "$P$OPT/courant.nouveau" "$P$OPT/courant"
dit "$OPT/courant -> $NEUF"

# ------------------------------------------------------------------------------------------------
# 3. La configuration
# ------------------------------------------------------------------------------------------------
json_tables() {
    premier=1
    printf '['
    for t in $TABLES_HISTOIRE; do
        if [ "$premier" = 1 ]; then premier=0; else printf ', '; fi
        printf '"%s"' "$t"
    done
    printf ']'
}

json_depots_publics() {
    premier=1
    printf '['
    for t in $DEPOTS_PUBLICS; do
        if [ "$premier" = 1 ]; then premier=0; else printf ', '; fi
        printf '"%s"' "$t"
    done
    printf ']'
}

json_hotes() {
    premier=1
    printf '['
    for t in $HOTES_AUTORISES; do
        if [ "$premier" = 1 ]; then premier=0; else printf ', '; fi
        printf '"%s"' "$t"
    done
    printf ']'
}

json_suites() {
    premier=1
    while IFS='|' read -r nom depot chemin dossier fichier; do
        [ -n "$nom" ] || continue
        if [ "$premier" = 1 ]; then premier=0; else printf ',\n'; fi
        printf '    "%s": {"depot": "%s", "chemin": "%s", "dossier": "%s", "fichier": "%s"}' \
            "$nom" "$depot" "$chemin" "$dossier" "$fichier"
    done <<FIN
$SUITES
FIN
    printf '\n'
}

json_zones() {
    premier=1
    while IFS='|' read -r nom chemin place; do
        [ -n "$nom" ] || continue
        if [ "$premier" = 1 ]; then premier=0; else printf ',\n'; fi
        printf '    "%s": {"chemin": "%s", "place_min_go": %s}' "$nom" "$chemin" "$place"
    done <<FIN
$ZONES
FIN
    printf '\n'
}

ecrire_config() {
    cat <<FIN
{
  "repertoire_etat": "$ETAT",
  "git": {
    "cle_ordres": "$CONF/cle_ordres",
    "cle_application": "$CONF/cle_app",
    "known_hosts": "$CONF/known_hosts",
    "identite_nom": "$IDENTITE_GIT_NOM",
    "identite_courriel": "$IDENTITE_GIT_COURRIEL"
  },
  "depot_ordres": {"url": "$DEPOT_ORDRES", "branche": "main"},
  "application": {
    "projet": "$PROJET",
    "dossier": "$DOSSIER_COMPOSE",
    "fichier_compose": "$FICHIER_COMPOSE",
    "service_app": "$SERVICE_APP",
    "service_db": "$SERVICE_DB",
    "conteneur_db": "$CONTENEUR_DB",
    "volume_base": "$VOLUME_BASE",
    "montage_base": "$MONTAGE_BASE",
    "volume_ecussons": "$VOLUME_ECUSSONS",
    "volume_depots_bruts": "$VOLUME_DEPOTS_BRUTS",
    "prefixe_sauvegarde": "$PREFIXE_SAUVEGARDE",
    "url_sante": "$URL_SANTE",
    "depot_url": "$DEPOT_APPLICATION",
    "tables_histoire": $(json_tables),
    "chemins_proteges": [],
    "place_min_deploiement_go": $PLACE_MIN_DEPLOIEMENT_GO,
    "sauvegardes_garder": $SAUVEGARDES_GARDER,
    "delai_sante_s": $DELAI_SANTE_S
  },
  "suites": {
$(json_suites)
  },
  "hote_fichiers_bruts": "raw.githubusercontent.com",
  "zones": {
$(json_zones)
  },
  "zone_transfert": "$ZONE_TRANSFERT",
  "depots_publics": $(json_depots_publics),
  "hotes_autorises": $(json_hotes),
  "intervalle_en_cours_s": 300
}
FIN
}

etape "3. Configuration $CONF/config.json"
install -d -m 700 "$P$CONF"
chmod 700 "$P$CONF"
if [ -e "$P$CONF/config.json" ]; then
    dit "la configuration existe : elle est gardée telle quelle (non modifiée)"
else
    ecrire_config >"$P$CONF/config.json.nouveau"
    chmod 600 "$P$CONF/config.json.nouveau"
    mv "$P$CONF/config.json.nouveau" "$P$CONF/config.json"
    dit "configuration écrite (600) depuis le bloc « Valeurs de ce projet »"
fi
chmod 600 "$P$CONF/config.json"
(cd "$P$OPT/courant" && python3 -m deployeur --verifier --config "$P$CONF/config.json") \
    || die "la configuration $CONF/config.json est invalide (zone interdite, chemin relatif, clé manquante…) : corriger puis relancer"

# ------------------------------------------------------------------------------------------------
# 4. Les clés
# ------------------------------------------------------------------------------------------------
etape "4. Clés SSH du déployeur (ed25519, sans phrase de passe)"
for cle in cle_ordres cle_app; do
    if [ -e "$P$CONF/$cle" ]; then
        dit "$cle : existe déjà, gardée"
    else
        ssh-keygen -q -t ed25519 -N "" -C "deployeur-$cle@$(hostname)" -f "$P$CONF/$cle"
        dit "$cle : générée"
    fi
    chmod 600 "$P$CONF/$cle"
    chmod 644 "$P$CONF/$cle.pub"
done

# ------------------------------------------------------------------------------------------------
# 5. known_hosts
# ------------------------------------------------------------------------------------------------
etape "5. known_hosts de GitHub (empreinte contrôlée)"
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT
ssh-keyscan -T 10 -t ed25519 github.com 2>/dev/null | grep -v '^#' >"$TMP/kh" || true
[ -s "$TMP/kh" ] || die "ssh-keyscan n'a rien rendu pour github.com (réseau ?)"
EMPREINTE=$(ssh-keygen -lf "$TMP/kh" -E sha256 | awk '{print $2}' | head -n 1)
if [ "$EMPREINTE" != "$EMPREINTE_GITHUB" ]; then
    die "empreinte de github.com inattendue : $EMPREINTE (attendue : $EMPREINTE_GITHUB). known_hosts non écrit."
fi
install -m 644 "$TMP/kh" "$P$CONF/known_hosts"
dit "empreinte conforme à celle publiée par GitHub : $EMPREINTE"

# ------------------------------------------------------------------------------------------------
# 6. État et zones
# ------------------------------------------------------------------------------------------------
etape "6. État et zones"
install -d -m 700 "$P$ETAT"
chmod 700 "$P$ETAT"
dit "$ETAT (700, root)"
GROUPE_ZONES=$(id -gn "$PROPRIETAIRE_ZONES")
while IFS='|' read -r nom chemin place; do
    [ -n "$nom" ] || continue
    if [ -d "$P$chemin" ]; then
        dit "zone $nom : $chemin existe déjà"
    else
        parent=$(dirname "$chemin")
        [ -d "$P$parent" ] || die "le dossier parent de la zone $nom n'existe pas : $parent"
        install -d -m 755 "$P$chemin"
        chown "$PROPRIETAIRE_ZONES:$GROUPE_ZONES" "$P$chemin"
        dit "zone $nom : $chemin créée (propriétaire $PROPRIETAIRE_ZONES)"
    fi
    if [ ! -d "$P$chemin/_corbeille" ]; then
        proprio=$(stat -c '%u:%g' "$P$chemin")
        install -d -m 755 "$P$chemin/_corbeille"
        chown "$proprio" "$P$chemin/_corbeille"
        dit "zone $nom : _corbeille/ créée"
    fi
done <<FIN
$ZONES
FIN

# ------------------------------------------------------------------------------------------------
# 7. Compte de transfert
# ------------------------------------------------------------------------------------------------
etape "7. Compte de transfert « $COMPTE_TRANSFERT » (dépôt de fichiers par rsync sur SSH, en écriture seule)"
if id "$COMPTE_TRANSFERT" >/dev/null 2>&1; then
    dit "le compte $COMPTE_TRANSFERT existe déjà"
else
    useradd --system --user-group --create-home --home-dir "/var/lib/$COMPTE_TRANSFERT" --shell /bin/sh \
        "$COMPTE_TRANSFERT"
    dit "compte $COMPTE_TRANSFERT créé"
fi
passwd -l "$COMPTE_TRANSFERT" >/dev/null 2>&1 || true
dit "mot de passe verrouillé (connexion par clé seulement)"
HOME_TRANSFERT="/var/lib/$COMPTE_TRANSFERT"
install -d -m 700 "$P$HOME_TRANSFERT/.ssh"
chown "$COMPTE_TRANSFERT:$COMPTE_TRANSFERT" "$P$HOME_TRANSFERT/.ssh"
AK="$P$HOME_TRANSFERT/.ssh/authorized_keys"
[ -e "$AK" ] || : >"$AK"
chmod 600 "$AK"
chown "$COMPTE_TRANSFERT:$COMPTE_TRANSFERT" "$AK"
install -d -m 755 "$P$ENTREE"
chown "$PROPRIETAIRE_ZONES:$COMPTE_TRANSFERT" "$P$ENTREE"
chmod 2775 "$P$ENTREE"
dit "$ENTREE : propriétaire $PROPRIETAIRE_ZONES, groupe $COMPTE_TRANSFERT, mode 2775"

ajouter_cle() {
    cle=$1
    case "$cle" in
        *'"'* | *\\*) die "la clé ne doit contenir ni guillemet ni barre oblique inverse" ;;
        *'
'*) die "une seule ligne de clé à la fois" ;;
    esac
    printf '%s' "$cle" | grep -Eq '^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521)|sk-ssh-ed25519@openssh\.com) [A-Za-z0-9+/]+=*( .*)?$' \
        || die "ce n'est pas une ligne de clé publique SSH (attendu : « ssh-ed25519 AAAA… commentaire », sans options)"
    type=$(printf '%s' "$cle" | awk '{print $1}')
    corps=$(printf '%s' "$cle" | awk '{print $2}')
    if grep -qF -- "$type $corps" "$AK"; then
        dit "cette clé est déjà autorisée : rien à ajouter"
        return 0
    fi
    printf 'restrict,command="/usr/bin/rrsync -wo -no-del %s" %s\n' "$ENTREE" "$cle" >>"$AK"
    dit "clé ajoutée : écriture seule dans $ENTREE, rien d'autre (restrict + rrsync -wo -no-del)"
}

if [ "$CLE_DEMANDEE" = 1 ]; then
    ajouter_cle "$CLE_TRANSFERT"
fi

# ------------------------------------------------------------------------------------------------
# 8. Unités systemd
# ------------------------------------------------------------------------------------------------
etape "8. Unités systemd et minuteurs"
for u in $UNITES; do
    install -m 644 "$DEST/systemd/$u" "$P/etc/systemd/system/$u"
done
systemctl daemon-reload
systemctl enable --now deployeur-deploiement.timer deployeur-fichiers.timer
dit "minuteurs activés : un passage par minute et par file (deploiement, fichiers)"

# ------------------------------------------------------------------------------------------------
# 9. Lien pour le gestionnaire de fichiers
# ------------------------------------------------------------------------------------------------
etape "9. Lien $LIEN_FICHIERS"
if [ -e "$P$LIEN_FICHIERS" ] || [ -L "$P$LIEN_FICHIERS" ]; then
    dit "quelque chose existe déjà à $LIEN_FICHIERS : je n'y touche pas"
elif [ -d "$P$(dirname "$LIEN_FICHIERS")" ]; then
    ln -s "$ZONE_TRANSFERT_CHEMIN" "$P$LIEN_FICHIERS"
    dit "$LIEN_FICHIERS -> $ZONE_TRANSFERT_CHEMIN"
else
    dit "le dossier $(dirname "$LIEN_FICHIERS") n'existe pas : lien non posé"
fi

# ------------------------------------------------------------------------------------------------
# 10. L'ancien programme de la même version
# ------------------------------------------------------------------------------------------------
etape "10. Ancien programme de la même version"
ATTENTE=${INSTALLATEUR_ATTENTE_VERROU_S:-1800}
case "$ANCIEN" in
    "$VERSION" | "$VERSION.nouveau")
        # « courant » pointe déjà sur le dossier neuf : plus aucun passage nouveau n'utilise l'ancien. On attend la fin des
        # passages en cours (les deux verrous de file), au plus 30 minutes, puis on relâche et on retire l'ancien.
        install -d -m 700 "$P$ETAT"
        exec 8>>"$P$ETAT/verrou-deploiement" 9>>"$P$ETAT/verrou-fichiers"
        debut=$(date +%s)
        PRIS=0
        if flock -w "$ATTENTE" 8; then
            reste=$((ATTENTE - ($(date +%s) - debut)))
            [ "$reste" -ge 1 ] || reste=1
            if flock -w "$reste" 9; then
                PRIS=1
            fi
        fi
        exec 8>&- 9>&-
        if [ "$PRIS" = 1 ]; then
            rm -rf -- "${P}${OPT:?}/${ANCIEN:?}"
            dit "ancien dossier $OPT/$ANCIEN retiré (aucun passage en cours)"
        else
            dit "un passage dure encore après $((ATTENTE / 60)) min : l'ancien dossier $OPT/$ANCIEN est LAISSÉ en place"
            dit "(sans danger : « courant » pointe déjà sur $NEUF). Le retirer à la main plus tard."
        fi
        ;;
    *) dit "aucun ancien dossier de cette version à retirer" ;;
esac

# ------------------------------------------------------------------------------------------------
# 11. Résumé
# ------------------------------------------------------------------------------------------------
etape "Résumé"
DEPOT_ORDRES_COURT=$(depot_court "$DEPOT_ORDRES")
DEPOT_APP_COURT=$(depot_court "$DEPOT_APPLICATION")
dit "Déployeur $VERSION installé dans $OPT/courant ; configuration $CONF/config.json (600) ; état $ETAT."
dit "Dépôt d'ordres : $DEPOT_ORDRES_COURT (branche main) — dépôt de l'application : $DEPOT_APP_COURT."
dit "Minuteurs : deployeur-deploiement.timer et deployeur-fichiers.timer, un passage par minute."
dit "Je n'ai touché ni au pare-feu, ni à SSH, ni au dossier Compose, ni à Docker."
printf '\n== À faire maintenant\n'
dit "1. Sur GitHub, dépôt $DEPOT_ORDRES_COURT : Settings > Deploy keys > Add deploy key."
dit "   Titre : deployeur-ordres. Coller la clé publique ci-dessous. COCHER « Allow write access » (écriture)."
printf '\n'
cat "$P$CONF/cle_ordres.pub"
printf '\n'
dit "2. Sur GitHub, dépôt $DEPOT_APP_COURT : Settings > Deploy keys > Add deploy key."
dit "   Titre : deployeur-application. Coller la clé publique ci-dessous. NE PAS cocher « Allow write access » (lecture seule)."
printf '\n'
cat "$P$CONF/cle_app.pub"
printf '\n'
dit "3. Pour déposer des fichiers depuis le PC : sur le PC, afficher la clé publique SSH (ligne « ssh-ed25519 AAAA… »),"
dit "   puis sur cette machine : sudo sh installer.sh --cle-transfert \"<la ligne de clé>\""
dit "   La clé n'ouvre que rsync en écriture seule dans $ENTREE (sans suppression)."
dit "4. Vérifier les passages : systemctl list-timers 'deployeur-*' ; journalctl -u deployeur-deploiement.service -n 50."
dit "5. L'essai à blanc (ordres etat, adopter, redéploiement, retour, suite, fichiers) est décrit dans docs/INSTALLATION.md."
