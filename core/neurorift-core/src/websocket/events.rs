use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use crate::state::*;

/// WebSocket event protocol
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum WSEvent {
    // Session events
    SessionCreated {
        session_id: String,
        name: String,
    },
    SessionLoaded {
        session_id: String,
        state: SessionState,
    },
    SessionUpdated {
        session_id: String,
        delta: SessionDelta,
    },
    SessionSaved {
        session_id: String,
        timestamp: DateTime<Utc>,
    },
    SessionDeleted {
        session_id: String,
    },
    SessionList {
        sessions: Vec<crate::session::SessionMetadata>,
    },
    
    // Agent events
    AgentStatusChanged {
        agent: AgentType,
        status: AgentStatus,
    },
    PlanGenerated {
        plan: Vec<ScanRequest>,
    },
    
    // Task events
    TaskQueued {
        task: Task,
    },
    TaskStarted {
        task_id: String,
        started_at: DateTime<Utc>,
    },
    TaskProgress {
        task_id: String,
        progress: f32,
        message: Option<String>,
    },
    TaskCompleted {
        task_id: String,
        result: TaskResult,
    },
    TaskFailed {
        task_id: String,
        error: String,
    },
    TaskOutput {
        task_id: String,
        chunk: String,
    },
    TaskCancelled {
        task_id: String,
        timestamp: DateTime<Utc>,
    },
    
    // Approval events
    ApprovalRequired {
        approval: ApprovalRequest,
    },
    ApprovalGranted {
        approval_id: String,
        granted_at: DateTime<Utc>,
    },
    ApprovalDenied {
        approval_id: String,
        denied_at: DateTime<Utc>,
        reason: Option<String>,
    },
    
    // Finding events
    FindingDiscovered {
        finding: Finding,
    },
    
    // Log events
    LogEntry {
        level: LogLevel,
        agent: Option<AgentType>,
        message: String,
        timestamp: DateTime<Utc>,
    },
    
    // System events
    SystemHealth {
        cpu: f32,
        memory: f32,
        timestamp: DateTime<Utc>,
    },
    TorStatus {
        connected: bool,
        circuit: Option<String>,
    },
    BrowserStatus {
        active: bool,
        url: Option<String>,
    },
    OllamaStatus {
        available: bool,
        model: Option<String>,
        model_count: usize,
        needs_pull: bool,
    },
    
    // Error events
    Error {
        message: String,
        details: Option<String>,
    },
    
    // Client commands
    CreateSession {
        name: String,
        mode: OperationalMode,
        metadata: Option<std::collections::HashMap<String, String>>,
    },
    LoadSession {
        session_id: String,
    },
    SaveSession {
        session_id: String,
    },
    DeleteSession {
        session_id: String,
    },
    ExportSession {
        session_id: String,
    },
    QueueTask {
        tool_name: String,
        target: String,
        args: serde_json::Value,
    },
    CancelTask {
        task_id: String,
    },
    ApproveAction {
        approval_id: String,
    },
    DenyAction {
        approval_id: String,
        reason: Option<String>,
    },
    GetSessionList,
    GetAgentStatus {
        agent: AgentType,
    },
    Chat {
        message: String,
        model: Option<String>,
    },
    GetOllamaStatus,
    ChatResponse {
        response: String,
        model: String,
    },
}

/// Session delta for incremental updates
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionDelta {
    pub task_added: Option<Task>,
    pub task_updated: Option<Task>,
    pub approval_added: Option<ApprovalRequest>,
    pub approval_updated: Option<ApprovalRequest>,
    pub finding_added: Option<Finding>,
    pub artifact_added: Option<Artifact>,
    pub status_changed: Option<SessionStatus>,
}

/// Scan request from planner
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanRequest {
    pub tool_name: String,
    pub target: String,
    pub args: serde_json::Value,
    pub reasoning: Option<String>,
}

/// Task execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResult {
    pub success: bool,
    pub output: String,
    pub structured_data: Option<serde_json::Value>,
    pub duration_ms: u64,
}

/// Log level
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "UPPERCASE")]
pub enum LogLevel {
    Debug,
    Info,
    Warn,
    Error,
}

impl WSEvent {
    /// Create a log entry event
    pub fn log(level: LogLevel, message: impl Into<String>, agent: Option<AgentType>) -> Self {
        Self::LogEntry {
            level,
            agent,
            message: message.into(),
            timestamp: Utc::now(),
        }
    }
    
    /// Create an error event
    pub fn error(message: impl Into<String>, details: Option<String>) -> Self {
        Self::Error {
            message: message.into(),
            details,
        }
    }
}
