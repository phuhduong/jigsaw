"""
Component search via the DigiKey MCP server.
"""

import os
import json
import requests

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")

# MCP session ID cached for reuse across calls
_mcp_session_id: str | None = None


def _reset_session() -> None:
    """Clear the cached MCP session so the next call re-initializes."""
    global _mcp_session_id
    _mcp_session_id = None


def _init_mcp_session() -> str:
    """Initialize an MCP session and return the session ID."""
    global _mcp_session_id
    if _mcp_session_id:
        return _mcp_session_id

    # Send an initialize request to create a session
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "jigsaw-backend", "version": "0.1.0"},
        },
    }

    resp = requests.post(
        f"{MCP_SERVER_URL}/mcp",
        json=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        timeout=10,
    )
    resp.raise_for_status()

    session_id = resp.headers.get("mcp-session-id")
    if session_id:
        _mcp_session_id = session_id

    # Send initialized notification
    notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }
    requests.post(
        f"{MCP_SERVER_URL}/mcp",
        json=notif,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **({"mcp-session-id": _mcp_session_id} if _mcp_session_id else {}),
        },
        timeout=10,
    )

    return _mcp_session_id or ""


def _parse_mcp_response(resp: requests.Response) -> list[dict]:
    """Extract component list from an MCP JSON-RPC or SSE response."""
    body = resp.text.strip()

    # Handle SSE format: lines starting with "event:" and "data:"
    if body.startswith("event:"):
        for line in body.split("\n"):
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if data_str:
                    data = json.loads(data_str)
                    if "result" in data:
                        content = data["result"].get("content", [])
                        for item in content:
                            if item.get("type") == "text":
                                return json.loads(item["text"])
        return []

    # Handle plain JSON response
    data = json.loads(body)
    if "result" in data:
        content = data["result"].get("content", [])
        for item in content:
            if item.get("type") == "text":
                return json.loads(item["text"])

    return []


def _do_search(search_query: str) -> list[dict]:
    """Execute a single search call against the MCP server."""
    session_id = _init_mcp_session()

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "search_components",
            "arguments": {
                "query": search_query,
                "limit": 5,
            },
        },
    }

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["mcp-session-id"] = session_id

    resp = requests.post(
        f"{MCP_SERVER_URL}/mcp",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return _parse_mcp_response(resp)


def search_components(query: str, specifications: dict | None = None) -> list[dict]:
    """
    Search for components by calling the DigiKey MCP server.
    Retries once with a fresh session on failure.
    """
    search_query = query
    if specifications:
        spec_parts = [f"{v}" for v in specifications.values() if v]
        if spec_parts:
            search_query += " " + " ".join(spec_parts)

    for attempt in range(2):
        try:
            return _do_search(search_query)
        except Exception as e:
            print(f"MCP server error (attempt {attempt + 1}): {e}")
            if attempt == 0:
                _reset_session()
            else:
                return [
                    {
                        "mpn": "ERROR",
                        "manufacturer": "N/A",
                        "description": f"Component search unavailable: {str(e)}",
                        "price": 0,
                        "currency": "USD",
                        "quantity": 0,
                    }
                ]
    return []
