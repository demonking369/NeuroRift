"""
NeuroRift Python Adapter
Thin bridge between Rust core and Python tools/AI
"""

import os
import hmac
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import logging

# Import existing NeuroRift modules
from modules.ai.ai_integration import LocalAIClient, AIAnalyzer
from modules.orchestration.execution_manager import (
    ExecutionManager,
    ScanRequest,
    SessionContext,
)
from modules.darkweb.robin import runner as robin_runner
from modules.tools.base import ToolMode

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NeuroRift Python Bridge")

# --- Docker-aware configuration ---
# When running in Docker Compose, LLAMA_HOST is set to http://ollama:8080
LLAMA_HOST = os.environ.get("LLAMA_HOST", "http://localhost:8080")
BRIDGE_HOST = os.environ.get("BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", "8766"))

# Initialize components
llama = LocalAIClient(base_url=LLAMA_HOST)
ai_analyzer = AIAnalyzer(llama)
execution_manager = ExecutionManager()


class Command(BaseModel):
    """Generic command structure"""

    type: str
    data: Dict[str, Any] = {}


class Response(BaseModel):
    """Generic response structure"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.post("/execute", response_model=Response)
async def execute_command(command: Dict[str, Any]) -> Response:
    """
    Execute a command from Rust core

    Command types:
    - ai_generate: Generate AI response
    - tool_execute: Execute a security tool
    - robin_search: Dark web search via Robin
    - browser_action: Browser automation action
    """
    try:
        # Authentication: validate API token from request payload against server secret
        expected_token = os.environ.get("BRIDGE_API_KEY") or os.environ.get("EXECUTE_API_KEY")
        auth_token = command.get("api_key") or command.get("auth_token") or command.get("token")
        if not expected_token:
            logger.error("Authentication token not configured for /execute; refusing request")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        if not auth_token or not hmac.compare_digest(str(auth_token), str(expected_token)):
            raise HTTPException(status_code=401, detail="Unauthorized")
        # Remove auth material before further processing
        command.pop("api_key", None)
        command.pop("auth_token", None)
        command.pop("token", None)

        cmd_type = command.get("type")

        if cmd_type == "ai_generate":
            result = await handle_ai_generate(command)
        elif cmd_type == "tool_execute":
            result = await handle_tool_execute(command)
        elif cmd_type == "robin_search":
            result = await handle_robin_search(command)
        elif cmd_type == "browser_action":
            result = await handle_browser_action(command)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown command type: {cmd_type}"
            )

        return Response(success=True, data=result)

    except Exception as e:
        logger.error(f"Command execution failed: {e}", exc_info=True)
        return Response(success=False, error=str(e))


async def handle_ai_generate(command: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI response"""
    prompt = command.get("prompt", "")
    model = command.get("model")

    response = await llama.generate(prompt, model=model)

    return {
        "response": response,
        "model": model or llama.model,
    }


async def handle_tool_execute(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a security tool"""
    tool_name = command.get("tool", "")
    target = command.get("target", "")
    args = command.get("args", {})

    # Create scan request
    scan_request = ScanRequest(tool_name=tool_name, target=target, args=args)

    # Create minimal session context
    session_context = SessionContext(
        session_id="temp", mode=ToolMode.OFFENSIVE, history=[]  # TODO: Get from Rust
    )

    # Execute tool
    result = await execution_manager.execute_tool(scan_request, session_context)

    return {
        "tool_name": result.tool_name,
        "command": result.command,
        "status": result.status,
        "raw_output": result.raw_output,
        "structured_output": result.structured_output,
        "duration_seconds": result.duration_seconds,
        "error": result.error,
    }


async def handle_robin_search(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Robin dark web search"""
    query = command.get("query", "")

    # TODO: Integrate with Robin module
    # For now, return placeholder
    return {"query": query, "results": [], "message": "Robin integration pending"}


async def handle_browser_action(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute browser automation action"""
    action = command.get("action", "")
    params = command.get("params", {})

    # TODO: Integrate with browser automation
    # For now, return placeholder
    return {
        "action": action,
        "success": True,
        "message": "Browser automation integration pending",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "neurorift-python-bridge"}


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🐍 NeuroRift Python Bridge started")
    logger.info(f"📡 Listening on http://{BRIDGE_HOST}:{BRIDGE_PORT}")
    logger.info(f"🤖 llama.cpp endpoint: {LLAMA_HOST}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=BRIDGE_HOST, port=BRIDGE_PORT, log_level="info")
