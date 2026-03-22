"""NeuroRift Web Mode V3 — FastAPI Backend

WebSocket-first architecture powering the dashboard.
All panels receive real-time data via WebSocket channels.
REST endpoints for actions (scan control, file upload, config).
"""

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

logger = logging.getLogger("neurorift.webapi")

# ─── Project Paths ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
REPORTS_DIR = PROJECT_ROOT / "reports"
SCOPE_DIR = PROJECT_ROOT / "scopes"

# ─── App ──────────────────────────────────────────────────────────
app = FastAPI(title="NeuroRift WebAPI", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
#  WebSocket Connection Manager
# ═══════════════════════════════════════════════════════════════════


class ConnectionManager:
    """Manages WebSocket connections and broadcasts to all clients."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info("WebSocket client connected (%d total)", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(self.active_connections))

    async def broadcast(self, channel: str, data: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        message = json.dumps({"channel": channel, "data": data, "ts": time.time()})
        dead: List[WebSocket] = []
        async with self._lock:
            connections = list(self.active_connections)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════════
#  Pipeline State (in-memory, fed by NeuroRift engine)
# ═══════════════════════════════════════════════════════════════════


class PipelineState:
    """Tracks the current state of the scan pipeline."""

    def __init__(self):
        self.status: str = "idle"  # idle | running | stopped | error
        self.stage: str = ""  # recon | planning | executing | reporting
        self.target: str = ""
        self.scope_file: str = ""
        self.started_at: Optional[float] = None
        self.findings: List[Dict[str, Any]] = []
        self.scan_log: List[Dict[str, Any]] = []  # Live terminal entries
        self.neurocore: Dict[str, Any] = {
            "loaded_model": None,
            "active_role": None,
            "vram_used_mb": 0,
            "vram_total_mb": 4096,
            "models": {},
        }
        self.notifications: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "stage": self.stage,
            "target": self.target,
            "scope_file": self.scope_file,
            "started_at": self.started_at,
            "finding_count": len(self.findings),
        }


pipeline = PipelineState()


# ═══════════════════════════════════════════════════════════════════
#  Broadcast Helpers (called by NeuroRift engine hooks)
# ═══════════════════════════════════════════════════════════════════


async def broadcast_pipeline_state():
    """Push current pipeline state to all clients."""
    await manager.broadcast("pipeline_state", pipeline.to_dict())


async def broadcast_neurocore_status():
    """Push NeuroCore model/VRAM status to all clients."""
    await manager.broadcast("neurocore_status", pipeline.neurocore)


async def broadcast_finding(finding: Dict[str, Any]):
    """Push a new finding to all clients."""
    pipeline.findings.append(finding)
    await manager.broadcast("finding", finding)


async def broadcast_scan_log(entry: Dict[str, Any]):
    """Push a live scan terminal entry (agent reasoning, tool call, model decision)."""
    entry.setdefault("ts", time.time())
    entry.setdefault("id", str(uuid.uuid4())[:8])
    pipeline.scan_log.append(entry)
    # Keep only last 500 entries in memory
    if len(pipeline.scan_log) > 500:
        pipeline.scan_log = pipeline.scan_log[-500:]
    await manager.broadcast("scan_terminal", entry)


async def broadcast_notification(event: Dict[str, Any]):
    """Push a notification event to the feed."""
    event.setdefault("ts", time.time())
    pipeline.notifications.append(event)
    if len(pipeline.notifications) > 200:
        pipeline.notifications = pipeline.notifications[-200:]
    await manager.broadcast("notification_feed", event)


# ═══════════════════════════════════════════════════════════════════
#  WebSocket Endpoint
# ═══════════════════════════════════════════════════════════════════


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Send initial state snapshot on connect
    try:
        await websocket.send_text(json.dumps({
            "channel": "initial_state",
            "data": {
                "pipeline": pipeline.to_dict(),
                "neurocore": pipeline.neurocore,
                "findings": pipeline.findings,
                "scan_log": pipeline.scan_log[-50:],
                "notifications": pipeline.notifications[-50:],
            },
            "ts": time.time(),
        }))

        # Keep alive — listen for client messages (pings, commands)
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"channel": "pong", "data": {}, "ts": time.time()}))

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        await manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════
#  REST — Scan Control
# ═══════════════════════════════════════════════════════════════════


@app.post("/api/scan/start")
async def scan_start(body: Dict[str, Any] = {}):
    """Start a new scan."""
    if pipeline.status == "running":
        raise HTTPException(400, "Scan already running")

    pipeline.status = "running"
    pipeline.stage = "initializing"
    pipeline.target = body.get("target", "")
    pipeline.scope_file = body.get("scope_file", "")
    pipeline.started_at = time.time()
    pipeline.findings = []
    pipeline.scan_log = []

    await broadcast_pipeline_state()
    await broadcast_scan_log({
        "type": "system",
        "message": f"Scan started for target: {pipeline.target}",
        "severity": "info",
    })

    return {"status": "started", "target": pipeline.target}


@app.post("/api/scan/stop")
async def scan_stop():
    """Stop the current scan."""
    if pipeline.status != "running":
        raise HTTPException(400, "No scan running")

    pipeline.status = "stopped"
    pipeline.stage = ""
    await broadcast_pipeline_state()
    await broadcast_scan_log({
        "type": "system",
        "message": "Scan stopped by user",
        "severity": "warning",
    })
    return {"status": "stopped"}


@app.get("/api/scan/status")
async def scan_status():
    """Get current scan status."""
    return pipeline.to_dict()


# ═══════════════════════════════════════════════════════════════════
#  REST — Scope File Upload
# ═══════════════════════════════════════════════════════════════════


@app.post("/api/scope/upload")
async def scope_upload(file: UploadFile = File(...)):
    """Upload a scope file."""
    SCOPE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"scope_{int(time.time())}_{file.filename}"
    dest = SCOPE_DIR / filename
    content = await file.read()
    dest.write_bytes(content)

    line_count = content.decode("utf-8", errors="replace").count("\n") + 1
    return {
        "filename": filename,
        "path": str(dest),
        "size_bytes": len(content),
        "line_count": line_count,
    }


# ═══════════════════════════════════════════════════════════════════
#  REST — Reports
# ═══════════════════════════════════════════════════════════════════


@app.get("/api/reports")
async def list_reports():
    """List generated reports."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for f in sorted(REPORTS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.is_file():
            stat = f.stat()
            reports.append({
                "name": f.name,
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
            })
    return {"reports": reports}


@app.get("/api/reports/{name}")
async def download_report(name: str):
    """Download a specific report."""
    path = REPORTS_DIR / name
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Report not found")
    # Prevent path traversal
    if not path.resolve().is_relative_to(REPORTS_DIR.resolve()):
        raise HTTPException(403, "Access denied")
    return FileResponse(path, filename=name)


# ═══════════════════════════════════════════════════════════════════
#  REST — Config Management
# ═══════════════════════════════════════════════════════════════════


ALLOWED_CONFIGS = {"models", "notifications"}


@app.get("/api/config/{name}")
async def get_config(name: str):
    """Read a config file (models.yaml or notifications.yaml)."""
    if name not in ALLOWED_CONFIGS:
        raise HTTPException(400, f"Unknown config: {name}. Allowed: {ALLOWED_CONFIGS}")
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        return {"name": name, "content": "", "exists": False}
    return {"name": name, "content": path.read_text(), "exists": True}


@app.put("/api/config/{name}")
async def update_config(name: str, body: Dict[str, Any]):
    """Write a config file."""
    if name not in ALLOWED_CONFIGS:
        raise HTTPException(400, f"Unknown config: {name}")

    content = body.get("content", "")
    # Validate YAML syntax
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(422, f"Invalid YAML: {e}")

    path = CONFIG_DIR / f"{name}.yaml"
    path.write_text(content)
    return {"name": name, "saved": True}


# ═══════════════════════════════════════════════════════════════════
#  REST — Findings (for initial load)
# ═══════════════════════════════════════════════════════════════════


@app.get("/api/findings")
async def get_findings():
    """Get all findings from current/last scan."""
    return {"findings": pipeline.findings, "count": len(pipeline.findings)}


# ═══════════════════════════════════════════════════════════════════
#  REST — NeuroCore Control
# ═══════════════════════════════════════════════════════════════════


@app.get("/api/neurocore/status")
async def neurocore_status():
    """Get NeuroCore model status."""
    return pipeline.neurocore


@app.post("/api/neurocore/load")
async def neurocore_load(body: Dict[str, Any]):
    """Load a model by role."""
    role = body.get("role", "")
    if not role:
        raise HTTPException(400, "Role required")
    # In production, this calls neurocore.load_model(role)
    pipeline.neurocore["loaded_model"] = role
    pipeline.neurocore["active_role"] = role
    await broadcast_neurocore_status()
    await broadcast_scan_log({
        "type": "model",
        "message": f"Model loaded for role: {role}",
        "severity": "info",
    })
    return {"loaded": role}


@app.post("/api/neurocore/unload")
async def neurocore_unload():
    """Unload current model."""
    prev = pipeline.neurocore.get("loaded_model")
    pipeline.neurocore["loaded_model"] = None
    pipeline.neurocore["active_role"] = None
    pipeline.neurocore["vram_used_mb"] = 0
    await broadcast_neurocore_status()
    await broadcast_scan_log({
        "type": "model",
        "message": f"Model unloaded: {prev}",
        "severity": "info",
    })
    return {"unloaded": prev}


# ═══════════════════════════════════════════════════════════════════
#  REST — Notification Control
# ═══════════════════════════════════════════════════════════════════


@app.post("/api/notifications/test")
async def notification_test(body: Dict[str, Any]):
    """Send a test notification to a channel."""
    channel = body.get("channel", "")
    if not channel:
        raise HTTPException(400, "Channel required")

    event = {
        "type": "test",
        "channel": channel,
        "message": "Test notification from NeuroRift dashboard",
        "status": "sent",
    }
    await broadcast_notification(event)
    return event


@app.post("/api/notifications/toggle")
async def notification_toggle(body: Dict[str, Any]):
    """Toggle a notification channel on/off."""
    channel = body.get("channel", "")
    enabled = body.get("enabled", True)

    path = CONFIG_DIR / "notifications.yaml"
    if not path.exists():
        raise HTTPException(404, "notifications.yaml not found")

    config = yaml.safe_load(path.read_text()) or {}
    notif = config.setdefault("notifications", {})
    channels = notif.setdefault("channels", {})
    ch = channels.setdefault(channel, {})
    ch["enabled"] = enabled

    path.write_text(yaml.dump(config, default_flow_style=False))
    return {"channel": channel, "enabled": enabled}


# ═══════════════════════════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════════════════════════


@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "3.0.0",
        "connections": len(manager.active_connections),
        "pipeline": pipeline.status,
    }


# ═══════════════════════════════════════════════════════════════════
#  Run Server
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
