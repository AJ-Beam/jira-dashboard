from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, base64, ssl, json

JIRA_DOMAIN = "beamdental.atlassian.net"   
JIRA_EMAIL  = "Andrew.jenkins@beambenefits.com"            
JIRA_TOKEN  = "ATATT3xFfGF0mYqI8WSQJndIPa5vZsFjdZyQGr3MweyaswW0kHJDsI_gr4817ej3ZQn2szmSNRb8TaTeYTRlMyEcAU_A5TUF6mDsuoB0Uw5spaKzTRyThgMx_htvYSDXiWXC5BF4-GEaIyGACGPSpcxrXJWGgnwWYffLwzmjcoL4X1U1r39Qg9g=64C5D27C"

credentials = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Jira People Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f5f7fa;color:#1a1a2e;min-height:100vh}
header{background:#fff;border-bottom:1px solid #e5e7eb;padding:16px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:20px;font-weight:800;color:#4f46e5}
header p{font-size:12px;color:#999}
#search-bar{display:flex;gap:8px;margin-left:auto;flex-wrap:wrap}
#search-bar input{border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;width:220px;outline:none}
#search-bar input:focus{border-color:#6366f1}
#search-bar button{background:#6366f1;color:#fff;border:none;border-radius:8px;padding:8px 16px;cursor:pointer;font-size:13px;font-weight:600}
#status{padding:10px 24px;font-size:12px}
#status.ok{color:#16a34a} #status.err{color:#dc2626} #status.loading{color:#999}
#content{padding:24px}
.people-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.person-card{background:#fff;border-radius:14px;box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden}
.person-header{padding:14px 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #f3f4f6}
.avatar{width:38px;height:38px;border-radius:50%;background:#6366f1;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0}
.person-name{font-weight:700;font-size:14px}
.person-meta{font-size:11px;color:#999;margin-top:2px}
.pills{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}
.pill{font-size:10px;font-weight:700;padding:3px 8px;border-radius:20px}
.pill.todo{background:#e0f2fe;color:#0369a1}
.pill.inprogress{background:#fef9c3;color:#92400e}
.pill.done{background:#dcfce7;color:#166534}
.pill.overdue{background:#fee2e2;color:#991b1b}
.task-list{max-height:280px;overflow-y:auto}
.task-row{padding:10px 16px;border-bottom:1px solid #f9fafb;display:flex;align-items:flex-start;gap:10px;font-size:12px}
.task-row:last-child{border-bottom:none}
.task-row:hover{background:#fafafa}
.status-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:3px}
.dot-todo{background:#93c5fd} .dot-inprogress{background:#fbbf24} .dot-done{background:#4ade80}
.task-info{flex:1;min-width:0}
.task-key{color:#6366f1;font-weight:600;font-size:11px}
.task-summary{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#374151}
.task-badges{display:flex;gap:4px;margin-top:3px;flex-wrap:wrap}
.badge{font-size:10px;padding:1px 6px;border-radius:4px;font-weight:600}
.badge.bug{background:#fee2e2;color:#991b1b}
.badge.story{background:#ede9fe;color:#5b21b6}
.badge.task{background:#e0f2fe;color:#0369a1}
.badge.subtask{background:#f3f4f6;color:#6b7280}
.badge.pts{background:#f0fdf4;color:#166534}
.badge.overdue{background:#fee2e2;color:#991b1b}
.no-tasks{padding:20px;text-align:center;color:#bbb;font-size:13px}
.summary-bar{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.07);padding:16px 24px;margin-bottom:20px;display:flex;gap:24px;flex-wrap:wrap}
.stat{text-align:center}
.stat .n{font-size:26px;font-weight:800;color:#4f46e5}
.stat .l{font-size:11px;color:#999;margin-top:2px}
</style>
</head>
<body>
<header>
  <div>
    <h1>👤 Jira People Dashboard</h1>
    <p>beamdental.atlassian.net · Tasks by assignee</p>
  </div>
  <div id="search-bar">
    <input id="search-input" type="text" placeholder="Filter by name…" oninput="filterCards()"/>
    <button onclick="loadAll()">🔄 Refresh</button>
  </div>
</header>
<div id="status" class="status loading">⏳ Loading assignees…</div>
<div id="content">
  <div class="summary-bar" id="summary" style="display:none">
    <div class="stat"><div class="n" id="s-people">—</div><div class="l">People</div></div>
    <div class="stat"><div class="n" id="s-tasks">—</div><div class="l">Total Tasks</div></div>
    <div class="stat"><div class="n" id="s-inprogress" style="color:#d97706">—</div><div class="l">In Progress</div></div>
    <div class="stat"><div class="n" id="s-overdue" style="color:#dc2626">—</div><div class="l">Overdue</div></div>
    <div class="stat"><div class="n" id="s-pts" style="color:#16a34a">—</div><div class="l">Total Points</div></div>
  </div>
  <div class="people-grid" id="grid"></div>
</div>
<script>
const today = new Date();

function statusCategory(issue) {
  const key = issue.fields.status?.statusCategory?.key || "";
  if (key === "done") return "done";
  if (key === "indeterminate") return "inprogress";
  return "todo";
}

function isOverdue(issue) {
  const due = issue.fields.duedate;
  if (!due) return false;
  return new Date(due) < today && statusCategory(issue) !== "done";
}

function issueType(issue) {
  return (issue.fields.issuetype?.name || "Task").toLowerCase();
}

function initials(name) {
  return name.split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase();
}

function avatarColor(name) {
  const colors = ["#6366f1","#f59e0b","#10b981","#ef4444","#3b82f6","#ec4899","#14b8a6","#f97316"];
  let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) % colors.length;
  return colors[h];
}

function formatDate(d) {
  if (!d) return null;
  const dt = new Date(d);
  return dt.toLocaleDateString("en-US", {month:"short", day:"numeric"});
}

let allCards = [];

async function loadAll() {
  document.getElementById("status").className = "status loading";
  document.getElementById("status").textContent = "⏳ Loading tasks from Jira…";
  document.getElementById("grid").innerHTML = "";
  document.getElementById("summary").style.display = "none";
  allCards = [];

  try {
    // Use JQL to get all open + recently closed issues with assignees
    const jql = encodeURIComponent('assignee is not EMPTY AND statusCategory in ("To Do","In Progress") ORDER BY updated DESC');
    const fields = "summary,assignee,status,issuetype,customfield_10016,duedate,priority";
    let start = 0, all = [];
    while (true) {
      const r = await fetch(`/jira/search?jql=${jql}&fields=${fields}&maxResults=100&startAt=${start}`);
      const data = await r.json();
      all = all.concat(data.issues || []);
      if (all.length >= data.total || (data.issues||[]).length === 0) break;
      start += 100;
      if (start > 500) break; // cap at 500
    }

    // Group by assignee
    const byPerson = {};
    for (const issue of all) {
      const a = issue.fields.assignee;
      if (!a) continue;
      const key = a.accountId;
      if (!byPerson[key]) byPerson[key] = { name: a.displayName, avatar: a.avatarUrls?.["32x32"], issues: [] };
      byPerson[key].issues.push(issue);
    }

    // Summary stats
    const totalTasks = all.length;
    const totalPts = all.reduce((s,i) => s + (i.fields.customfield_10016||0), 0);
    const totalIP = all.filter(i => statusCategory(i) === "inprogress").length;
    const totalOD = all.filter(i => isOverdue(i)).length;
    const people = Object.values(byPerson).sort((a,b) => b.issues.length - a.issues.length);

    document.getElementById("s-people").textContent = people.length;
    document.getElementById("s-tasks").textContent = totalTasks;
    document.getElementById("s-inprogress").textContent = totalIP;
    document.getElementById("s-overdue").textContent = totalOD;
    document.getElementById("s-pts").textContent = totalPts;
    document.getElementById("summary").style.display = "flex";

    // Render cards
    const grid = document.getElementById("grid");
    for (const p of people) {
      const card = buildCard(p);
      grid.appendChild(card.el);
      allCards.push({ name: p.name.toLowerCase(), el: card.el });
    }

    document.getElementById("status").className = "status ok";
    document.getElementById("status").textContent = `✅ Loaded ${totalTasks} tasks across ${people.length} people`;
  } catch(e) {
    document.getElementById("status").className = "status err";
    document.getElementById("status").textContent = "❌ Error: " + e.message + " — is the proxy running?";
  }
}

function buildCard(p) {
  const issues = p.issues;
  const todo = issues.filter(i => statusCategory(i) === "todo").length;
  const ip = issues.filter(i => statusCategory(i) === "inprogress").length;
  const done = issues.filter(i => statusCategory(i) === "done").length;
  const overdue = issues.filter(i => isOverdue(i)).length;
  const pts = issues.reduce((s,i) => s + (i.fields.customfield_10016||0), 0);
  const color = avatarColor(p.name);

  const el = document.createElement("div");
  el.className = "person-card";
  el.innerHTML = `
    <div class="person-header">
      <div class="avatar" style="background:${color}">${initials(p.name)}</div>
      <div>
        <div class="person-name">${p.name}</div>
        <div class="person-meta">${issues.length} tasks · ${pts} pts</div>
      </div>
      <div class="pills">
        ${todo ? `<span class="pill todo">${todo} To Do</span>` : ""}
        ${ip ? `<span class="pill inprogress">${ip} In Progress</span>` : ""}
        ${overdue ? `<span class="pill overdue">⚠️ ${overdue} Overdue</span>` : ""}
      </div>
    </div>
    <div class="task-list">
      ${issues.length === 0 ? '<div class="no-tasks">No open tasks</div>' :
        issues.sort((a,b) => isOverdue(b)-isOverdue(a) || (statusCategory(a)==="inprogress"?-1:1))
        .map(i => {
          const cat = statusCategory(i);
          const type = issueType(i);
          const pts = i.fields.customfield_10016;
          const due = i.fields.duedate;
          const od = isOverdue(i);
          return `<div class="task-row">
            <span class="status-dot dot-${cat}"></span>
            <div class="task-info">
              <div class="task-key">${i.key}</div>
              <div class="task-summary">${i.fields.summary}</div>
              <div class="task-badges">
                <span class="badge ${type==="bug"?"bug":type==="story"?"story":type==="sub-task"?"subtask":"task"}">${i.fields.issuetype?.name||"Task"}</span>
                ${pts ? `<span class="badge pts">${pts} pts</span>` : ""}
                ${due ? `<span class="badge ${od?"overdue":""}">${od?"⚠️ ":""}${formatDate(due)}</span>` : ""}
              </div>
            </div>
          </div>`;
        }).join("")}
    </div>`;
  return { el };
}

function filterCards() {
  const q = document.getElementById("search-input").value.toLowerCase();
  for (const c of allCards) {
    c.el.style.display = c.name.includes(q) ? "" : "none";
  }
}

loadAll();
</script>
</body>
</html>""";

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
            return

        # Strip /jira prefix for Jira API calls
        jira_path = self.path.replace("/jira", "", 1)
        # Use correct search endpoint
        if jira_path.startswith("/search"):
            jira_path = jira_path  # keep as /search for older Jira
        url = f"https://{JIRA_DOMAIN}/rest/api/2{jira_path}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json"
        })
        try:
            with urllib.request.urlopen(req, context=ssl_ctx) as r:
                body = r.read()
            self.send_response(200)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host_ip = s.getsockname()[0]
    s.close()
except Exception:
    host_ip = "unknown"
print("✅ Jira People Dashboard running!")
print(f"👉 You:       http://localhost:8765")
print(f"👉 Colleague: http://{host_ip}:8765")
HTTPServer(("0.0.0.0", 8765), Handler).serve_forever()
