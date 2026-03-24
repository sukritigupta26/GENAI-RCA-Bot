from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import Tool
import os
from dotenv import load_dotenv

load_dotenv()

# Use xAI Grok (OpenAI-compatible endpoint)
if os.getenv("LLM_PROVIDER") == "xai":
    llm = ChatOpenAI(
        model="grok-beta",
        base_url="https://api.x.ai/v1",
        api_key=os.getenv("XAI_API_KEY"),
        temperature=0.1
    )
else:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

# Import all tools
from .tools.kubernetes import restart_kubernetes_pod, create_kubernetes_pod, scale_deployment
from .tools.jenkins import trigger_jenkins_job
from .tools.ansible_tower import launch_ansible_tower_job

tools = [
    restart_kubernetes_pod,
    create_kubernetes_pod,
    scale_deployment,
    trigger_jenkins_job,
    launch_ansible_tower_job,
]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Simple ReAct graph
def agent_node(state):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": messages + [response]}

def should_continue(state):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

def tool_node(state):
    from langchain_core.messages import ToolMessage
    tool_calls = state["messages"][-1].tool_calls
    results = []
    for tc in tool_calls:
        tool = next(t for t in tools if t.name == tc["name"])
        result = tool.invoke(tc["args"])
        results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return {"messages": state["messages"] + results}

workflow = StateGraph(dict)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

rca_agent = workflow.compile()