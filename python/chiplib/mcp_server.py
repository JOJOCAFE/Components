"""MCP (Model Context Protocol) server for the Components Board.

Exposes Components engine operations as MCP tools over stdio transport.
Allows AI assistants (Kiro, Claude) to interact with the Board in real-time:
place chips, connect wires, run simulations, probe results.

Protocol: JSON-RPC 2.0 over stdio (newline-delimited JSON).
Spec: https://modelcontextprotocol.io/

Usage (standalone — own engine instance):
    python3 -B -m chiplib.mcp_server

Usage (shared with Board — forwards to HTTP API):
    python3 -B -m chiplib.mcp_server --api http://127.0.0.1:8765

When --api is given, the MCP server forwards tool calls to the running
HTTP API, which is the same instance the Board connects to. This means
AI actions appear on the Board in real-time.

Kiro MCP config (.kiro/settings/mcp.json):
    {
      "mcpServers": {
        "components-board": {
          "command": "python3",
          "args": ["-B", "-m", "chiplib.mcp_server", "--api", "http://127.0.0.1:8765"],
          "cwd": "/home/jo/kiro/Components/python"
        }
      }
    }
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .api import handle_request
from .services import FrontendDesignService, CircuitCommandService, CircuitSessionRegistry


# =============================================================================
# MCP TOOL DEFINITIONS
# =============================================================================

TOOLS = [
    {
        "name": "component_parse",
        "description": "Parse component:component source text into an AST. Use this to check syntax before resolving.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Component source text (component:component language)"}
            },
            "required": ["source"]
        }
    },
    {
        "name": "component_resolve",
        "description": "Parse and resolve component source into a topology (instances, nets, edges, tests). Shows what chips and connections exist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Component source text"}
            },
            "required": ["source"]
        }
    },
    {
        "name": "component_run",
        "description": "Parse, resolve, and run a component circuit. Optionally drive inputs and read probe values. Returns simulation state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Component source text"},
                "drives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string"},
                            "value": {}
                        }
                    },
                    "description": "List of {target, value} to drive before probing"
                },
                "test": {"type": "string", "description": "Name of a declared test to run"},
                "probe": {"type": "string", "description": "Name of a specific probe to read (omit for all)"}
            },
            "required": ["source"]
        }
    },
    {
        "name": "component_board_view",
        "description": "Get the Board rendering data for a component (device positions, pin info, connections). Used to understand visual layout.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Component source text"}
            },
            "required": ["source"]
        }
    },
    {
        "name": "component_edit",
        "description": "Apply a source edit to component text. Returns the modified source. Edits: add_device, add_net, add_connection, remove_connection, add_test, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Current component source text"},
                "edit": {
                    "type": "object",
                    "description": "Edit operation: {kind, ...params}. Kinds: add_device, add_net, add_bus, add_connection, remove_connection, add_probe, add_test",
                    "properties": {
                        "kind": {"type": "string"},
                        "device": {"type": "string"},
                        "part": {"type": "string"},
                        "library": {"type": "string"},
                        "net": {"type": "string"},
                        "bus": {"type": "string"},
                        "width": {"type": "integer"},
                        "from": {"type": "string"},
                        "to": {"type": "string"},
                        "name": {"type": "string"},
                        "target": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["kind"]
                }
            },
            "required": ["source", "edit"]
        }
    },
    {
        "name": "component_catalog",
        "description": "List available components from the library. Shows chip names, descriptions, pin counts. Use to find parts for a circuit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter": {"type": "string", "description": "Optional filter (e.g. '74HC', 'memory', 'counter')"}
            }
        }
    },
    {
        "name": "component_detail",
        "description": "Get detailed information about a specific component: pins, behavior, timing, package.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "part": {"type": "string", "description": "Part name (e.g. '74HC04', '74HC574', 'AT28C256')"}
            },
            "required": ["part"]
        }
    },
    {
        "name": "circuit_validate",
        "description": "Validate a circuit for bus conflicts, floating pins, and timing issues. Returns pass/fail with diagnostics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Component source text"}
            },
            "required": ["source"]
        }
    },
    {
        "name": "circuit_probe",
        "description": "Quick probe: parse+resolve+instantiate a circuit and read all observable values without running tests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Component source text"},
                "drives": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"target": {"type": "string"}, "value": {}}},
                    "description": "Drive signals before probing"
                }
            },
            "required": ["source"]
        }
    },
]


# =============================================================================
# MCP PROTOCOL HANDLER
# =============================================================================

class MCPServer:
    """Minimal MCP server over stdio (JSON-RPC 2.0)."""

    def __init__(self, api_url: str | None = None):
        self.api_url = api_url
        if not api_url:
            self.service = FrontendDesignService()
            self.circuit_service = CircuitCommandService()
            self.sessions = CircuitSessionRegistry()
        else:
            self.service = None
            self.circuit_service = None
            self.sessions = None

    def handle_message(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a single JSON-RPC 2.0 message. Returns response or None for notifications."""
        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg.get("id")

        # Notifications (no id) — no response needed
        if msg_id is None:
            return None

        if method == "initialize":
            return self._respond(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "components-board",
                    "version": "1.0.0"
                }
            })

        if method == "tools/list":
            return self._respond(msg_id, {"tools": TOOLS})

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                result = self._call_tool(tool_name, arguments)
                return self._respond(msg_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
                })
            except Exception as e:
                return self._respond(msg_id, {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True
                })

        if method == "ping":
            return self._respond(msg_id, {})

        # Unknown method
        return {"jsonrpc": "2.0", "id": msg_id, "error": {
            "code": -32601, "message": f"Method not found: {method}"
        }}

    def _respond(self, msg_id: Any, result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _call_tool(self, name: str, args: dict[str, Any]) -> Any:
        """Dispatch MCP tool call to chiplib API (local or HTTP forwarded)."""

        # Build the request for the chiplib API
        req = self._build_api_request(name, args)
        if req is None:
            raise ValueError(f"Unknown tool: {name}")

        # Forward to HTTP API if configured, otherwise handle locally
        if self.api_url:
            return self._http_forward(req)
        return handle_request(req, self.service, self.circuit_service)

    def _http_forward(self, request: dict[str, Any]) -> Any:
        """Forward a request to the running HTTP API."""
        import urllib.request
        import urllib.error
        data = json.dumps(request).encode()
        req = urllib.request.Request(
            f"{self.api_url}/api",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot reach Board API at {self.api_url}: {e}") from e

    def _build_api_request(self, name: str, args: dict[str, Any]) -> dict[str, Any] | None:
        """Map MCP tool name + args to a chiplib API request."""

        if name == "component_parse":
            return {"command": "component-language-parse", "input": {"source": args["source"]}}

        if name == "component_resolve":
            return {"command": "component-language-resolve", "input": {"source": args["source"]}}

        if name == "component_run":
            req: dict[str, Any] = {"command": "component-language-run", "input": {"source": args["source"]}}
            if "drives" in args:
                req["input"]["drives"] = args["drives"]
            if "test" in args:
                req["options"] = {"test": args["test"]}
            if "probe" in args:
                req.setdefault("options", {})["probe"] = args["probe"]
            return req

        if name == "component_board_view":
            return {"command": "component-language-board-view", "input": {"source": args["source"]}}

        if name == "component_edit":
            return {"command": "component-language-edit",
                    "input": {"source": args["source"], "edit": args["edit"]}}

        if name == "component_catalog":
            req = {"command": "student-component-catalog", "input": {}}
            if "filter" in args:
                req["input"]["filter"] = args["filter"]
            return req

        if name == "component_detail":
            return {"command": "component-detail", "input": {"part": args["part"]}}

        if name == "circuit_validate":
            return {"command": "component-language-resolve", "input": {"source": args["source"]}}

        if name == "circuit_probe":
            req = {"command": "component-language-run", "input": {"source": args["source"]}}
            if "drives" in args:
                req["input"]["drives"] = args["drives"]
            return req

        return None


# =============================================================================
# STDIO TRANSPORT
# =============================================================================

def run_mcp_stdio() -> int:
    """Run MCP server on stdio (newline-delimited JSON-RPC 2.0)."""
    import argparse
    parser = argparse.ArgumentParser(description="Components Board MCP server")
    parser.add_argument("--api", type=str, default=None,
                        help="Forward to HTTP API (e.g. http://127.0.0.1:8765)")
    args = parser.parse_args()

    server = MCPServer(api_url=args.api)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stderr.write(f"MCP: invalid JSON: {line[:100]}\n")
            continue

        response = server.handle_message(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

    return 0


if __name__ == "__main__":
    sys.exit(run_mcp_stdio())
