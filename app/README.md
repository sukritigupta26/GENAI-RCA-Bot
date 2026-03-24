GENAI RCA Agent
Autonomous Root Cause Analysis & Remediation Agent for DevOps & SRE
An intelligent AI agent that ingests logs from Kubernetes, Jenkins, Ansible Tower, or any CI/CD system, performs root cause analysis, and automatically remediates common issues by restarting pods, triggering Jenkins jobs, scaling deployments, launching Ansible playbooks, and more.
Built with FastAPI + LangGraph (ReAct) and supports xAI Grok, GPT-4o, or Claude.

Features

Real-time Root Cause Analysis (RCA) from raw logs
Autonomous remediation using tool-calling
Native integrations:
Kubernetes (restart/create pods, scale deployments)
Jenkins (trigger jobs with parameters)
Ansible Tower / AWX (launch job templates)

Webhook support for Jenkins, ArgoCD, GitLab CI, Prometheus alerts
Optional Human-in-the-Loop approval via Slack/Teams
Docker-first deployment (runs in < 60 seconds)
Fully auditable actions with detailed logs


Quick Start (60 seconds)
Bash# 1. Clone the repository
git clone https://github.com/xai-devops/genai-rca-agent.git

# 2. Go to the project directory
cd genai-rca-agent

# 3. Copy and edit environment variables
cp .env.example .env
# ← Edit .env with your API keys and credentials

# 4. Start the agent
docker compose up --build -d
The agent will be available at http://localhost:8000

Test the Agent Immediately
Send a sample issue and watch the agent diagnose + fix it:
Bashcurl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "source": "kubernetes",
    "logs": "2025-03-24T12:01:23Z pod/frontend-7f8b9c4d5-xyz123 CrashLoopBackOff\nError: liveness probe failed: HTTP probe failed with statuscode 503\nBack-off restarting failed container frontend in pod frontend-7f8b9c4d5-xyz123"
  }'
Expected Flow:

Parse the incoming logs
Run ReAct reasoning with the LLM
Identify root cause
Call appropriate remediation tools (e.g., restart pod, trigger Jenkins rollback job)
Return a clear summary of actions taken


Project Structure
textgenai-rca-agent/
├── app/
│   ├── main.py                 # FastAPI endpoints & webhooks
│   ├── agent.py                # LangGraph ReAct agent logic
│   └── tools/
│       ├── kubernetes.py       # K8s restart, create, scale
│       ├── jenkins.py          # Trigger Jenkins jobs
│       └── ansible_tower.py    # Launch Tower jobs
├── .env.example
├── requirements.txt
├── docker-compose.yml
└── README.md

Configuration (.env)
Make sure to update the following in .env:
env# LLM Configuration (recommended: xAI Grok)
LLM_PROVIDER=xai
XAI_API_KEY=xai-...

# Kubernetes (use in-cluster for production)
K8S_IN_CLUSTER=true

# Jenkins
JENKINS_URL=http://jenkins.yourcompany.com:8080
JENKINS_USERNAME=admin
JENKINS_API_TOKEN=your-token-here

# Ansible Tower
ANSIBLE_TOWER_URL=https://tower.yourcompany.com
ANSIBLE_TOWER_USERNAME=admin
ANSIBLE_TOWER_PASSWORD=your-password

# Optional: Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

Available Tools (Remediation Actions)
Tool,Description
restart_kubernetes_pod,Delete & recreate a pod
create_kubernetes_pod,Create a new pod from manifest
scale_deployment,Scale Deployment replicas
trigger_jenkins_job,Trigger any Jenkins job with parameters
launch_ansible_tower_job,Launch Ansible Tower job template