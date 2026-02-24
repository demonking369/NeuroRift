use anyhow::Result;
use neurorift_core::NeuroRiftCore;
use std::path::PathBuf;
use std::sync::Arc;
use tracing_subscriber;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_target(false)
        .with_thread_ids(true)
        .with_level(true)
        .init();
    
    tracing::info!("🧠 NeuroRift Core starting...");
    
    // Configuration
    let base_dir = PathBuf::from(std::env::var("NEURORIFT_HOME")
        .unwrap_or_else(|_| {
            let home = std::env::var("HOME").unwrap();
            format!("{}/.neurorift", home)
        }));
    
    let ws_addr = "127.0.0.1:8765".parse()?;
    let python_bridge_url = "http://127.0.0.1:8766".to_string();
    
    // Create core
    let core = Arc::new(NeuroRiftCore::new(
        base_dir,
        ws_addr,
        python_bridge_url.clone(),
    )?);
    
    tracing::info!("✅ NeuroRift Core initialized");
    tracing::info!("📡 WebSocket server: ws://{}", ws_addr);
    tracing::info!("🐍 Python bridge: {}", python_bridge_url);
    
    // Start WebSocket server
    let ws_server = core.ws_server();
    let ws_task = tokio::spawn(async move {
        if let Err(e) = ws_server.run().await {
            tracing::error!("WebSocket server error: {}", e);
        }
    });
    
    // Start auto-save task
    let core_clone = core.clone();
    let autosave_task = tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(300)); // 5 minutes
        loop {
            interval.tick().await;
            
            if let Some(session) = core_clone.get_active_session() {
                let session_id = session.read().id.clone();
                if let Err(e) = core_clone.save_session(&session_id) {
                    tracing::error!("Auto-save failed: {}", e);
                } else {
                    tracing::info!("Auto-saved session: {}", session_id);
                }
            }
        }
    });
    
    // Start command listener
    let core_cmd = core.clone();
    let cmd_task = tokio::spawn(async move {
        let mut rx = core_cmd.ws_server().get_sender().subscribe();
        
        while let Ok(event) = rx.recv().await {
            use neurorift_core::websocket::events::WSEvent::*;
            
            match event {
                CreateSession { name, mode, metadata } => {
                    tracing::info!("Received CreateSession: {}", name);
                    if let Err(e) = core_cmd.create_session(name, mode, metadata) {
                        tracing::error!("Failed to create session: {}", e);
                    }
                }
                LoadSession { session_id } => {
                     tracing::info!("Received LoadSession: {}", session_id);
                     if let Err(e) = core_cmd.load_session(&session_id) {
                         tracing::error!("Failed to load session: {}", e);
                     }
                }
                SaveSession { session_id } => {
                    tracing::info!("Received SaveSession: {}", session_id);
                    if let Err(e) = core_cmd.save_session(&session_id) {
                         tracing::error!("Failed to save session: {}", e);
                    }
                }
                DeleteSession { session_id } => {
                    tracing::info!("Received DeleteSession: {}", session_id);
                    if let Err(e) = core_cmd.delete_session(&session_id) {
                        tracing::error!("Failed to delete session: {}", e);
                    }
                }
                ExportSession { session_id } => {
                    tracing::info!("Received ExportSession: {}", session_id);
                    if let Err(e) = core_cmd.export_session(&session_id) {
                        tracing::error!("Failed to export session: {}", e);
                    }
                }
                GetSessionList => {
                    tracing::info!("Received GetSessionList");
                    if let Err(e) = core_cmd.list_sessions() {
                        tracing::error!("Failed to list sessions: {}", e);
                    }
                }
                QueueTask { tool_name, target, args } => {
                    tracing::info!("Received QueueTask: {} -> {}", tool_name, target);
                    match core_cmd.queue_task(tool_name, target, args) {
                        Ok(Some(task_id)) => {
                            let core_exec = core_cmd.clone();
                            tokio::spawn(async move {
                                if let Err(e) = core_exec.execute_task(&task_id).await {
                                    tracing::error!("Failed to execute task {}: {}", task_id, e);
                                }
                            });
                        }
                        Ok(None) => {}
                        Err(e) => {
                            tracing::error!("Failed to queue task: {}", e);
                        }
                    }
                }
                CancelTask { task_id } => {
                    tracing::info!("Received CancelTask: {}", task_id);
                    if let Err(e) = core_cmd.cancel_task(&task_id) {
                        tracing::error!("Failed to queue task: {}", e);
                    }
                }
                Chat { message, model } => {
                     tracing::info!("Received Chat message");
                     let core_chat = core_cmd.clone();
                     tokio::spawn(async move {
                         if let Err(e) = core_chat.chat(message, model).await {
                             tracing::error!("Chat failed: {}", e);
                         }
                     });
                }
                GetOllamaStatus => {
                    let core_ai = core_cmd.clone();
                    tokio::spawn(async move {
                        if let Err(e) = core_ai.get_ollama_status().await {
                            tracing::error!("Failed to fetch Ollama status: {}", e);
                        }
                    });
                }
                _ => {} // Ignore other events
            }
        }
    });

    tracing::info!("🚀 NeuroRift Core ready!");
    
    // Wait for tasks
    tokio::select! {
        _ = ws_task => {
            tracing::info!("WebSocket server stopped");
        }
        _ = cmd_task => {
            tracing::info!("Command listener stopped");
        }
        _ = autosave_task => {
            tracing::info!("Auto-save task stopped");
        }
        _ = tokio::signal::ctrl_c() => {
            tracing::info!("Received Ctrl+C, shutting down...");
        }
    }
    
    tracing::info!("👋 NeuroRift Core stopped");
    Ok(())
}
