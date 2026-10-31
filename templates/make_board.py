#!/usr/bin/env python3
"""Workstreams board — a fixed page and its data file, drawn from workstreams.yaml.

    python3 -B make_board.py workstreams.yaml workstreams.html

Writes TWO files: the page (the second argument, "workstreams.html") and, next to it, the
data file of the same name in ".json" ("workstreams.json"). The page is fixed: it holds no
workstream data, only the project name; it reads its data from the JSON file with "fetch" and
builds the board in the browser. Two sources with the same header give the same page, byte for
byte; only the data changes, so only the data is republished when a workstream moves. The data
file is deterministic (two generations of the same source are byte-identical, except for the
"generated on" date).

The two files are published together, side by side. The page opened from the disk ("file://")
does not load its data: this is a browser limit, and the page says so ("Cannot load
workstreams.json (…)"). Open it served ("python3 -m http.server" in the folder) or published.

The PL's tool (not part of the deliverable), copied as is from the method package
into the living-docs repository, next to workstreams.yaml. No dependency, no
network when the generator runs. The reader covers ONLY the file's shape (“- id:” then
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


def data_path(output: pathlib.Path) -> pathlib.Path:
    """The data file written next to the page: same name, .json extension."""
    return output.with_suffix(".json")


def data(project, labels, workstreams: list[dict]) -> dict:
    """Everything the page shows: the entries in the order of the file, with all their keys."""
    return {"project": project, "generated": date.today().strftime("%d/%m/%Y"),
            "labels": labels, "workstreams": workstreams}


def data_text(project, labels, workstreams: list[dict]) -> str:
    return json.dumps(data(project, labels, workstreams), ensure_ascii=False, indent=1) + "\n"


def page(project: str, data_name: str) -> str:
    """The fixed page: it depends only on the project name and on the name of the data file."""
    def js(value) -> str:
        return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")
    values = {"PROJECT": html.escape(project), "DATA": js(data_name), "STATUSES": js(STATUSES),
              "PRIORITIES": js(PRIORITIES), "COMPLEXITIES": js(COMPLEXITIES)}
    return re.sub(r"%(PROJECT|DATA|STATUSES|PRIORITIES|COMPLEXITIES)%", lambda m: values[m.group(1)], TEMPLATE)


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
.column{min-width:0}
.column h2{font-family:var(--label);font-weight:500;letter-spacing:.1em;text-transform:uppercase;
  font-size:.8rem;color:var(--ink);border-bottom:1px solid var(--border);padding-bottom:.3rem;
  margin:0 0 .7rem;display:flex;justify-content:space-between;align-items:baseline}
.column h2 b{font-family:var(--mono);font-size:.75rem;font-weight:400;color:var(--mute)}
.card{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--p-medium);
  box-shadow:0 1px 3px var(--shadow);padding:.65rem .7rem;margin-bottom:.7rem;overflow-wrap:anywhere}
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
.error{margin:1rem 0;padding:.7rem .9rem;border:1px solid var(--border);border-left:4px solid var(--p-high);font-size:.85rem}
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
  <p id="meta"></p>
</header>
<div class="filters" id="filters"><button type="button" class="chip reset" id="reset" hidden>Show all</button></div>
<div class="board" id="board"></div>
<footer class="foot">This board is not kept by hand: it is regenerated from <code>workstreams.yaml</code>,
the single source. A workstream missing from the file is missing from the project.</footer>
</div>
<script>
const DATA_NAME = %DATA%;
const STATUSES = %STATUSES%;
const PRIORITIES = %PRIORITIES%;
const COMPLEXITIES = %COMPLEXITIES%;
const DOTS = {high:"●●●", medium:"●●", low:"●"};
const active = {mod:new Set(), pr:new Set(), cx:new Set(), st:new Set()};
let labels = {};

function el(name, className, text){
  const n = document.createElement(name);
  if(className) n.className = className;
  if(text !== undefined && text !== null) n.textContent = String(text);
  return n;
}
function label(v){
  v = v || "";
  if(Object.prototype.hasOwnProperty.call(labels, v) && labels[v]) return labels[v];
  const s = (v || "—").replace(/-/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}
function rankOf(w){ return /^[0-9]+$/.test(w.rank || "") ? parseInt(w.rank, 10) : 99; }
function card(w){
  const pr = w.priority || "medium", cx = w.complexity || "medium";
  const a = el("article", "card pr-" + pr);
  a.dataset.mod = w.module || ""; a.dataset.pr = pr; a.dataset.cx = cx;
  const head = el("header");
  if(w.rank) head.appendChild(el("span", "rank", w.rank));
  head.appendChild(el("h3", null, w.title || w.id));
  a.appendChild(head);
  a.appendChild(el("p", "basis", w.basis || ""));
  if(w.cost) a.appendChild(el("p", "cost", w.cost));
  const foot = el("footer");
  foot.appendChild(el("span", "mod", label(w.module)));
  if(w.category) foot.appendChild(el("span", "cat", label(w.category)));
  const x = el("span", "cx", DOTS[cx] || "");
  const cxName = (COMPLEXITIES.find(k => k[0] === cx) || [cx, cx])[1];
  x.title = cxName.toLowerCase() + " complexity";
  foot.appendChild(x);
  if(w.refs) foot.appendChild(el("span", "ref", w.refs));
  a.appendChild(foot);
  return a;
}
function columns(workstreams){
  const board = el("div", "board");
  STATUSES.forEach(([key, lab]) => {
    const subset = workstreams.filter(w => w.status === key).sort((a, b) => rankOf(a) - rankOf(b));
    const col = el("section", "column st-" + key);
    col.dataset.status = key;
    const h2 = el("h2", null, lab);
    h2.appendChild(el("b", null, subset.length));
    col.appendChild(h2);
    subset.forEach(w => col.appendChild(card(w)));
    board.appendChild(col);
  });
  return board;
}
function group(workstreams, title, field, values, attr){
  const present = values.filter(([v]) => workstreams.some(x => x[field] === v));
  if(!present.length) return null;
  const g = el("div", "group");
  g.appendChild(el("span", "gt", title));
  present.forEach(([v, lab]) => {
    const b = el("button", "chip " + attr + "-" + v);
    b.type = "button";
    b.dataset.field = attr; b.dataset.val = v;
    b.setAttribute("aria-pressed", "false");
    b.appendChild(document.createTextNode(lab));
    b.appendChild(el("b", null, workstreams.filter(x => x[field] === v).length));
    b.addEventListener("click", () => {
      const set = active[attr];
      if(set.has(v)){ set.delete(v); b.setAttribute("aria-pressed", "false"); }
      else { set.add(v); b.setAttribute("aria-pressed", "true"); }
      applyFilters();
    });
    g.appendChild(b);
  });
  return g;
}
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
function show(d){
  labels = d.labels || {};
  const workstreams = d.workstreams;
  const debts = workstreams.filter(w => w.status === "debt").length;
  const meta = document.getElementById("meta");
  const count = el("b", null, workstreams.length);
  count.id = "count";
  meta.replaceChildren(count, " entries shown out of " + workstreams.length + " · " + debts
    + " in debt · generated on " + (d.generated || "?") + " from ", el("code", null, "workstreams.yaml"));
  const modules = [];
  workstreams.forEach(w => { if(w.module && !modules.includes(w.module)) modules.push(w.module); });
  const filters = document.getElementById("filters"), reset = document.getElementById("reset");
  [group(workstreams, "Module", "module", modules.map(m => [m, label(m)]), "mod"),
   group(workstreams, "Priority", "priority", PRIORITIES, "pr"),
   group(workstreams, "Complexity", "complexity", COMPLEXITIES, "cx"),
   group(workstreams, "Status", "status", STATUSES, "st")]
    .forEach(g => { if(g) filters.insertBefore(g, reset); });
  document.getElementById("board").replaceWith(columns(workstreams));
  applyFilters();
}
function failure(detail){
  const m = el("p", "error", "Cannot load " + DATA_NAME + " (" + detail + ").");
  m.setAttribute("role", "alert");
  document.getElementById("board").replaceWith(m);
}
document.getElementById("reset").addEventListener("click", ()=>{
  Object.values(active).forEach(s => s.clear());
  document.querySelectorAll(".chip[data-field]").forEach(c => c.setAttribute("aria-pressed", "false"));
  applyFilters();
});
fetch(DATA_NAME, {cache: "no-cache"})
  .then(r => { if(!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then(d => {
    if(!d || !Array.isArray(d.workstreams)) throw new Error("unexpected format");
    show(d);
  })
  .catch(e => failure(e && e.message ? e.message : String(e)));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: make_board.py <workstreams.yaml> <workstreams.html>")
    source, output = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    project, labels, workstreams = read(source)
    data_output = data_path(output)
    if data_output == output:
        sys.exit("STOP: the page cannot have the .json extension (it is the one of the data file).")
    output.write_text(page(project, data_output.name), encoding="utf-8")
    data_output.write_text(data_text(project, labels, workstreams), encoding="utf-8")
    by_status = {s: sum(1 for w in workstreams if w["status"] == s) for s, _ in STATUSES}
    print(f"{len(workstreams)} workstreams read · {json.dumps(by_status, ensure_ascii=False)} · "
          f"written to {output} and {data_output}")
