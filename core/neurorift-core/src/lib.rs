pub mod state;
pub mod session;
pub mod websocket;
pub mod python_bridge;
pub mod security;

use anyhow::Result;
use dashmap::DashMap;
use std::sync::Arc;
use std::path::PathBuf;
use parking_lot::RwLock;
use crate::state::{SessionState, OperationalMode, AgentType, AgentState};
use crate::session::SessionManager;
use crate::websocket::{WebSocketServer, events::WSEvent};
use crate::python_bridge::PythonBridge;

/// Core orchestrator for NeuroRift
pub struct NeuroRiftCore {
    /// Active sessions (in-memory)
    sessions: Arc<DashMap<String, Arc<RwLock<SessionState>>>>,
    
    /// Session persistence
    session_manager: Arc<SessionManager>,
    
    /// WebSocket server
    ws_server: Arc<WebSocketServer>,
    
    /// Python bridge
    python_bridge: Arc<PythonBridge>,
    
    /// Current active session ID
    active_session: Arc<RwLock<Option<String>>>,
}

impl NeuroRiftCore {
    /// Create a new NeuroRift core
    pub fn new(
        base_dir: PathBuf,
        ws_addr: std::net::SocketAddr,
        python_bridge_url: String,
    ) -> Result<Self> {
        let session_manager = Arc::new(SessionManager::new(&base_dir)?);
        let ws_server = Arc::new(WebSocketServer::new(ws_addr));
        let python_bridge = Arc::new(PythonBridge::new(python_bridge_url));
        
        Ok(Self {
            sessions: Arc::new(DashMap::new()),
            session_manager,
            ws_server,
            python_bridge,
            active_session: Arc::new(RwLock::new(None)),
        })
    }
    
    /// Get WebSocket server
    pub fn ws_server(&self) -> Arc<WebSocketServer> {
        self.ws_server.clone()
    }
    
    /// Create a new session
    pub fn create_session(&self, name: String, mode: OperationalMode, metadata: Option<std::collections::HashMap<String, String>>) -> Result<String> {
        let mut session = SessionState::new(name.clone(), mode);
        
        if let Some(meta) = metadata {
            session.metadata = meta;
        }
        
        let session_id = session.id.clone();
        
        self.sessions.insert(session_id.clone(), Arc::new(RwLock::new(session)));
        *self.active_session.write() = Some(session_id.clone());
        
        // Broadcast event
        self.ws_server.broadcast(WSEvent::SessionCreated {
            session_id: session_id.clone(),
            name,
        });
        
        tracing::info!("Session created: {}", session_id);
        Ok(session_id)
    }

    /// Delete a session
    pub fn delete_session(&self, session_id: &str) -> Result<()> {
        // Remove from memory
        self.sessions.remove(session_id);
        
        // Clear active session if it matches
        let mut active = self.active_session.write();
        if let Some(active_id) = &*active {
            if active_id == session_id {
                *active = None;
            }
        }
        
        // Delete from disk
        self.session_manager.delete_session(session_id)?;
        
        // Broadcast event
        self.ws_server.broadcast(WSEvent::SessionDeleted {
            session_id: session_id.to_string(),
        });
        
        tracing::info!("Session deleted: {}", session_id);
        Ok(())
    }

    /// Export session to file
    pub fn export_session(&self, session_id: &str) -> Result<PathBuf> {
        // Ensure latest state is saved
        self.save_session(session_id)?;
        
        let path = self.session_manager.export_session_auto(session_id)?;
        tracing::info!("Session exported to: {:?}", path);
        Ok(path)
    }
    
    /// List all sessions
    pub fn list_sessions(&self) -> Result<()> {
        let sessions = self.session_manager.list_sessions()?;
        
        self.ws_server.broadcast(WSEvent::SessionList {
            sessions,
        });
        
        Ok(())
    }

    /// Load a session from disk
    pub fn load_session(&self, session_id: &str) -> Result<()> {
        let session = self.session_manager.load_session(session_id)?;
        let id = session.id.clone();
        
        self.sessions.insert(id.clone(), Arc::new(RwLock::new(session.clone())));
        *self.active_session.write() = Some(id.clone());
        
        // Broadcast event
        self.ws_server.broadcast(WSEvent::SessionLoaded {
            session_id: id,
            state: session,
        });
        
        Ok(())
    }
    
    /// Save current session
    pub fn save_session(&self, session_id: &str) -> Result<()> {
        if let Some(session_ref) = self.sessions.get(session_id) {
            let session = session_ref.read().clone();
            self.session_manager.save_session(&session)?;
            
            // Broadcast event
            self.ws_server.broadcast(WSEvent::SessionSaved {
                session_id: session_id.to_string(),
                timestamp: chrono::Utc::now(),
            });
        }
        
        Ok(())
    }
    
    /// Get active session
    pub fn get_active_session(&self) -> Option<Arc<RwLock<SessionState>>> {
        let active_id = self.active_session.read().clone()?;
        self.sessions.get(&active_id).map(|r| r.value().clone())
    }
    
    /// Queue a task in the active session
    pub fn queue_task(&self, tool_name: String, target: String, args: serde_json::Value) -> Result<Option<String>> {
        if let Some(session) = self.get_active_session() {
            let mut session = session.write();
            let args_map = args.as_object()
                .map(|obj| obj.iter().map(|(k, v)| (k.clone(), v.clone())).collect())
                .unwrap_or_default();
            
            session.queue_task(tool_name.clone(), target.clone(), args_map);
            
            // Get the task that was just added
            if let Some(task) = session.task_queue.back() {
                let task_id = task.id.clone();
                self.ws_server.broadcast(WSEvent::TaskQueued {
                    task: task.clone(),
                });
                return Ok(Some(task_id));
            }
        }
        
        Ok(None)
    }

    /// Cancel a queued/running task.
    pub fn cancel_task(&self, task_id: &str) -> Result<()> {
        if let Some(session) = self.get_active_session() {
            let mut session = session.write();
            if let Some(task) = session.task_queue.iter_mut().find(|task| task.id == task_id) {
                task.status = crate::state::TaskStatus::Cancelled;
                task.completed_at = Some(chrono::Utc::now());
                session.touch();
                self.ws_server.broadcast(WSEvent::TaskCancelled {
                    task_id: task_id.to_string(),
                    timestamp: chrono::Utc::now(),
                });
            }
        }
        Ok(())
    }

    /// Execute a task by ID through the Python bridge.
    pub async fn execute_task(&self, task_id: &str) -> Result<()> {
        let (session_id, tool_name, target, args, mode) = if let Some(session) = self.get_active_session() {
            let mut session = session.write();
            let session_id = session.id.clone();
            let mode = session.mode;

            if let Some(task) = session.task_queue.iter_mut().find(|task| task.id == task_id) {
                task.status = crate::state::TaskStatus::Running;
                task.started_at = Some(chrono::Utc::now());
                let args = serde_json::Value::Object(task.args.clone().into_iter().collect());
                let tool_name = task.tool_name.clone();
                let target = task.target.clone();
                self.ws_server.broadcast(WSEvent::TaskStarted {
                    task_id: task.id.clone(),
                    started_at: chrono::Utc::now(),
                });
                (session_id, tool_name, target, args, mode)
            } else {
                return Ok(());
            }
        } else {
            return Ok(());
        };

        let command = serde_json::json!({
            "type": "tool_execute",
            "tool": tool_name,
            "target": target,
            "args": args,
            "mode": format!("{:?}", mode).to_uppercase(),
            "session_id": session_id,
        });

        let result = self.python_bridge.execute(command).await;

        if let Some(session) = self.get_active_session() {
            let mut session = session.write();
            if let Some(task) = session.task_queue.iter_mut().find(|task| task.id == task_id) {
                match result {
                    Ok(data) => {
                        let raw_output = data
                            .get("raw_output")
                            .and_then(|v| v.as_str())
                            .unwrap_or_default()
                            .to_string();
                        let success = data
                            .get("status")
                            .and_then(|v| v.as_str())
                            .map(|s| s.eq_ignore_ascii_case("completed"))
                            .unwrap_or(true);

                        task.status = if success {
                            crate::state::TaskStatus::Completed
                        } else {
                            crate::state::TaskStatus::Failed
                        };
                        task.completed_at = Some(chrono::Utc::now());
                        session.touch();

                        self.ws_server.broadcast(WSEvent::TaskOutput {
                            task_id: task_id.to_string(),
                            chunk: raw_output.clone(),
                        });

                        if success {
                            self.ws_server.broadcast(WSEvent::TaskCompleted {
                                task_id: task_id.to_string(),
                                result: crate::websocket::events::TaskResult {
                                    success: true,
                                    output: raw_output,
                                    structured_data: data.get("structured_output").cloned(),
                                    duration_ms: (data.get("duration_seconds").and_then(|v| v.as_f64()).unwrap_or(0.0) * 1000.0) as u64,
                                },
                            });
                        } else {
                            self.ws_server.broadcast(WSEvent::TaskFailed {
                                task_id: task_id.to_string(),
                                error: data.get("error").and_then(|v| v.as_str()).unwrap_or("tool execution failed").to_string(),
                            });
                        }
                    }
                    Err(error) => {
                        task.status = crate::state::TaskStatus::Failed;
                        task.completed_at = Some(chrono::Utc::now());
                        session.touch();
                        self.ws_server.broadcast(WSEvent::TaskFailed {
                            task_id: task_id.to_string(),
                            error: error.to_string(),
                        });
                    }
                }
            }
        }

        if let Some(session) = self.get_active_session() {
            let session_id = session.read().id.clone();
            let _ = self.save_session(&session_id);
        }

        Ok(())
    }
    
    /// Update agent status
    pub fn update_agent_status(&self, agent: AgentType, state: AgentState, current_task: Option<String>) {
        if let Some(session) = self.get_active_session() {
            let mut session = session.write();
            
            if let Some(agent_status) = session.agent_states.get_mut(&agent) {
                agent_status.state = state;
                agent_status.current_task = current_task;
                agent_status.last_update = chrono::Utc::now();
                
                // Broadcast event
                self.ws_server.broadcast(WSEvent::AgentStatusChanged {
                    agent,
                    status: agent_status.clone(),
                });
            }
        }
    }
    
    /// Handle chat message
    pub async fn chat(&self, message: String, model: Option<String>) -> Result<()> {
        let session_id = self
            .get_active_session()
            .map(|s| s.read().id.clone())
            .unwrap_or_else(|| "default".to_string());

        // Forward to Python bridge
        let cmd = serde_json::json!({
            "type": "ai_generate",
            "prompt": message,
            "model": model,
            "session_id": session_id,
        });
        
        let data = match self.python_bridge.execute(cmd).await {
            Ok(data) => data,
            Err(error) => {
                self.ws_server.broadcast(WSEvent::Error {
                    message: "AI generation failed".to_string(),
                    details: Some(error.to_string()),
                });
                return Ok(());
            }
        };
        
        if let Some(text) = data.get("response").and_then(|v| v.as_str()) {
            let model = data.get("model").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
            
            // Broadcast response
            self.ws_server.broadcast(WSEvent::ChatResponse {
                response: text.to_string(),
                model,
            });
        }
        
        Ok(())
    }

    pub async fn get_ollama_status(&self) -> Result<()> {
        let data = self.python_bridge.execute(serde_json::json!({
            "type": "ai_status"
        })).await?;

        self.ws_server.broadcast(WSEvent::OllamaStatus {
            available: data.get("available").and_then(|v| v.as_bool()).unwrap_or(false),
            model: data.get("model").and_then(|v| v.as_str()).map(|s| s.to_string()),
            model_count: data.get("model_count").and_then(|v| v.as_u64()).unwrap_or(0) as usize,
            needs_pull: data.get("needs_pull").and_then(|v| v.as_bool()).unwrap_or(false),
        });

        Ok(())
    }

    /// Get Python bridge
    pub fn python_bridge(&self) -> Arc<PythonBridge> {
        self.python_bridge.clone()
    }
}
