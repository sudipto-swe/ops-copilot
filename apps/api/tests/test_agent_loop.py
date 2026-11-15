import pytest

from apps.api.app.agent.ops_agent import OpsAgent
from apps.api.app.llm.client import LLMResponse, MockLLMClient
from apps.api.app.mcp_server.server import MCPServer


@pytest.mark.asyncio
async def test_agent_loop_with_mock_llm():
    mock_llm = MockLLMClient()
    mcp = MCPServer()
    agent = OpsAgent(llm_client=mock_llm, mcp_server=mcp, max_steps=5)

    alert = "Gateway returning HTTP 500 on health checks"
    result = await agent.investigate(alert)

    assert "report" in result
    assert "scratchpad" in result
    report = result["report"]
    assert report["target_service"] == "gateway"
    assert report["recommended_action"] == "restart"
    assert len(result["scratchpad"]) >= 3

@pytest.mark.asyncio
async def test_agent_loop_detection():
    # Force mock to repeat identical tool call
    repeated_response = LLMResponse(
        content="Repeating status check",
        tool_calls=[{"name": "get_service_status", "arguments": {"service": "gateway"}}]
    )
    mock_llm = MockLLMClient(scripted_responses=[repeated_response, repeated_response, repeated_response])
    mcp = MCPServer()
    agent = OpsAgent(llm_client=mock_llm, mcp_server=mcp, max_steps=5)

    result = await agent.investigate("Loop test alert")
    assert len(result["scratchpad"]) <= 3
