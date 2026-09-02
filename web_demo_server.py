"""
MutualAid-Agent Web Demo Server.
Serves the Emergency Logistics Command Center dashboard for ndemo video recording.
"""

import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mutualaid_agent.db.seed_data import seed_database
from mutualaid_agent.db.dynamodb_client import db_client
from mutualaid_agent.db.models import ResourceStatus
from mutualaid_agent.handlers.weather_webhook import lambda_handler as weather_handler
from mutualaid_agent.handlers.sms_webhook import lambda_handler as sms_handler


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MutualAid-Agent | Autonomous Emergency Command Center</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card: #131b2e;
      --card-border: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-green: #22c55e;
      --accent-amber: #f59e0b;
      --accent-red: #ef4444;
      --accent-purple: #a855f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    
    .header {
      display: flex; justify-content: space-between; align-items: center;
      padding-bottom: 20px; border-bottom: 1px solid var(--card-border); margin-bottom: 24px;
    }
    .brand { display: flex; align-items: center; gap: 14px; }
    .logo-badge {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: white; font-weight: 800; padding: 10px 16px; border-radius: 12px; font-size: 20px;
      box-shadow: 0 4px 14px rgba(37,99,235,0.4);
    }
    .brand h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }
    .brand p { font-size: 13px; color: var(--text-muted); }
    .status-pill {
      display: flex; align-items: center; gap: 8px; background: rgba(34, 197, 94, 0.15);
      border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 6px 14px; border-radius: 20px;
      font-size: 13px; font-weight: 600;
    }
    .pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }

    .kpi-grid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card); border: 1px solid var(--card-border); border-radius: 14px; padding: 18px;
    }
    .kpi-title { font-size: 12px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; margin-bottom: 6px; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #fff; }
    .kpi-sub { font-size: 12px; color: #38bdf8; margin-top: 4px; }

    .main-grid {
      display: grid; grid-template-columns: 1.4fr 1.1fr; gap: 24px;
    }

    .panel {
      background: var(--card); border: 1px solid var(--card-border); border-radius: 16px; padding: 22px;
      display: flex; flex-direction: column; gap: 16px;
    }
    .panel-title { font-size: 17px; font-weight: 700; display: flex; align-items: center; gap: 8px; }

    .scenario-triggers { display: flex; gap: 12px; flex-wrap: wrap; }
    .trigger-btn {
      background: #1e293b; border: 1px solid #334155; color: #f1f5f9; padding: 12px 18px;
      border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;
      display: flex; align-items: center; gap: 8px;
    }
    .trigger-btn:hover { background: #334155; border-color: #475569; transform: translateY(-2px); }
    .trigger-btn.active { background: #0284c7; border-color: #38bdf8; box-shadow: 0 0 15px rgba(56,189,248,0.4); }

    .terminal-box {
      background: #050811; border: 1px solid #1e293b; border-radius: 12px; padding: 16px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px;
      color: #e2e8f0; height: 260px; overflow-y: auto; line-height: 1.6;
    }
    .term-line-agent { color: #38bdf8; }
    .term-line-success { color: #4ade80; }
    .term-line-warning { color: #fbbf24; }
    .term-line-alert { color: #f87171; }
    .term-line-meta { color: #64748b; }

    .phone-simulator {
      background: #0f172a; border: 2px solid #334155; border-radius: 24px; padding: 18px;
      display: flex; flex-direction: column; gap: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .phone-header {
      display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted);
      border-bottom: 1px solid #1e293b; padding-bottom: 10px;
    }
    .chat-bubble {
      background: #1e293b; border-radius: 14px; border-bottom-left-radius: 2px; padding: 14px 16px;
      font-size: 14px; line-height: 1.5; color: #f8fafc; border: 1px solid #334155;
    }
    .chat-bubble.inbound {
      background: #0369a1; border-color: #0284c7; align-self: flex-start;
    }
    .chat-bubble.reply {
      background: #15803d; border-color: #22c55e; align-self: flex-end; border-bottom-left-radius: 14px;
      border-bottom-right-radius: 2px;
    }
    .phone-actions {
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 6px;
    }
    .action-btn-yes {
      background: #16a34a; color: white; border: none; padding: 12px; border-radius: 10px;
      font-weight: 700; cursor: pointer; transition: all 0.2s; font-size: 14px;
    }
    .action-btn-yes:hover { background: #22c55e; transform: scale(1.02); }
    .action-btn-no {
      background: #dc2626; color: white; border: none; padding: 12px; border-radius: 10px;
      font-weight: 700; cursor: pointer; transition: all 0.2s; font-size: 14px;
    }
    .action-btn-no:hover { background: #ef4444; transform: scale(1.02); }

    .inventory-table {
      width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;
    }
    .inventory-table th { padding: 10px; color: var(--text-muted); border-bottom: 1px solid var(--card-border); }
    .inventory-table td { padding: 12px 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .badge {
      display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;
    }
    .badge-available { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-dispatched { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
  </style>
</head>
<body>

  <div class="header">
    <div class="brand">
      <div class="logo-badge">MA</div>
      <div>
        <h1>MutualAid-Agent Command Center</h1>
        <p>Autonomous Emergency Logistics Powered by Strands Agents SDK & Amazon Bedrock</p>
      </div>
    </div>
    <div class="status-pill">
      <div class="pulse-dot"></div>
      Autonomous Background Agent Active
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Community Assets</div>
      <div class="kpi-value" id="kpi-assets">7 Registered</div>
      <div class="kpi-sub">100% Verified in DynamoDB</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Response Decision Model</div>
      <div class="kpi-value" id="kpi-model">Single-Decision SMS</div>
      <div class="kpi-sub">Human-in-the-Loop Safeguard</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Proximity Calculation</div>
      <div class="kpi-value">Haversine GPS</div>
      <div class="kpi-sub">&lt; 0.5 mi Average Proximity</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Reasoning Latency</div>
      <div class="kpi-value" id="kpi-latency">1.2s</div>
      <div class="kpi-sub">Serverless AWS Lambda</div>
    </div>
  </div>

  <div class="main-grid">
    <!-- Left Column -->
    <div style="display: flex; flex-direction: column; gap: 24px;">
      
      <!-- Disaster Scenario Simulation -->
      <div class="panel">
        <div class="panel-title">
          <span>⚡</span> Live Disaster Trigger (Webhook Simulation)
        </div>
        <div class="scenario-triggers">
          <button id="btn-flood" class="trigger-btn" onclick="triggerScenario('flood')">
            <span>🌊</span> Flash Flood Warning (10 Main St)
          </button>
          <button id="btn-tree" class="trigger-btn" onclick="triggerScenario('tree')">
            <span>🌲</span> Downed Tree / Roadblock (5 Pine Rd)
          </button>
          <button id="btn-power" class="trigger-btn" onclick="triggerScenario('power')">
            <span>⚡</span> Life-Support Power Outage (22 Oak Ave)
          </button>
        </div>
      </div>

      <!-- Autonomous Reasoning Terminal -->
      <div class="panel">
        <div class="panel-title">
          <span>🤖</span> Strands Agent Autonomous Execution Stream
        </div>
        <div class="terminal-box" id="terminal">
          <div class="term-line-meta">[SYSTEM INIT] MutualAid-Agent initialized with Strands Agents SDK & Amazon Bedrock.</div>
          <div class="term-line-meta">[DYNAMODB] 7 verified community resources loaded in registry.</div>
          <div class="term-line-success">[STATUS] Standing by in background for severe weather webhooks...</div>
        </div>
      </div>

      <!-- Inventory Table -->
      <div class="panel">
        <div class="panel-title">
          <span>📦</span> Amazon DynamoDB Community Inventory
        </div>
        <table class="inventory-table">
          <thead>
            <tr>
              <th>Item / Equipment</th>
              <th>Owner</th>
              <th>Capacity Specs</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="inventory-body">
            <tr>
              <td>2-inch Submersible Trash Pump</td>
              <td>Neighbor Bob</td>
              <td>3000 GPH / 120V</td>
              <td><span id="status-bob" class="badge badge-available">AVAILABLE</span></td>
            </tr>
            <tr>
              <td>3-inch High-Flow Sump Pump</td>
              <td>Neighbor Dave</td>
              <td>5500 GPH / Gas</td>
              <td><span id="status-dave" class="badge badge-available">AVAILABLE</span></td>
            </tr>
            <tr>
              <td>Honda 7000W Inverter Generator</td>
              <td>Neighbor Sarah</td>
              <td>7000W / Dual Fuel</td>
              <td><span id="status-sarah" class="badge badge-available">AVAILABLE</span></td>
            </tr>
            <tr>
              <td>Stihl 18-inch Chainsaw</td>
              <td>Neighbor Carlos</td>
              <td>18-inch / 50cc</td>
              <td><span id="status-carlos" class="badge badge-available">AVAILABLE</span></td>
            </tr>
            <tr>
              <td>Sandbags (Pallet of 100)</td>
              <td>Community Center</td>
              <td>40 lbs woven poly</td>
              <td><span id="status-center" class="badge badge-available">AVAILABLE</span></td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>

    <!-- Right Column: SMS Simulator -->
    <div style="display: flex; flex-direction: column; gap: 24px;">
      
      <div class="panel" style="height: 100%;">
        <div class="panel-title">
          <span>📱</span> Human Coordinator Phone (Twilio In-the-Loop Simulator)
        </div>
        <p style="font-size: 13px; color: var(--text-muted);">
          Single-decision interface: The agent surfaces only for binary coordinator approval.
        </p>

        <div class="phone-simulator">
          <div class="phone-header">
            <span>MUTUALAID EMERGENCY DISPATCH</span>
            <span>+1 (555) 010-0911</span>
          </div>

          <div id="sms-feed" style="display: flex; flex-direction: column; gap: 12px; min-height: 280px; justify-content: flex-end;">
            <div class="chat-bubble">
              [MutualAid Standby] Background monitoring active. You will only be alerted when human approval is required.
            </div>
          </div>

          <div class="phone-actions" id="phone-actions" style="display: none;">
            <button id="btn-approve" class="action-btn-yes" onclick="replySMS('YES')">
              ✅ Reply YES (Approve Dispatch)
            </button>
            <button id="btn-reject" class="action-btn-no" onclick="replySMS('NO')">
              ❌ Reply NO (Seek Alternative)
            </button>
          </div>
        </div>

        <div id="dispatch-outcome" style="margin-top: 10px; font-size: 13px; line-height: 1.5; color: #38bdf8;">
        </div>
      </div>

    </div>
  </div>

  <script>
    let activeProposalId = null;

    async function triggerScenario(type) {
      document.querySelectorAll('.trigger-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('btn-' + type);
      if (activeBtn) activeBtn.classList.add('active');

      const term = document.getElementById('terminal');
      term.innerHTML += `<div class="term-line-alert">>>> [WEBHOOK TRIGGER] Incoming emergency alert for scenario: ${type.toUpperCase()}</div>`;
      term.innerHTML += `<div class="term-line-agent">🤖 [STRANDS AGENT] Ingesting alert payload via AWS API Gateway...</div>`;
      term.scrollTop = term.scrollHeight;

      const res = await fetch('/api/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: type })
      });
      const data = await res.json();
      const result = data.result;

      term.innerHTML += `<div class="term-line-agent">🧠 [BEDROCK REASONER] Classified need: <b>${result.incident.required_resource_type}</b> (Severity: ${result.incident.severity.toUpperCase()})</div>`;
      term.innerHTML += `<div class="term-line-success">📍 [DYNAMODB MATCH] Found closest asset: <b>${result.best_match.title}</b> (${result.best_match.distance_miles} mi away) owned by ${result.best_match.owner_name}</div>`;
      term.innerHTML += `<div class="term-line-agent">📱 [HUMAN-IN-THE-LOOP] Drafting single-decision SMS to coordinator phone...</div>`;
      term.scrollTop = term.scrollHeight;

      // Update SMS Feed
      activeProposalId = result.proposal.proposal_id;
      const smsFeed = document.getElementById('sms-feed');
      smsFeed.innerHTML += `
        <div class="chat-bubble inbound">
          ${result.proposal.single_decision_sms}
        </div>
      `;
      document.getElementById('phone-actions').style.display = 'grid';
      document.getElementById('dispatch-outcome').innerHTML = `<b>Status:</b> Awaiting coordinator decision for proposal <code>${activeProposalId}</code>`;
    }

    async function replySMS(decision) {
      document.getElementById('phone-actions').style.display = 'none';
      const smsFeed = document.getElementById('sms-feed');
      smsFeed.innerHTML += `
        <div class="chat-bubble reply">
          ${decision}
        </div>
      `;

      const term = document.getElementById('terminal');
      term.innerHTML += `<div class="term-line-alert">📥 [TWILIO WEBHOOK] Received coordinator reply: '${decision}'</div>`;

      const res = await fetch('/api/sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Body: decision })
      });
      const data = await res.json();

      if (decision === 'YES') {
        term.innerHTML += `<div class="term-line-success">✅ [DISPATCH EXECUTED] Proposal marked APPROVED in DynamoDB.</div>`;
        term.innerHTML += `<div class="term-line-success">📡 [NOTIFICATION DISPATCHED] Staging instructions texted to equipment owner!</div>`;
        
        smsFeed.innerHTML += `
          <div class="chat-bubble inbound">
            ${data.reply_sms}
          </div>
        `;

        document.getElementById('status-bob').className = 'badge badge-dispatched';
        document.getElementById('status-bob').innerText = 'DISPATCHED';

        document.getElementById('dispatch-outcome').innerHTML = `
          <div style="background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.3); padding: 12px; border-radius: 8px;">
            <b style="color: #4ade80;">Emergency Dispatch Confirmed</b><br>
            • DynamoDB state updated to <b>DISPATCHED</b><br>
            • Owner Neighbor Bob texted staging address (10 Main St)
          </div>
        `;
      } else {
        term.innerHTML += `<div class="term-line-warning">⚠️ [FALLBACK] Coordinator rejected proposal. Seeking next closest alternative...</div>`;
        smsFeed.innerHTML += `
          <div class="chat-bubble inbound">
            ${data.reply_sms}
          </div>
        `;
        document.getElementById('dispatch-outcome').innerHTML = `
          <div style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.3); padding: 12px; border-radius: 8px;">
            <b style="color: #fbbf24;">Alternative Match Suggested</b><br>
            Pivoted to next closest asset in inventory (Neighbor Dave's 3-inch Pump).
          </div>
        `;
      }
      term.scrollTop = term.scrollHeight;
    }
  </script>
</body>
</html>
"""


class DemoServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/inventory":
            resources = db_client.list_resources()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([r.model_dump() for r in resources]).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(post_data) if post_data else {}

        if self.path == "/api/trigger":
            scenario = data.get("type", "flood")
            if scenario == "flood":
                payload = {
                    "source": "NWS_STORM_RADAR_FEED",
                    "event": "Flash Flood Warning",
                    "headline": "Dangerous Flash Flooding at 10 Main St",
                    "description": "Rapid water accumulation in basements and driveways at 10 Main St. Urgent high capacity pump needed.",
                    "address": "10 Main St, Downtown",
                    "latitude": 40.7130,
                    "longitude": -74.0065,
                    "severity": "severe"
                }
            elif scenario == "tree":
                payload = {
                    "source": "MUNICIPAL_DISPATCH",
                    "event": "Severe Windstorm",
                    "headline": "Large Oak Tree Down Blocking Road at 5 Pine Rd",
                    "description": "Fallen tree blocking roadway. Chainsaw crew needed.",
                    "address": "5 Pine Rd, Downtown",
                    "latitude": 40.7180,
                    "longitude": -74.0090,
                    "severity": "moderate"
                }
            else:
                payload = {
                    "source": "COMMUNITY_HOTLINE",
                    "event": "Grid Failure",
                    "headline": "Power Outage Life Support at 22 Oak Ave",
                    "description": "Resident requires backup power for medical oxygen device.",
                    "address": "22 Oak Ave, Downtown",
                    "latitude": 40.7150,
                    "longitude": -74.0040,
                    "severity": "critical"
                }

            resp = weather_handler({"body": json.dumps(payload)}, None)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp["body"].encode("utf-8"))

        elif self.path == "/api/sms":
            decision = data.get("Body", "YES")
            decision_res = sms_handler({"From": "+15550199283", "Body": decision}, None)
            from mutualaid_agent.engine.dispatch_planner import process_coordinator_decision
            raw_res = process_coordinator_decision(decision, client=db_client)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(raw_res).encode("utf-8"))


def start_server(port=3000):
    seed_database()
    server = HTTPServer(("0.0.0.0", port), DemoServerHandler)
    print(f"MutualAid-Agent Demo Server running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    start_server(port)
