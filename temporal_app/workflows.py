from temporalio import workflow
from datetime import timedelta
from typing import List
import json

from .activities import llm_reasoning, execute_tool
from .shared import RCAInput, RCAResult, AgentMessage

@workflow.defn
class RCAAgentWorkflow:
    @workflow.run
    async def run(self, input_data: RCAInput) -> RCAResult:
        messages: List[dict] = [{
            "role": "user",
            "content": f"""
Source: {input_data.source}
Logs:
{input_data.logs}
Context: {json.dumps(input_data.context)}
Task: Perform root cause analysis and autonomously remediate the DevOps/SRE issue if possible.
            """
        }]

        actions_taken = []
        MAX_STEPS = 12

        for step in range(MAX_STEPS):
            # 1. LLM Reasoning (as Activity)
            llm_response = await workflow.execute_activity(
                llm_reasoning,
                messages,
                start_to_close_timeout=timedelta(seconds=30),
            )

            ai_content = llm_response["content"]
            tool_calls = llm_response.get("tool_calls", [])

            messages.append({"role": "assistant", "content": ai_content})

            if not tool_calls:
                # Agent decided to finish
                final_summary = ai_content
                break

            # 2. Execute tools (one by one)
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]

                result = await workflow.execute_activity(
                    execute_tool,
                    args=[tool_name, tool_args],
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=workflow.RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=10),
                    ),
                )

                actions_taken.append(f"{tool_name} → {result}")
                messages.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tc.get("id", "1")
                })

            # Optional: Check if we should continue_as_new for very long RCAs
            if workflow.upsert_search_attributes({"RCA_Step": [step]}):
                pass  # You can add continue_as_new logic here if needed

        else:
            final_summary = "Max steps reached. Manual intervention recommended."

        return RCAResult(
            rca_summary=final_summary,
            actions_taken=actions_taken,
            status="resolved" if "✅" in final_summary or len(actions_taken) > 0 else "needs_human"
        )