#!/usr/bin/env python3
"""Tableau de bord des chantiers — page lisible tirée de chantiers.yaml.

    python3 -B generer_tableau.py chantiers.yaml chantiers.html

Outil du CdP (pas du livrable), copié tel quel du package méthode dans le dépôt
des vivants, à côté de chantiers.yaml. Aucune dépendance, aucun réseau à
l'exécution. Le lecteur ne couvre QUE la forme du fichier (« - id: » puis des
« clé: valeur » sur une ligne) : c'est voulu, la source reste lisible à l'œil.

Ce qui est propre au projet se lit dans l'en-tête de chantiers.yaml, rien à
modifier ici :
  - le titre : la première ligne, « # Chantiers — <Projet> · … » ;
  - les libellés des modules et catégories : des lignes
    « # libelle: mission-plan = Mission Plan » (facultatives ; sinon la valeur
    elle-même, tirets en espaces, première lettre en capitale).
Les statuts, priorités et complexités sont ceux de la méthode : fixes.
"""
import html
import json
import pathlib
import re
import sys
from datetime import date

STATUTS = [("a-venir", "À venir"), ("a-cadrer", "À cadrer"), ("en-vol", "En vol"),
           ("dette", "Dette"), ("recette", "Recetté")]
PRIORITES = [("haut", "Important"), ("moyen", "Moyen"), ("faible", "Faible")]
COMPLEXITES = [("forte", "Forte"), ("moyenne", "Moyenne"), ("faible", "Faible")]
LIBELLES_DEFAUT = {"ecran": "Écran", "donnees": "Données", "doc": "Documentation", "outillage": "Outillage",
                   "moteur": "Moteur", "exploitation": "Exploitation", "socle": "Socle"}


def lire(chemin: pathlib.Path):
    texte = chemin.read_text(encoding="utf-8")
    premiere = texte.split("\n", 1)[0]
    m = re.match(r"#\s*Chantiers\s*[—-]\s*([^·]+)", premiere)
    projet = m.group(1).strip() if m else chemin.parent.name
    libelles = dict(LIBELLES_DEFAUT)
    chantiers: list[dict] = []
    for ligne in texte.split("\n"):
        nue = ligne.strip()
        lm = re.match(r"#\s*libelle\s*:\s*([\w-]+)\s*=\s*(.+)$", nue)
        if lm:
            libelles[lm.group(1)] = lm.group(2).strip()
            continue
        if not nue or nue.startswith("#"):
            continue
        if nue.startswith("- "):
            chantiers.append({})
            nue = nue[2:]
        if ":" not in nue or not chantiers:
            continue
        cle, _, valeur = nue.partition(":")
        chantiers[-1][cle.strip()] = valeur.strip()
    manquants = [c for c in chantiers if not c.get("id") or not c.get("statut")]
    if manquants:
        sys.exit(f"ARRÊT : {len(manquants)} entrée(s) sans id ou sans statut.")
    ids = [c["id"] for c in chantiers]
    doublons = sorted({i for i in ids if ids.count(i) > 1})
    if doublons:
        sys.exit(f"ARRÊT : id en double {doublons}.")
    for champ, valides in (("statut", {s for s, _ in STATUTS}), ("priorite", {p for p, _ in PRIORITES}),
                           ("complexite", {x for x, _ in COMPLEXITES})):
        hors = {c.get(champ) for c in chantiers if c.get(champ)} - valides
        if hors:
            sys.exit(f"ARRÊT : {champ} inconnu {sorted(hors)}.")
    return projet, libelles, chantiers


def libelle(libelles, v):
    return libelles.get(v) or (v or "—").replace("-", " ").capitalize()


def carte(c: dict, libelles) -> str:
    e = lambda x: html.escape(str(x or ""))
    pr, cx = c.get("priorite") or "moyen", c.get("complexite") or "moyenne"
    rang = f'<span class="rang">{e(c["rang"])}</span>' if c.get("rang") else ""
    refs = f'<span class="ref">{e(c["refs"])}</span>' if c.get("refs") else ""
    cout = f'<p class="cout">{e(c.get("cout"))}</p>' if c.get("cout") else ""
    points = {"forte": "●●●", "moyenne": "●●", "faible": "●"}[cx]
    cat = f'<span class="cat">{e(libelle(libelles, c.get("categorie")))}</span>' if c.get("categorie") else ""
    return f"""<article class="carte pr-{e(pr)}" data-mod="{e(c.get('module'))}" data-pr="{e(pr)}" data-cx="{e(cx)}">
      <header>{rang}<h3>{e(c.get('titre') or c['id'])}</h3></header>
      <p class="mesure">{e(c.get('mesure'))}</p>
      {cout}
      <footer>
        <span class="mod">{e(libelle(libelles, c.get('module')))}</span>{cat}
        <span class="cx" title="complexité {e(dict(COMPLEXITES)[cx].lower())}">{points}</span>
        {refs}
      </footer>
    </article>"""


def page(projet, libelles, chantiers: list[dict]) -> str:
    colonnes = ""
    for cle, lib in STATUTS:
        lot = [c for c in chantiers if c["statut"] == cle]
        lot.sort(key=lambda c: int(c["rang"]) if c.get("rang", "").isdigit() else 99)
        colonnes += (f'<section class="colonne st-{cle}" data-statut="{cle}">'
                     f'<h2>{lib}<b>{len(lot)}</b></h2>'
                     + "".join(carte(c, libelles) for c in lot) + "</section>")
    modules = []
    for c in chantiers:
        if c.get("module") and c["module"] not in modules:
            modules.append(c["module"])

    def groupe(titre, champ, valeurs, attr):
        boutons = "".join(
            f'<button type="button" class="chip {attr}-{html.escape(v)}" data-champ="{attr}" data-val="{html.escape(v)}">'
            f'{html.escape(lib)}<b>{sum(1 for x in chantiers if x.get(champ) == v)}</b></button>'
            for v, lib in valeurs if any(x.get(champ) == v for x in chantiers))
        return f'<div class="groupe"><span class="gt">{titre}</span>{boutons}</div>' if boutons else ""
    chips = (groupe("Module", "module", [(m, libelle(libelles, m)) for m in modules], "mod")
             + groupe("Priorité", "priorite", PRIORITES, "pr")
             + groupe("Complexité", "complexite", COMPLEXITES, "cx")
             + groupe("Statut", "statut", STATUTS, "st"))
    e = html.escape
    return (TEMPLATE.replace("%PROJET%", e(projet)).replace("%COLONNES%", colonnes).replace("%CHIPS%", chips)
            .replace("%DATE%", date.today().strftime("%d/%m/%Y"))
            .replace("%TOTAL%", str(len(chantiers)))
            .replace("%DETTES%", str(sum(1 for c in chantiers if c["statut"] == "dette"))))


TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Chantiers %PROJET%</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&amp;family=Oswald:wght@400;500;600&amp;display=swap">
<style>
:root{
  --fond:#EFE9DC; --carte:#FBF7EE; --bord:#C6BCA5; --ink:#2C3A57; --texte:#241F17;
  --mute:#6B6355; --accent:#9A6B12; --ombre:rgba(60,48,28,.16);
  --p-haut:#A8332A; --p-moyen:#9A6B12; --p-faible:#5B6B7F;
  --mono:'JetBrains Mono',ui-monospace,monospace; --label:'Oswald',system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --fond:#1B150D; --carte:#241B0F; --bord:#4A4132; --ink:#CBD8E4; --texte:#E9E7DD;
  --mute:#ABAA9A; --accent:#E0A83A; --ombre:rgba(0,0,0,.45);
  --p-haut:#D4564A; --p-moyen:#E0A83A; --p-faible:#8AA0B8;
}}
:root[data-theme="dark"]{
  --fond:#1B150D; --carte:#241B0F; --bord:#4A4132; --ink:#CBD8E4; --texte:#E9E7DD;
  --mute:#ABAA9A; --accent:#E0A83A; --ombre:rgba(0,0,0,.45);
  --p-haut:#D4564A; --p-moyen:#E0A83A; --p-faible:#8AA0B8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--texte);font-family:var(--mono);font-size:15px;line-height:1.5}
.enveloppe{max-width:1400px;margin:0 auto;padding:1.4rem 1rem 3rem}
header.tete{border-bottom:1.5px solid var(--ink);padding-bottom:.7rem;margin-bottom:1rem}
header.tete h1{font-family:var(--label);font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  font-size:1rem;color:var(--ink);margin:0}
header.tete p{margin:.35rem 0 0;color:var(--mute);font-size:.78rem}
.filtres{display:flex;flex-direction:column;gap:.45rem;margin:0 0 1.3rem}
.groupe{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}
.gt{font-family:var(--label);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mute);flex:0 0 5.6rem}
.raz{align-self:flex-start}
.chip{font-family:var(--label);font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;
  background:none;border:1px solid var(--bord);color:var(--mute);padding:.22rem .55rem;cursor:pointer;
  border-radius:0;display:inline-flex;gap:.4rem;align-items:center}
.chip b{font-family:var(--mono);font-size:.7rem;font-weight:400;opacity:.8}
.chip[aria-pressed="true"]{border-color:var(--accent);color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent)}
.chip:hover{border-color:var(--ink);color:var(--ink)}
.tableau{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:1rem;align-items:start}
.colonne h2{font-family:var(--label);font-weight:500;letter-spacing:.1em;text-transform:uppercase;
  font-size:.8rem;color:var(--ink);border-bottom:1px solid var(--bord);padding-bottom:.3rem;
  margin:0 0 .7rem;display:flex;justify-content:space-between;align-items:baseline}
.colonne h2 b{font-family:var(--mono);font-size:.75rem;font-weight:400;color:var(--mute)}
.carte{background:var(--carte);border:1px solid var(--bord);border-left:4px solid var(--p-moyen);
  box-shadow:0 1px 3px var(--ombre);padding:.65rem .7rem;margin-bottom:.7rem}
.carte.pr-haut{border-left-color:var(--p-haut)}
.carte.pr-faible{border-left-color:var(--p-faible)}
.carte header{display:flex;gap:.45rem;align-items:baseline}
.carte h3{font-family:var(--label);font-weight:500;font-size:.95rem;margin:0;color:var(--texte)}
.rang{font-family:var(--mono);font-size:.68rem;color:var(--accent);border:1px solid var(--accent);padding:0 .25rem;flex:0 0 auto}
.mesure{margin:.45rem 0 0;font-size:.78rem;opacity:.92}
.cout{margin:.35rem 0 0;font-size:.72rem;color:var(--mute);font-style:italic}
.carte footer{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap;margin-top:.55rem}
.cat{font-family:var(--label);font-size:.62rem;letter-spacing:.07em;text-transform:uppercase;
  border:1px solid var(--bord);color:var(--mute);padding:.02rem .3rem}
.mod{font-family:var(--label);font-size:.62rem;letter-spacing:.07em;text-transform:uppercase;
  background:var(--ink);color:var(--carte);padding:.04rem .32rem}
.cx{font-size:.6rem;color:var(--mute);letter-spacing:.08em}
.ref{font-size:.66rem;color:var(--mute);margin-left:auto}
.masque{display:none}
footer.pied{margin-top:2rem;border-top:1px solid var(--bord);padding-top:.6rem;font-size:.72rem;color:var(--mute)}
@media (max-width:1300px){.tableau{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:1000px){.tableau{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:680px){.tableau{grid-template-columns:1fr;gap:1.4rem}.gt{flex-basis:100%}}
</style>
</head>
<body>
<div class="enveloppe">
<header class="tete">
  <h1>Chantiers — %PROJET%</h1>
  <p><b id="compte">%TOTAL%</b> entrées affichées sur %TOTAL% · %DETTES% en dette · engendré le %DATE% depuis <code>chantiers.yaml</code></p>
</header>
<div class="filtres">%CHIPS%<button type="button" class="chip raz" id="raz" hidden>Tout afficher</button></div>
<div class="tableau">%COLONNES%</div>
<footer class="pied">Ce tableau ne se tient pas à la main : il se régénère depuis <code>chantiers.yaml</code>,
seule source. Un chantier absent du fichier est absent du projet.</footer>
</div>
<script>
const actifs = {mod:new Set(), pr:new Set(), cx:new Set(), st:new Set()};
function appliquer(){
  document.querySelectorAll(".colonne").forEach(col=>{
    col.classList.toggle("masque", actifs.st.size > 0 && !actifs.st.has(col.dataset.statut));
  });
  document.querySelectorAll(".carte").forEach(c=>{
    const ok = (actifs.mod.size === 0 || actifs.mod.has(c.dataset.mod))
            && (actifs.pr.size === 0 || actifs.pr.has(c.dataset.pr))
            && (actifs.cx.size === 0 || actifs.cx.has(c.dataset.cx));
    c.classList.toggle("masque", !ok);
  });
  let total = 0;
  document.querySelectorAll(".colonne").forEach(col=>{
    const n = col.querySelectorAll(".carte:not(.masque)").length;
    col.querySelector("h2 b").textContent = n;
    if(!col.classList.contains("masque")) total += n;
  });
  document.getElementById("compte").textContent = total;
  document.getElementById("raz").hidden = !Object.values(actifs).some(s => s.size > 0);
}
document.querySelectorAll(".chip[data-champ]").forEach(ch=>{
  ch.setAttribute("aria-pressed","false");
  ch.addEventListener("click",()=>{
    const jeu = actifs[ch.dataset.champ], v = ch.dataset.val;
    if(jeu.has(v)){ jeu.delete(v); ch.setAttribute("aria-pressed","false"); }
    else { jeu.add(v); ch.setAttribute("aria-pressed","true"); }
    appliquer();
  });
});
document.getElementById("raz").addEventListener("click",()=>{
  Object.values(actifs).forEach(s=>s.clear());
  document.querySelectorAll(".chip[data-champ]").forEach(c=>c.setAttribute("aria-pressed","false"));
  appliquer();
});
appliquer();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage : generer_tableau.py <chantiers.yaml> <chantiers.html>")
    source, sortie = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    projet, libelles, chantiers = lire(source)
    sortie.write_text(page(projet, libelles, chantiers), encoding="utf-8")
    par_statut = {s: sum(1 for c in chantiers if c["statut"] == s) for s, _ in STATUTS}
    print(f"{len(chantiers)} chantiers lus · {json.dumps(par_statut, ensure_ascii=False)} · écrit dans {sortie}")
