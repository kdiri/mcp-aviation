#!/usr/bin/env python3
"""Standalone MCP Server for Emergency Airport Finder."""

import asyncio
import json
import sys
import logging
from typing import Any, Dict

from src.data.database import DatabaseManager
from src.data.airport_fetcher import AirportDataFetcher
from src.mcp.server import MCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServerApp:
    """MCP Server application for stdio communication."""
    
    def __init__(self):
        """Initialize MCP server application."""
        self.db_manager = None
        self.mcp_server = None
    
    async def initialize(self):
        """Initialize database and MCP server."""
        logger.info("Initializing Emergency Airport Finder MCP Server...")
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Initialize data if needed
        data_fetcher = AirportDataFetcher(self.db_manager)
        data_fetcher.initialize_system_data()
        
        # Create MCP server
        self.mcp_server = MCPServer(self.db_manager)
        
        logger.info("MCP Server initialized successfully")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                # Return available tools
                tools_manifest = self.mcp_server.get_tools_manifest()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": tools_manifest
                }
            
            elif method == "tools/call":
                # Handle tool call
                tool_name = params.get("name")
                tool_arguments = params.get("arguments", {})
                
                result = await self.mcp_server.handle_tool_call(tool_name, tool_arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def run(self):
        """Run MCP server with stdio communication."""
        await self.initialize()
        
        logger.info("MCP Server ready for requests")
        
        # Read requests from stdin and write responses to stdout
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # Write response to stdout
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON request: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except KeyboardInterrupt:
                logger.info("Shutting down MCP server...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        # Cleanup
        if self.db_manager:
            self.db_manager.close()


async def main():
    """Main entry point."""
    server = MCPServerApp()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())