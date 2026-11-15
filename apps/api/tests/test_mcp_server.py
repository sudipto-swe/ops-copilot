import pytest

from apps.api.app.mcp_server.server import MCPServer


@pytest.fixture
def mcp():
    return MCPServer()

@pytest.mark.asyncio
async def test_mcp_list_tools(mcp):
    tools = mcp.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "list_services" in tool_names
    assert "get_service_status" in tool_names
    assert "get_logs" in tool_names
    assert "query_metrics" in tool_names

@pytest.mark.asyncio
async def test_mcp_list_services(mcp):
    res = await mcp.call_tool("list_services", {})
    assert "services" in res
    assert len(res["services"]) == 3

@pytest.mark.asyncio
async def test_mcp_get_service_status(mcp):
    res = await mcp.call_tool("get_service_status", {"service": "gateway"})
    assert "service" in res
    assert res["service"] == "gateway"

@pytest.mark.asyncio
async def test_mcp_get_logs_with_redaction(mcp, tmp_path):
    # Test secret redaction
    log_content = '{"message": "User login token=supersecret123 Authorization: Bearer eyJhbGciOiJIUzI1NiJ9"}\n'
    test_log = tmp_path / "gateway.log"
    test_log.write_text(log_content)

    # Monkeypatch log path
    from apps.api.app.mcp_server import server
    server.LOG_PATHS["gateway"] = str(test_log)

    res = await mcp.call_tool("get_logs", {"service": "gateway", "lines": 5})
    assert len(res["lines"]) == 1
    assert "supersecret123" not in res["lines"][0]
    assert "BEARER [REDACTED]" in res["lines"][0]

@pytest.mark.asyncio
async def test_mcp_query_metrics(mcp):
    res = await mcp.call_tool("query_metrics", {"metric_template": "http_requests_total", "service": "gateway"})
    assert "service" in res
    assert res["service"] == "gateway"
