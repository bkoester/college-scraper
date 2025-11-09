#!/usr/bin/env python3
"""
MCP (Model Context Protocol) SSE Client

Communicates with MCP server via Server-Sent Events (SSE) transport.
"""

import json
import logging
import requests
import sseclient
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for MCP server via SSE transport"""

    def __init__(self, base_url: str = "http://localhost:8931/sse", timeout: int = 60):
        """
        Initialize MCP client

        Args:
            base_url: MCP server SSE endpoint URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session_id = None

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize MCP session

        Returns:
            Server capabilities and info
        """
        try:
            # Send initialize request
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        }
                    },
                    "clientInfo": {
                        "name": "art-school-scraper",
                        "version": "1.0.0"
                    }
                }
            }

            response = self.session.post(
                self.base_url,
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"MCP session initialized: {result}")

            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }

            self.session.post(
                self.base_url,
                json=initialized_notification,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )

            return result

        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            raise

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")

            response = self.session.post(
                self.base_url,
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                error = result["error"]
                logger.error(f"MCP tool error: {error}")
                raise Exception(f"MCP error: {error.get('message', 'Unknown error')}")

            logger.info(f"MCP tool result: {result.get('result', {})}")
            return result.get("result")

        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {e}")
            raise

    def list_tools(self) -> list:
        """
        List available MCP tools

        Returns:
            List of available tools
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list"
            }

            response = self.session.post(
                self.base_url,
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            tools = result.get("result", {}).get("tools", [])

            logger.info(f"Available MCP tools: {[t['name'] for t in tools]}")
            return tools

        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            raise

    def close(self):
        """Close MCP session"""
        try:
            self.session.close()
            logger.info("MCP session closed")
        except Exception as e:
            logger.warning(f"Error closing MCP session: {e}")


def test_mcp_client():
    """Test MCP client connectivity and tools"""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=" * 60)
    print("Testing MCP Client")
    print("=" * 60)
    print()

    try:
        # Create client
        print("1. Creating MCP client...")
        client = MCPClient()
        print("   ✓ Client created")
        print()

        # Initialize
        print("2. Initializing MCP session...")
        init_result = client.initialize()
        print(f"   ✓ Session initialized")
        print(f"   Server: {init_result.get('serverInfo', {}).get('name', 'Unknown')}")
        print()

        # List tools
        print("3. Listing available tools...")
        tools = client.list_tools()
        print(f"   ✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"     - {tool['name']}: {tool.get('description', 'No description')}")
        print()

        # Test browser_navigate if available
        if any(t['name'] == 'browser_navigate' for t in tools):
            print("4. Testing browser_navigate...")
            result = client.call_tool(
                "browser_navigate",
                {"url": "https://example.com"}
            )
            print(f"   ✓ Navigation successful")
            print(f"   Result: {result}")
        else:
            print("4. browser_navigate tool not available")

        print()
        print("=" * 60)
        print("MCP Client Test Complete!")
        print("=" * 60)

        client.close()
        return True

    except Exception as e:
        print()
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure MCP server is running:")
        print("   docker-compose up -d mcp-server")
        print()
        print("2. Check MCP server logs:")
        print("   docker-compose logs mcp-server")
        print()
        print("3. Verify endpoint is accessible:")
        print("   curl http://localhost:8931/sse")
        print()
        return False


if __name__ == "__main__":
    import sys
    success = test_mcp_client()
    sys.exit(0 if success else 1)
