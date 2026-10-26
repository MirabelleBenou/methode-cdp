#!/usr/bin/env python3
"""Workstreams board — a readable page drawn from workstreams.yaml.

    python3 -B make_board.py workstreams.yaml workstreams.html

The PL's tool (not part of the deliverable), copied as is from the method package
into the living-docs repository, next to workstreams.yaml. No dependency, no
network at run time. The reader covers ONLY the file's shape (“- id:” then
“key: value” on one line): this is intended, the source stays readable by eye.

What is specific to the project is read from the header of workstreams.yaml,
nothing to change here:
  - the title: the first line, “# Workstreams — <Project> · …”;
  - the labels of modules and categories: lines
    “# label: mission-plan = Mission Plan” (optional; otherwise the value
    itself, dashes as spaces, first letter capitalized).
Statuses, priorities and complexities are the method's: fixed.
"""
import html
import json
import pathlib
import re
import sys
from datetime import date

STATUSES = [("upcoming", "Upcoming"), ("to-brief", "To brief"), ("in-flight", "In flight"),
            ("debt", "Debt"), ("accepted", "Accepted")]
PRIORITIES = [("high", "High"), ("medium", "Medium"), ("low", "Low")]
COMPLEXITIES = [("high", "High"), ("medium", "Medium"), ("low", "Low")]
DEFAULT_LABELS = {"screen": "Screen", "data": "Data", "doc": "Documentation", "tooling": "Tooling",
                  "engine": "Engine", "operations": "Operations", "core": "Core"}


def read(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    first = text.split("\n", 1)[0]
    m = re.match(r"#\s*Workstreams\s*[—-]\s*([^·]+)", first)
    project = m.group(1).strip() if m else path.parent.name
    labels = dict(DEFAULT_LABELS)
    workstreams: list[dict] = []
    for line in text.split("\n"):
        bare = line.strip()
        lm = re.match(r"#\s*label\s*:\s*([\w-]+)\s*=\s*(.+)$", bare)
        if lm:
            labels[lm.group(1)] = lm.group(2).strip()
            continue
        if not bare or bare.startswith("#"):
            continue
        if bare.startswith("- "):
            workstreams.append({})
            bare = bare[2:]
        if ":" not in bare or not workstreams:
            continue
        key, _, value = bare.partition(":")
        workstreams[-1][key.strip()] = value.strip()
    missing = [w for w in workstreams if not w.get("id") or not w.get("status")]
    if missing:
        sys.exit(f"STOP: {len(missing)} entry(ies) without id or without status.")
    ids = [w["id"] for w in workstreams]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        sys.exit(f"STOP: duplicate id {duplicates}.")
    for field, valid in (("status", {s for s, _ in STATUSES}), ("priority", {p for p, _ in PRIORITIES}),
                         ("complexity", {x for x, _ in COMPLEXITIES})):
        outside = {w.get(field) for w in workstreams if w.get(field)} - valid
        if outside:
            sys.exit(f"STOP: unknown {field} {sorted(outside)}.")
    return project, labels, workstreams


def label(labels, v):
    return labels.get(v) or (v or "—").replace("-", " ").capitalize()


def card(w: dict, labels) -> str:
    e = lambda x: html.escape(str(x or ""))
    pr, cx = w.get("priority") or "medium", w.get("complexity") or "medium"
    rank = f'<span class="rank">{e(w["rank"])}</span>' if w.get("rank") else ""
    refs = f'<span class="ref">{e(w["refs"])}</span>' if w.get("refs") else ""
    cost = f'<p class="cost">{e(w.get("cost"))}</p>' if w.get("cost") else ""
    dots = {"high": "●●●", "medium": "●●", "low": "●"}[cx]
    cat = f'<span class="cat">{e(label(labels, w.get("category")))}</span>' if w.get("category") else ""
    return f"""<article class="card pr-{e(pr)}" data-mod="{e(w.get('module'))}" data-pr="{e(pr)}" data-cx="{e(cx)}">
      <header>{rank}<h3>{e(w.get('title') or w['id'])}</h3></header>
      <p class="basis">{e(w.get('basis'))}</p>
      {cost}
      <footer>
        <span class="mod">{e(label(labels, w.get('module')))}</span>{cat}
        <span class="cx" title="{e(dict(COMPLEXITIES)[cx].lower())} complexity">{dots}</span>
        {refs}
      </footer>
    </article>"""


def page(project, labels, workstreams: list[dict]) -> str:
    columns = ""
    for key, lab in STATUSES:
        subset = [w for w in workstreams if w["status"] == key]
        subset.sort(key=lambda w: int(w["rank"]) if w.get("rank", "").isdigit() else 99)
        columns += (f'<section class="column st-{key}" data-status="{key}">'
                    f'<h2>{lab}<b>{len(subset)}</b></h2>'
                    + "".join(card(w, labels) for w in subset) + "</section>")
    modules = []
    for w in workstreams:
        if w.get("module") and w["module"] not in modules:
            modules.append(w["module"])

    def group(title, field, values, attr):
        buttons = "".join(
            f'<button type="button" class="chip {attr}-{html.escape(v)}" data-field="{attr}" data-val="{html.escape(v)}">'
            f'{html.escape(lab)}<b>{sum(1 for x in workstreams if x.get(field) == v)}</b></button>'
            for v, lab in values if any(x.get(field) == v for x in workstreams))
        return f'<div class="group"><span class="gt">{title}</span>{buttons}</div>' if buttons else ""
    chips = (group("Module", "module", [(m, label(labels, m)) for m in modules], "mod")
             + group("Priority", "priority", PRIORITIES, "pr")
             + group("Complexity", "complexity", COMPLEXITIES, "cx")
             + group("Status", "status", STATUSES, "st"))
    e = html.escape
    return (TEMPLATE.replace("%PROJECT%", e(project)).replace("%COLUMNS%", columns).replace("%CHIPS%", chips)
            .replace("%DATE%", date.today().strftime("%d/%m/%Y"))
            .replace("%TOTAL%", str(len(workstreams)))
            .replace("%DEBTS%", str(sum(1 for w in workstreams if w["status"] == "debt"))))


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Workstreams %PROJECT%</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&amp;family=Oswald:wght@400;500;600&amp;display=swap">
<style>
:root{
  --bg:#EFE9DC; --card:#FBF7EE; --border:#C6BCA5; --ink:#2C3A57; --text:#241F17;
  --mute:#6B6355; --accent:#9A6B12; --shadow:rgba(60,48,28,.16);
  --p-high:#A8332A; --p-medium:#9A6B12; --p-low:#5B6B7F;
  --mono:'JetBrains Mono',ui-monospace,monospace; --label:'Oswald',system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#1B150D; --card:#241B0F; --border:#4A4132; --ink:#CBD8E4; --text:#E9E7DD;
  --mute:#ABAA9A; --accent:#E0A83A; --shadow:rgba(0,0,0,.45);
  --p-high:#D4564A; --p-medium:#E0A83A; --p-low:#8AA0B8;
}}
:root[data-theme="dark"]{
  --bg:#1B150D; --card:#241B0F; --border:#4A4132; --ink:#CBD8E4; --text:#E9E7DD;
  --mute:#ABAA9A; --accent:#E0A83A; --shadow:rgba(0,0,0,.45);
  --p-high:#D4564A; --p-medium:#E0A83A; --p-low:#8AA0B8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--mono);font-size:15px;line-height:1.5}
.wrap{max-width:1400px;margin:0 auto;padding:1.4rem 1rem 3rem}
header.head{border-bottom:1.5px solid var(--ink);padding-bottom:.7rem;margin-bottom:1rem}
header.head h1{font-family:var(--label);font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  font-size:1rem;color:var(--ink);margin:0}
header.head p{margin:.35rem 0 0;color:var(--mute);font-size:.78rem}
.filters{display:flex;flex-direction:column;gap:.45rem;margin:0 0 1.3rem}
.group{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}
.gt{font-family:var(--label);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mute);flex:0 0 5.6rem}
.reset{align-self:flex-start}
.chip{font-family:var(--label);font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;
  background:none;border:1px solid var(--border);color:var(--mute);padding:.22rem .55rem;cursor:pointer;
  border-radius:0;display:inline-flex;gap:.4rem;align-items:center}
.chip b{font-family:var(--mono);font-size:.7rem;font-weight:400;opacity:.8}
.chip[aria-pressed="true"]{border-color:var(--accent);color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent)}
.chip:hover{border-color:var(--ink);color:var(--ink)}
.board{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:1rem;align-items:start}
.column h2{font-family:var(--label);font-weight:500;letter-spacing:.1em;text-transform:uppercase;
  font-size:.8rem;color:var(--ink);border-bottom:1px solid var(--border);padding-bottom:.3rem;
  margin:0 0 .7rem;display:flex;justify-content:space-between;align-items:baseline}
.column h2 b{font-family:var(--mono);font-size:.75rem;font-weight:400;color:var(--mute)}
.card{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--p-medium);
  box-shadow:0 1px 3px var(--shadow);padding:.65rem .7rem;margin-bottom:.7rem}
.card.pr-high{border-left-color:var(--p-high)}
.card.pr-low{border-left-color:var(--p-low)}
.card header{display:flex;gap:.45rem;align-items:baseline}
.card h3{font-family:var(--label);font-weight:500;font-size:.95rem;margin:0;color:var(--text)}
.rank{font-family:var(--mono);font-size:.68rem;color:var(--accent);border:1px solid var(--accent);padding:0 .25rem;flex:0 0 auto}
.basis{margin:.45rem 0 0;font-size:.78rem;opacity:.92}
.cost{margin:.35rem 0 0;font-size:.72rem;color:var(--mute);font-style:italic}
.card footer{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap;margin-top:.55rem}
.cat{font-family:var(--label);font-size:.62rem;letter-spacing:.07em;text-transform:uppercase;
  border:1px solid var(--border);color:var(--mute);padding:.02rem .3rem}
.mod{font-family:var(--label);font-size:.62rem;letter-spacing:.07em;text-transform:uppercase;
  background:var(--ink);color:var(--card);padding:.04rem .32rem}
.cx{font-size:.6rem;color:var(--mute);letter-spacing:.08em}
.ref{font-size:.66rem;color:var(--mute);margin-left:auto}
.masked{display:none}
footer.foot{margin-top:2rem;border-top:1px solid var(--border);padding-top:.6rem;font-size:.72rem;color:var(--mute)}
@media (max-width:1300px){.board{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:1000px){.board{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:680px){.board{grid-template-columns:1fr;gap:1.4rem}.gt{flex-basis:100%}}
</style>
</head>
<body>
<div class="wrap">
<header class="head">
  <h1>Workstreams — %PROJECT%</h1>
  <p><b id="count">%TOTAL%</b> entries shown out of %TOTAL% · %DEBTS% in debt · generated on %DATE% from <code>workstreams.yaml</code></p>
</header>
<div class="filters">%CHIPS%<button type="button" class="chip reset" id="reset" hidden>Show all</button></div>
<div class="board">%COLUMNS%</div>
<footer class="foot">This board is not kept by hand: it is regenerated from <code>workstreams.yaml</code>,
the single source. A workstream missing from the file is missing from the project.</footer>
</div>
<script>
const active = {mod:new Set(), pr:new Set(), cx:new Set(), st:new Set()};
function applyFilters(){
  document.querySelectorAll(".column").forEach(col=>{
    col.classList.toggle("masked", active.st.size > 0 && !active.st.has(col.dataset.status));
  });
  document.querySelectorAll(".card").forEach(c=>{
    const ok = (active.mod.size === 0 || active.mod.has(c.dataset.mod))
            && (active.pr.size === 0 || active.pr.has(c.dataset.pr))
            && (active.cx.size === 0 || active.cx.has(c.dataset.cx));
    c.classList.toggle("masked", !ok);
  });
  let total = 0;
  document.querySelectorAll(".column").forEach(col=>{
    const n = col.querySelectorAll(".card:not(.masked)").length;
    col.querySelector("h2 b").textContent = n;
    if(!col.classList.contains("masked")) total += n;
  });
  document.getElementById("count").textContent = total;
  document.getElementById("reset").hidden = !Object.values(active).some(s => s.size > 0);
}
document.querySelectorAll(".chip[data-field]").forEach(ch=>{
  ch.setAttribute("aria-pressed","false");
  ch.addEventListener("click",()=>{
    const set = active[ch.dataset.field], v = ch.dataset.val;
    if(set.has(v)){ set.delete(v); ch.setAttribute("aria-pressed","false"); }
    else { set.add(v); ch.setAttribute("aria-pressed","true"); }
    applyFilters();
  });
});
document.getElementById("reset").addEventListener("click",()=>{
  Object.values(active).forEach(s=>s.clear());
  document.querySelectorAll(".chip[data-field]").forEach(c=>c.setAttribute("aria-pressed","false"));
  applyFilters();
});
applyFilters();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: make_board.py <workstreams.yaml> <workstreams.html>")
    source, output = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    project, labels, workstreams = read(source)
    output.write_text(page(project, labels, workstreams), encoding="utf-8")
    by_status = {s: sum(1 for w in workstreams if w["status"] == s) for s, _ in STATUSES}
    print(f"{len(workstreams)} workstreams read · {json.dumps(by_status, ensure_ascii=False)} · written to {output}")
