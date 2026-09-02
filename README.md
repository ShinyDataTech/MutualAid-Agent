# MutualAid-Agent: Autonomous Emergency Resource Dispatcher

[![Hackathon Track](https://img.shields.io/badge/Track-Good%20Neighbor%20Agents-green.svg)](https://agentsforhumans.devpost.com)
[![SDK](https://img.shields.io/badge/SDK-Strands%20Agents%20SDK-blue.svg)](https://strandsagents.com)
[![Cloud](https://img.shields.io/badge/AWS-Amazon%20Bedrock%20%7C%20DynamoDB%20%7C%20Lambda-orange.svg)](https://aws.amazon.com)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Pytest-15%20Passing-brightgreen.svg)](tests)

> **Built for the "Good Neighbor Agents" Track of the Agents for Humans Hackathon 2026 using the Strands Agents SDK.**

---

## 🌟 Overview

**MutualAid-Agent** is a serverless, autonomous background AI agent engineered to coordinate localized emergency mutual aid logistics during severe weather events and municipal crises.

Instead of building another dashboard or mobile app that requires constant human attention, **MutualAid-Agent operates invisibly in the background 24/7**. It ingests incoming storm radar webhooks, emergency broadcast alerts, and IoT sensor distress pings. Using the **Strands Agents SDK** and **Amazon Bedrock**, it autonomously:
1. **Parses the emergency situation** and identifies required mutual aid machinery (e.g., flash flood ➡️ 3000 GPH submersible sump pump; fallen tree blocking road ➡️ 18" chainsaw; medical power outage ➡️ dual-fuel generator).
2. **Queries the community resource registry** in **Amazon DynamoDB** and calculates geospatial proximity using the Haversine formula.
3. **Formulates a single-decision SMS** sent directly to the neighborhood coordinator:
   > `"[MutualAid Alert] Flood at 10 Main St. Dispatch Neighbor Bob's 2-inch submersible pump (0.03 mi away)? Reply YES to approve, NO for alternative."`
4. **Executes dispatch and notifications** the instant the coordinator replies `YES`, automatically alerting the equipment owner with staging instructions and updating inventory state in DynamoDB. If the coordinator replies `NO`, the agent automatically pivots to the next closest alternative resource.

---

## 🏗️ Architecture & Data Flow

```
+-------------------------------------------------------------------------------+
|                        AUTONOMOUS INGESTION LAYER                             |
|  [NWS Weather Feed / IoT]                   [Twilio Coordinator SMS]          |
+-------------------------------------------------------------------------------+
                             |                                      |
                             v                                      v
                    [POST /webhooks/weather]               [POST /webhooks/sms]
                             |                                      |
                             +------------------+-------------------+
                                                |
                                                v
+-------------------------------------------------------------------------------+
|                      AWS LAMBDA SERVERLESS COMPUTE LAYER                      |
|       weather_webhook.py                              sms_webhook.py          |
+-------------------------------------------------------------------------------+
                                                |
                                                v
+-------------------------------------------------------------------------------+
|                     STRANDS AGENTS SDK & AMAZON BEDROCK                       |
|   MutualAid-Agent: Reasoner, Alert Classifier, Haversine Matcher, Formatter   |
+-------------------------------------------------------------------------------+
                                                |
                                                v
+-------------------------------------------------------------------------------+
|                      AMAZON DYNAMODB PERSISTENCE LAYER                        |
|   [MutualAid-Resources]      [MutualAid-Incidents]     [MutualAid-Dispatches] |
+-------------------------------------------------------------------------------+
                                                |
                                                v
+-------------------------------------------------------------------------------+
|                        HUMAN-IN-THE-LOOP APPROVAL                             |
|   Coordinator receives SMS -> Single Decision "YES" -> Owner Dispatched       |
+-------------------------------------------------------------------------------+
```

---

## 📂 Project Structure

```
Agents_for_Humans_Hackathon/
├── mutualaid_agent/
│   ├── __init__.py                # Package initialization
│   ├── config.py                  # Environment and Bedrock configurations
│   ├── agent.py                   # Core Strands Agent definition & coordinator
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic data schemas (Resources, Incidents, Proposals)
│   │   ├── dynamodb_client.py     # DynamoDB client (boto3 + local in-memory fallback)
│   │   └── seed_data.py           # Neighborhood asset seed generator
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── matcher.py             # Haversine proximity calculation & candidate ranking
│   │   └── dispatch_planner.py    # Single-decision SMS formatting & approval state machine
│   ├── tools/
│   │   ├── __init__.py            # Tool exports for Strands Agent
│   │   ├── alert_tools.py         # Strands @tool for alert ingestion & classification
│   │   ├── db_tools.py            # Strands @tool for querying inventory by proximity
│   │   └── notification_tools.py  # Strands @tool for single-decision SMS creation
│   └── handlers/
│       ├── __init__.py
│       ├── weather_webhook.py     # AWS Lambda handler for weather alerts
│       └── sms_webhook.py         # AWS Lambda handler for incoming Twilio SMS
├── submission_materials/
│   ├── project_overview.txt       # Project Name (<60 chars) and Elevator Pitch (<200 chars)
│   ├── devpost_story.md           # Full Devpost submission story formatted in Markdown
│   ├── architecture_diagram.md    # Mermaid.js dataflow & cloud architecture diagrams
│   └── video_script.md            # 5-minute scene-by-scene demo video script
├── tests/
│   ├── test_matcher.py            # Geospatial math and ranking tests
│   ├── test_agent_tools.py        # Strands SDK tool execution tests
│   ├── test_weather_webhook.py    # Inbound weather webhook parsing tests
│   ├── test_sms_webhook.py        # Coordinator SMS reply processing tests
│   └── test_dispatch_flow.py      # End-to-end integration test suite
├── run_local_demo.py              # Interactive terminal demonstration script
├── serverless.yml                 # Serverless Framework deployment config
├── template.yaml                  # AWS SAM & Bedrock AgentCore template
├── requirements.txt               # Python package dependencies
├── LICENSE                        # Standard MIT License
└── README.md                      # Project documentation
```

---

## 🚀 Quickstart & Local Execution

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11)
- `pip` or virtual environment manager

### 2. Setup Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Interactive End-to-End Demo
Run the standalone local simulator to observe the complete autonomous background lifecycle:
```bash
python run_local_demo.py
```

**What you will see in the demo:**
1. Initialization and seeding of neighborhood equipment (pumps, generators, chainsaws, sandbags, 4x4s, trauma kits) into DynamoDB.
2. Ingestion of a live severe flash flood warning webhook for `10 Main St`.
3. Background reasoning by MutualAid-Agent matching Neighbor Bob's pump (0.03 mi away).
4. Generation and transmission of the single-decision SMS:
   `"[MutualAid Alert] Flood at 10 Main St, Downtown. Dispatch Neighbor Bob's 2-inch Submersible Pump (0.03 mi away)? Reply YES to approve, NO for alternative."`
5. Simulated coordinator replying `YES` via Twilio webhook.
6. Immediate status updates in DynamoDB (`DISPATCHED`) and staging dispatch instructions sent to the equipment owner.

---

## 🧪 Running Automated Tests

Run the full Pytest suite (15 unit and integration tests):
```bash
pytest tests/ -v
```

**Test Coverage Highlights:**
- `test_matcher.py`: Validates Haversine distance accuracy and proximity sorting.
- `test_agent_tools.py`: Validates Strands `@tool` decorators and schema compliance.
- `test_weather_webhook.py`: Validates multi-hazard alert normalization (floods, tree obstructions, power failures).
- `test_sms_webhook.py`: Validates coordinator response handling (`YES`, `NO`, `STATUS`).
- `test_dispatch_flow.py`: Validates full end-to-end state transitions and alternative resource fallback logic.

---

## ☁️ AWS & Bedrock AgentCore Deployment

MutualAid-Agent is designed for zero-maintenance serverless deployment.

### Option A: Serverless Framework
```bash
serverless deploy --stage prod
```

### Option B: AWS SAM (Serverless Application Model)
```bash
sam build
sam deploy --guided
```

### Environment Variables
| Variable | Description | Default |
|---|---|---|
| `BEDROCK_MODEL_ID` | Model identifier on Amazon Bedrock | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `AWS_DEFAULT_REGION` | Target AWS region | `us-east-1` |
| `RESOURCES_TABLE` | DynamoDB Community Inventory Table | `MutualAid-Resources` |
| `INCIDENTS_TABLE` | DynamoDB Incidents Table | `MutualAid-Incidents` |
| `DISPATCHES_TABLE` | DynamoDB Dispatches Table | `MutualAid-Dispatches` |
| `COORDINATOR_PHONE`| Phone number of primary community coordinator | `+15550199283` |
| `USE_MOCK_DB` | Set to `true` to use local in-memory DynamoDB engine | `false` |

---

## 📄 Submission Materials

All required hackathon submission assets are compiled in the [`submission_materials/`](submission_materials/) directory:
- [`project_overview.txt`](submission_materials/project_overview.txt): Project Title (<60 chars) and Elevator Pitch (<200 chars).
- [`devpost_story.md`](submission_materials/devpost_story.md): Full Project Story (Inspiration, What it does, How we built it, Challenges, What's next).
- [`architecture_diagram.md`](submission_materials/architecture_diagram.md): Mermaid.js sequence and cloud architecture diagrams.
- [`video_script.md`](submission_materials/video_script.md): 5-minute scene-by-scene video script addressing problem, audience, importance, and demo walkthrough.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
