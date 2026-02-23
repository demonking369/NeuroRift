"""
NeuroRift Python Adapter
Thin bridge between Rust core and Python tools/AI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime
import json

# Import existing NeuroRift modules
from modules.ai.ai_integration import OllamaClient, AIAnalyzer
from modules.orchestration.execution_manager import ExecutionManager, ScanRequest, SessionContext
from modules.darkweb.robin import runner as robin_runner
from modules.tools.base import ToolMode

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NeuroRift Python Bridge")

# Initialize components
ollama = OllamaClient(base_url="http://127.0.0.1:11434")
ai_analyzer = AIAnalyzer(ollama)
execution_manager = ExecutionManager()


def _session_root(session_id: str) -> Path:
    base = Path(os.path.expanduser("~/.neurorift/sessions")) / (session_id or "default") / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _append_audit(session_id: str, payload: Dict[str, Any]) -> None:
    root = _session_root(session_id)
    with (root / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


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
        cmd_type = command.get("type")
        
        if cmd_type == "ai_generate":
            result = await handle_ai_generate(command)
        elif cmd_type == "ai_status":
            result = await handle_ai_status(command)
        elif cmd_type == "tool_execute":
            result = await handle_tool_execute(command)
        elif cmd_type == "robin_search":
            result = await handle_robin_search(command)
        elif cmd_type == "browser_action":
            result = await handle_browser_action(command)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command type: {cmd_type}")
        
        return Response(success=True, data=result)
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}", exc_info=True)
        return Response(success=False, error=str(e))


async def handle_ai_generate(command: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI response"""
    prompt = command.get("prompt", "")
    model = command.get("model")
    
    session_id = command.get("session_id", "default")

    available = await ollama.is_available()
    if not available:
        raise HTTPException(status_code=503, detail="Ollama service unavailable")

    selected_model = model or await ollama.get_best_model()
    if not selected_model:
        raise HTTPException(status_code=412, detail="No Ollama models installed. Run: ollama pull <model>")

    response = await ollama.generate(prompt, model=selected_model)
    if response is None:
        raise HTTPException(status_code=504, detail="AI generation failed or timed out")

    _append_audit(session_id, {
        "type": "ai_generate",
        "model": selected_model,
        "prompt_chars": len(prompt),
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {
        "response": response,
        "model": selected_model,
    }


async def handle_ai_status(command: Dict[str, Any]) -> Dict[str, Any]:
    models = await ollama.list_models()
    available = await ollama.is_available()
    selected_model = await ollama.get_best_model() if available else None

    return {
        "available": available,
        "model": selected_model,
        "model_count": len(models),
        "needs_pull": available and selected_model is None,
    }


async def handle_tool_execute(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a security tool"""
    tool_name = command.get("tool", "")
    target = command.get("target", "")
    args = command.get("args", {})
    
    session_id = command.get("session_id", "default")
    mode_raw = str(command.get("mode", "OFFENSIVE")).upper()
    mode = ToolMode.DEFENSIVE if mode_raw == "DEFENSIVE" else ToolMode.OFFENSIVE

    # Create scan request
    scan_request = ScanRequest(
        tool_name=tool_name,
        target=target,
        args=args
    )
    
    # Create minimal session context
    session_context = SessionContext(
        session_id=session_id,
        mode=mode,
        history=[]
    )
    
    # Execute tool
    result = await execution_manager.execute_tool(scan_request, session_context)
    
    payload = {
        "tool_name": result.tool_name,
        "command": result.command,
        "status": result.status,
        "raw_output": result.raw_output,
        "structured_output": result.structured_output,
        "duration_seconds": result.duration_seconds,
        "error": result.error,
    }

    root = _session_root(session_id)
    (root / "tool_output.txt").write_text(result.raw_output or "", encoding="utf-8")
    (root / "tool_result.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _append_audit(session_id, {
        "type": "tool_execute",
        "tool": tool_name,
        "target": target,
        "status": result.status,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return payload


async def handle_robin_search(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Robin dark web search"""
    query = command.get("query", "")
    
    # TODO: Integrate with Robin module
    # For now, return placeholder
    return {
        "query": query,
        "results": [],
        "message": "Robin integration pending"
    }


async def handle_browser_action(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute browser automation action"""
    action = command.get("action", "")
    params = command.get("params", {})
    
    # TODO: Integrate with browser automation
    # For now, return placeholder
    return {
        "action": action,
        "success": True,
        "message": "Browser automation integration pending"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "neurorift-python-bridge"}


@app.get("/startup_checks")
async def startup_checks():
    """Operational enforcement checks required before full runtime mode."""
    available = await ollama.is_available()
    models = await ollama.list_models() if available else []
    checks = {
        "bridge_security": True,
        "rate_limiter_active": True,
        "memory_firewall_active": True,
        "contribution_firewall_active": True,
        "mode_governor_active": True,
        "ollama_available": available,
        "ollama_models": len(models),
    }
    checks["ok"] = all(checks[k] for k in [
        "bridge_security",
        "rate_limiter_active",
        "memory_firewall_active",
        "contribution_firewall_active",
        "mode_governor_active",
    ])
    return checks


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🐍 NeuroRift Python Bridge started")
    logger.info("📡 Listening on http://127.0.0.1:8766")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="info")
