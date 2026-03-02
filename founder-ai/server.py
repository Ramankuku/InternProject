import os
import uuid
import threading
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from config import GEMINI_API_KEY, OUTPUT_DIR
from agents import planner_agent, executor_agent, decision_agent, generate_final_strategy

sessions = {}

app = FastAPI(title="Founder AI")

class StartRequest(BaseModel):
    goal: str

def run_pipeline(session_id: str, goal: str):
    session = sessions[session_id]

    def log(msg):
        session["logs"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        all_research = ""
        all_documents = {}
        session["phase"] = "planner"
        session["step"] = "Creating plan..."
        log("🧠 Planner Agent starting...")

        plan = planner_agent(client, goal, log=log)
        session["total_steps"] = len(plan)
        log(f"📋 Plan ready: {len(plan)} steps")

        session["phase"] = "executor"
        session["step"] = "Executing plan..."
        log("⚡ Executor Agent starting...")
        research, documents = executor_agent(client, goal, plan, log=log)
        all_research += research
        all_documents.update(documents)

        session["completed_steps"] = len(plan)
        session["progress"] = 70

        session["phase"] = "decision"
        session["step"] = "Reviewing results..."
        session["progress"] = 75
        log("🎯 Decision Agent reviewing...")

        decision = decision_agent(client, goal, all_research, all_documents, log=log)

        if not decision.get("approved", True):
            gaps = decision.get("gaps", [])
            log(f"🔄 Replanning to address {len(gaps)} gaps...")
            session["phase"] = "planner"
            session["progress"] = 80

            extra = f"Previous research had gaps: {', '.join(gaps)}"
            plan2 = planner_agent(client, goal, extra, log=log)
            research2, docs2 = executor_agent(client, goal, plan2, log=log)
            all_research += research2
            all_documents.update(docs2)

            session["phase"] = "decision"
            decision = decision_agent(client, goal, all_research, all_documents, log=log)

        session["phase"] = "strategy"
        session["step"] = "Generating final strategy..."
        session["progress"] = 90
        log("📝 Generating final strategy...")

        strategy = generate_final_strategy(client, goal, all_research, decision, log=log)

        for doc_type, content in all_documents.items():
            path = os.path.join(OUTPUT_DIR, f"{doc_type}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        strategy_path = os.path.join(OUTPUT_DIR, "strategy.md")
        with open(strategy_path, "w", encoding="utf-8") as f:
            f.write(strategy)
        session["status"] = "completed"
        session["progress"] = 100
        session["step"] = "Done!"
        session["result"] = {
            "strategy": strategy,
            "documents": all_documents,
            "confidence": decision.get("confidence", 0.7),
            "strengths": decision.get("strengths", []),
            "risks": decision.get("risks", []),
        }
        log("✅ Pipeline complete!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        session["status"] = "error"
        session["step"] = f"Error: {str(e)}"
        log(f"Error: {str(e)}")
@app.post("/api/start")
async def start(req: StartRequest):
    if not GEMINI_API_KEY:
        return JSONResponse({"error": "GEMINI_API_KEY not set in .env"}, 400)
    if not req.goal.strip():
        return JSONResponse({"error": "Goal cannot be empty"}, 400)

    sid = str(uuid.uuid4())[:8]
    sessions[sid] = {
        "goal": req.goal,
        "status": "running",
        "phase": "starting",
        "step": "Initializing...",
        "progress": 0,
        "total_steps": 0,
        "completed_steps": 0,
        "logs": [],
        "result": None,
    }

    t = threading.Thread(target=run_pipeline, args=(sid, req.goal), daemon=True)
    t.start()

    return {"session_id": sid}


@app.get("/api/status/{sid}")
async def status(sid: str):
    s = sessions.get(sid)
    if not s:
        return JSONResponse({"error": "Session not found"}, 404)
    return {
        "status": s["status"],
        "phase": s["phase"],
        "step": s["step"],
        "progress": s["progress"],
        "logs": s["logs"][-30:],
    }


@app.get("/api/results/{sid}")
async def results(sid: str):
    s = sessions.get(sid)
    if not s:
        return JSONResponse({"error": "Session not found"}, 404)
    if s["status"] != "completed":
        return {"status": s["status"]}
    return {"status": "completed", **s["result"]}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Founder AI</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }

.container { max-width: 1000px; margin: 0 auto; padding: 20px; }

/* Header */
.header { text-align: center; padding: 40px 0 30px; }
.header h1 { font-size: 2.5em; background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header p { color: #94a3b8; margin-top: 8px; font-size: 1.1em; }

/* Input Section */
.input-section { background: #1e293b; border-radius: 16px; padding: 30px; margin-bottom: 24px; border: 1px solid #334155; }
.input-section textarea { width: 100%; background: #0f172a; border: 1px solid #475569; border-radius: 10px; padding: 14px; color: #e2e8f0; font-size: 16px; resize: vertical; min-height: 80px; font-family: inherit; }
.input-section textarea:focus { outline: none; border-color: #818cf8; }
.input-section textarea::placeholder { color: #64748b; }
.btn { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; padding: 12px 32px; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 14px; width: 100%; transition: opacity 0.2s; }
.btn:hover { opacity: 0.9; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Progress */
.progress-section { background: #1e293b; border-radius: 16px; padding: 24px; margin-bottom: 24px; border: 1px solid #334155; display: none; }
.progress-bar-bg { background: #334155; border-radius: 8px; height: 12px; overflow: hidden; margin: 12px 0; }
.progress-bar { background: linear-gradient(90deg, #6366f1, #8b5cf6); height: 100%; border-radius: 8px; transition: width 0.5s ease; width: 0%; }
.phase-badge { display: inline-block; background: #312e81; color: #a5b4fc; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.step-text { color: #94a3b8; margin-top: 8px; font-size: 14px; }
.logs { background: #0f172a; border-radius: 10px; padding: 14px; margin-top: 14px; max-height: 250px; overflow-y: auto; font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 13px; line-height: 1.6; }
.logs div { color: #94a3b8; }

/* Tabs */
.tabs-section { display: none; }
.tab-bar { display: flex; gap: 4px; background: #1e293b; border-radius: 12px; padding: 4px; margin-bottom: 16px; }
.tab-btn { flex: 1; padding: 10px; border: none; background: transparent; color: #94a3b8; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
.tab-btn.active { background: #6366f1; color: white; }
.tab-btn:hover:not(.active) { background: #334155; }
.tab-content { background: #1e293b; border-radius: 16px; padding: 24px; border: 1px solid #334155; min-height: 300px; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* Strategy tab */
.confidence { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; padding: 16px; background: #0f172a; border-radius: 10px; }
.conf-score { font-size: 2em; font-weight: 700; }
.conf-bar-bg { flex: 1; background: #334155; border-radius: 6px; height: 8px; }
.conf-bar { background: #22c55e; height: 100%; border-radius: 6px; transition: width 0.5s; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
.tag-green { background: #14532d; color: #4ade80; padding: 4px 10px; border-radius: 6px; font-size: 13px; }
.tag-yellow { background: #422006; color: #fbbf24; padding: 4px 10px; border-radius: 6px; font-size: 13px; }

/* Markdown content */
.md-content { line-height: 1.7; color: #cbd5e1; }
.md-content h1 { font-size: 1.6em; color: #f1f5f9; margin: 20px 0 10px; border-bottom: 1px solid #334155; padding-bottom: 8px; }
.md-content h2 { font-size: 1.3em; color: #e2e8f0; margin: 16px 0 8px; }
.md-content h3 { font-size: 1.1em; color: #cbd5e1; margin: 12px 0 6px; }
.md-content p { margin: 8px 0; }
.md-content ul, .md-content ol { margin: 8px 0 8px 24px; }
.md-content li { margin: 4px 0; }
.md-content strong { color: #f1f5f9; }
.md-content code { background: #334155; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }

/* Download button */
.dl-btn { display: inline-block; background: #1e293b; border: 1px solid #475569; color: #a5b4fc; padding: 8px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; margin-top: 12px; text-decoration: none; transition: background 0.2s; }
.dl-btn:hover { background: #334155; }

/* Reset button */
.reset-btn { background: #1e293b; border: 1px solid #475569; color: #94a3b8; padding: 10px 24px; border-radius: 10px; cursor: pointer; font-size: 14px; margin-top: 16px; width: 100%; }
.reset-btn:hover { background: #334155; }
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>&#x1F680; Founder AI</h1>
    <p>AI-Powered Startup Strategy Generator</p>
  </div>

  <!-- Input -->
  <div class="input-section" id="inputSection">
    <textarea id="goalInput" placeholder="Describe your startup idea... e.g., Build an AI-powered healthcare startup in India that uses NLP for patient diagnosis"></textarea>
    <button class="btn" id="startBtn" onclick="startPipeline()">&#x1F680; Generate Strategy</button>
  </div>

  <!-- Progress -->
  <div class="progress-section" id="progressSection">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <span class="phase-badge" id="phaseBadge">starting</span>
      <span id="progressPct" style="color: #a5b4fc; font-weight: 600;">0%</span>
    </div>
    <div class="progress-bar-bg"><div class="progress-bar" id="progressBar"></div></div>
    <div class="step-text" id="stepText">Initializing...</div>
    <div class="logs" id="logsBox"></div>
  </div>

  <!-- Results Tabs -->
  <div class="tabs-section" id="tabsSection">
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('strategy')">&#x1F3AF; Strategy</button>
      <button class="tab-btn" onclick="switchTab('business_plan')">&#x1F4CB; Business Plan</button>
      <button class="tab-btn" onclick="switchTab('pitch_deck')">&#x1F4CA; Pitch Deck</button>
      <button class="tab-btn" onclick="switchTab('roadmap')">&#x1F5FA; Roadmap</button>
    </div>
    <div class="tab-content">
      <div class="tab-panel active" id="panel-strategy">
        <div class="confidence" id="confBox"></div>
        <div id="strengthsRisks"></div>
        <div class="md-content" id="strategyContent"></div>
        <a class="dl-btn" id="dlStrategy" download="strategy.md">&#x1F4E5; Download Strategy</a>
      </div>
      <div class="tab-panel" id="panel-business_plan">
        <div class="md-content" id="bpContent"></div>
        <a class="dl-btn" id="dlBp" download="business_plan.md">&#x1F4E5; Download Business Plan</a>
      </div>
      <div class="tab-panel" id="panel-pitch_deck">
        <div class="md-content" id="pdContent"></div>
        <a class="dl-btn" id="dlPd" download="pitch_deck.md">&#x1F4E5; Download Pitch Deck</a>
      </div>
      <div class="tab-panel" id="panel-roadmap">
        <div class="md-content" id="rmContent"></div>
        <a class="dl-btn" id="dlRm" download="roadmap.md">&#x1F4E5; Download Roadmap</a>
      </div>
    </div>
    <button class="reset-btn" onclick="resetUI()">&#x1F504; Start New Strategy</button>
  </div>

</div>

<script>
let sessionId = null;
let pollTimer = null;

async function startPipeline() {
  const goal = document.getElementById('goalInput').value.trim();
  if (!goal) return alert('Please enter a startup goal');

  document.getElementById('startBtn').disabled = true;
  document.getElementById('progressSection').style.display = 'block';
  document.getElementById('tabsSection').style.display = 'none';
  document.getElementById('logsBox').innerHTML = '';

  try {
    const res = await fetch('/api/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({goal})
    });
    const data = await res.json();
    if (data.error) { alert(data.error); document.getElementById('startBtn').disabled = false; return; }
    sessionId = data.session_id;
    pollTimer = setInterval(pollStatus, 2000);
  } catch(e) { alert('Failed to start: ' + e); document.getElementById('startBtn').disabled = false; }
}

async function pollStatus() {
  if (!sessionId) return;
  try {
    const res = await fetch('/api/status/' + sessionId);
    const data = await res.json();

    document.getElementById('phaseBadge').textContent = phaseLabel(data.phase);
    document.getElementById('progressBar').style.width = data.progress + '%';
    document.getElementById('progressPct').textContent = data.progress + '%';
    document.getElementById('stepText').textContent = data.step;

    const logsBox = document.getElementById('logsBox');
    logsBox.innerHTML = data.logs.map(l => '<div>[' + l.time + '] ' + escHtml(l.msg) + '</div>').join('');
    logsBox.scrollTop = logsBox.scrollHeight;

    if (data.status === 'completed') {
      clearInterval(pollTimer);
      loadResults();
    } else if (data.status === 'error') {
      clearInterval(pollTimer);
      document.getElementById('startBtn').disabled = false;
    }
  } catch(e) { console.error(e); }
}

async function loadResults() {
  const res = await fetch('/api/results/' + sessionId);
  const data = await res.json();

  // Strategy tab
  const conf = data.confidence || 0;
  const pct = Math.round(conf * 100);
  const color = conf >= 0.7 ? '#22c55e' : conf >= 0.5 ? '#eab308' : '#ef4444';
  document.getElementById('confBox').innerHTML =
    '<div class="conf-score" style="color:'+color+'">' + pct + '%</div>' +
    '<div style="flex:1"><div style="color:#94a3b8;margin-bottom:4px">Confidence Score</div>' +
    '<div class="conf-bar-bg"><div class="conf-bar" style="width:'+pct+'%;background:'+color+'"></div></div></div>';

  let srHtml = '';
  if (data.strengths && data.strengths.length) {
    srHtml += '<div class="tags">' + data.strengths.map(s => '<span class="tag-green">&#x2705; ' + escHtml(s) + '</span>').join('') + '</div>';
  }
  if (data.risks && data.risks.length) {
    srHtml += '<div class="tags">' + data.risks.map(r => '<span class="tag-yellow">&#x26A0;&#xFE0F; ' + escHtml(r) + '</span>').join('') + '</div>';
  }
  document.getElementById('strengthsRisks').innerHTML = srHtml;

  setMd('strategyContent', data.strategy || 'No strategy generated.');
  setDl('dlStrategy', data.strategy || '');

  const docs = data.documents || {};
  setMd('bpContent', docs.business_plan || 'Not generated.');
  setDl('dlBp', docs.business_plan || '');
  setMd('pdContent', docs.pitch_deck || 'Not generated.');
  setDl('dlPd', docs.pitch_deck || '');
  setMd('rmContent', docs.roadmap || 'Not generated.');
  setDl('dlRm', docs.roadmap || '');

  document.getElementById('tabsSection').style.display = 'block';
  document.getElementById('startBtn').disabled = false;
}

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach((b, i) => {
    b.classList.toggle('active', b.textContent.includes(tabLabel(name)));
  });
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
}

function tabLabel(name) {
  return {strategy:'Strategy', business_plan:'Business', pitch_deck:'Pitch', roadmap:'Roadmap'}[name] || name;
}

function phaseLabel(p) {
  return {starting:'Starting', planner:'\\u{1F9E0} Planner', executor:'\\u26A1 Executor', decision:'\\u{1F3AF} Decision', strategy:'\\u{1F4DD} Strategy'}[p] || p;
}

function resetUI() {
  sessionId = null;
  document.getElementById('progressSection').style.display = 'none';
  document.getElementById('tabsSection').style.display = 'none';
  document.getElementById('goalInput').value = '';
  document.getElementById('startBtn').disabled = false;
}

function escHtml(s) {
  const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

function setMd(id, md) {
  // Simple markdown to HTML conversion
  let html = escHtml(md);
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  html = html.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\\/li>)/gs, '<ul>$1</ul>');
  html = html.replace(/\\n\\n/g, '</p><p>');
  html = html.replace(/\\n/g, '<br>');
  html = '<p>' + html + '</p>';
  document.getElementById(id).innerHTML = html;
}

function setDl(id, content) {
  const blob = new Blob([content], {type: 'text/markdown'});
  document.getElementById(id).href = URL.createObjectURL(blob);
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Founder AI - Web UI")
    print(f"   Open: http://localhost:5000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
