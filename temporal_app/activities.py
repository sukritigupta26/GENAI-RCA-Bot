from temporalio import activity
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# Reuse your tools from before (or import them)
from app.tools.kubernetes import restart_kubernetes_pod, scale_deployment
from app.tools.jenkins import trigger_jenkins_job
# ... add ansible if needed

llm = ChatOpenAI(
    model="grok-beta",  # or gpt-4o
    base_url="https://api.x.ai/v1" if os.getenv("LLM_PROVIDER") == "xai" else None,
    api_key=os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
    temperature=0.1,
)

@activity.defn
async def llm_reasoning(messages: List[dict]) -> dict:
    """Call LLM with tool binding (non-deterministic)."""
    # Convert dicts back to LangChain messages
    lc_messages = []
    for m in messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m.get("content", "")))
        elif m["role"] == "tool":
            lc_messages.append(ToolMessage(content=m["content"], tool_call_id=m["tool_call_id"]))

    # Bind your tools (same as before)
    tools = [restart_kubernetes_pod, scale_deployment, trigger_jenkins_job]
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke(lc_messages)
    
    return {
        "content": response.content,
        "tool_calls": response.tool_calls if hasattr(response, "tool_calls") else []
    }

@activity.defn
async def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute any remediation tool safely."""
    if tool_name == "restart_kubernetes_pod":
        return restart_kubernetes_pod.invoke(tool_args)
    elif tool_name == "scale_deployment":
        return scale_deployment.invoke(tool_args)
    elif tool_name == "trigger_jenkins_job":
        return trigger_jenkins_job.invoke(tool_args)
    # Add more tools here
    return f"Unknown tool: {tool_name}"