import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from .workflows import RCAAgentWorkflow
from .activities import llm_reasoning, execute_tool

async def main():
    client = await Client.connect("localhost:7233")  # or Temporal Cloud endpoint

    worker = Worker(
        client,
        task_queue="rca-agent-task-queue",
        workflows=[RCAAgentWorkflow],
        activities=[llm_reasoning, execute_tool],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())