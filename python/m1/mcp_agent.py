import sys
import asyncio
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import model
from deepagents import create_deep_agent
from deepagents_code.mcp_tools import get_mcp_tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

MCP_CONFIG = Path(__file__).resolve().parents[2] / ".mcp.json"


async def main():
    tools, session_manager, server_infos = await get_mcp_tools(str(MCP_CONFIG))

    for info in server_infos:
        print(f"{info.name}: {info.status} - {len(info.tools)} tool(s)")

    agent = create_deep_agent(
        model=model,
        tools=tools,
        interrupt_on={"search": True},
        checkpointer=MemorySaver(),
    )

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    await agent.ainvoke(
        {"messages": [{"role": "user", "content": "What is the LangGraph interrupt API?"}]},
        config=config,
    )

    state = agent.get_state(config)
    if state.interrupts:
        interrupt = state.interrupts[0].value
        for req in interrupt["action_requests"]:
            print(f"\nPending tool call: {req['name']}")
            print(f"  Input: {req.get('args', {})}")
        decision = input("\nApprove? (y/n): ")
        if decision.strip().lower() == "y":
            result = await agent.ainvoke(
                Command(resume={"decisions": [{"type": "approve"} for _ in interrupt["action_requests"]]}),
                config=config,
            )
            print(result["messages"][-1].content)
        else:
            print("Rejected.")

    if session_manager:
        await session_manager.cleanup()


asyncio.run(main())
