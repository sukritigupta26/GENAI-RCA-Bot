from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from .agent import rca_agent
from langchain_core.messages import HumanMessage
import asyncio
import json

app = FastAPI(title="GENAI RCA Agent")

class AnalyzeRequest(BaseModel):
    source: str
    logs: str
    context: dict = {}

@app.post("/analyze")
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Main endpoint for Jenkins, Ansible Tower, K8s logs, etc."""
    user_message = f"""
Source: {request.source}
Context: {json.dumps(request.context)}
Raw logs:
{request.logs}
    """

    initial_state = {"messages": [HumanMessage(content=user_message)]}
    
    result = await asyncio.to_thread(rca_agent.invoke, initial_state)
    
    final_message = result["messages"][-1].content
    
    # Optional: send Slack notification here
    return {
        "rca": final_message,
        "status": "resolved" if "✅" in final_message else "needs_human"
    }

@app.post("/webhook/jenkins")
@app.post("/webhook/k8s")
@app.post("/webhook/tower")
async def webhook(request: Request):
    """Generic webhook for CI/CD systems."""
    body = await request.json()
    # You can route based on headers or body
    return await analyze(AnalyzeRequest(
        source=request.url.path.split("/")[-1],
        logs=json.dumps(body, indent=2)
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)