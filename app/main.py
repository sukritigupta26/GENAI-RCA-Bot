from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
import uuid
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()
import asyncio
import json

# Import Temporal + Workflow
from temporalio.client import Client
from temporal_app.workflows import RCAAgentWorkflow
from temporal_app.shared import RCAInput

# Try to import Kubernetes tools, but continue if not available
try:
    from app.tools.kubernetes import restart_kubernetes_pod, scale_deployment
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Kubernetes tools not available, some RCA actions may be limited")

app = FastAPI(title="GENAI RCA Agent - Temporal Edition")

class AnalyzeRequest(BaseModel):
    source: str
    logs: str
    context: dict = {}

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Main endpoint called by Jenkins, Kubernetes webhooks, etc."""
    try:
        # Connect to Temporal (do this once per request or use a singleton)
        client = await Client.connect("localhost:7233")   # Change to Temporal Cloud URL in production

        # Start the durable RCA Workflow
        workflow_handle = await client.start_workflow(
            RCAAgentWorkflow.run,
            RCAInput(
                source=request.source,
                logs=request.logs,
                context=request.context
            ),
            id=f"rca-{uuid.uuid4()}",                    # Unique workflow ID
            task_queue="rca-agent-task-queue",
            # Optional: Add search attributes for easier filtering in Temporal UI
            # search_attributes={"RCA_Source": [request.source]}
        )

        # Wait for the workflow to complete (with timeout)
        result = await workflow_handle.result(timeout=timedelta(minutes=10))

        return {
            "workflow_id": workflow_handle.id,
            "rca_summary": result.rca_summary,
            "actions_taken": result.actions_taken,
            "status": result.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start RCA workflow: {str(e)}")


@app.post("/webhook/jenkins")
@app.post("/webhook/kubernetes")
@app.post("/webhook/tower")
async def webhook(request: Request):
    """Generic webhook endpoint for CI/CD systems"""
    try:
        body = await request.json()
        # You can add logic to extract logs from different sources
        logs = json.dumps(body, indent=2) if isinstance(body, dict) else str(body)
        
        return await analyze(AnalyzeRequest(
            source=request.url.path.split("/")[-1],
            logs=logs
        ))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)