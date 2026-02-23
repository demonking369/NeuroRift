use anyhow::Result;
use reqwest::Client;
use serde_json::Value;
use std::time::Duration;

/// Python bridge for calling Python tools and AI
pub struct PythonBridge {
    client: Client,
    base_url: String,
}

impl PythonBridge {
    fn extract_data(result: Value) -> Result<Value> {
        let success = result.get("success").and_then(|v| v.as_bool()).unwrap_or(false);

        if !success {
            let error = result
                .get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("python bridge execution failed");
            anyhow::bail!(error.to_string());
        }

        Ok(result.get("data").cloned().unwrap_or(Value::Null))
    }

    /// Create a new Python bridge
    pub fn new(base_url: impl Into<String>) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(300)) // 5 minutes for long-running tools
            .build()
            .unwrap();
        
        Self {
            client,
            base_url: base_url.into(),
        }
    }
    
    /// Execute a Python command
    pub async fn execute(&self, command: Value) -> Result<Value> {
        let url = format!("{}/execute", self.base_url);
        
        let response = self.client
            .post(&url)
            .json(&command)
            .send()
            .await?;
        
        let result = response.json::<Value>().await?;
        Self::extract_data(result)
    }
    
    /// Execute a tool
    pub async fn execute_tool(&self, tool_name: &str, target: &str, args: Value) -> Result<Value> {
        let command = serde_json::json!({
            "type": "tool_execute",
            "tool": tool_name,
            "target": target,
            "args": args,
        });
        
        self.execute(command).await
    }
    
    /// Generate AI response
    pub async fn ai_generate(&self, prompt: &str, model: Option<&str>) -> Result<String> {
        let command = serde_json::json!({
            "type": "ai_generate",
            "prompt": prompt,
            "model": model,
        });
        
        let result = self.execute(command).await?;

        Ok(result["response"]
            .as_str()
            .unwrap_or("")
            .to_string())
    }
    
    /// Robin dark web search
    pub async fn robin_search(&self, query: &str) -> Result<Value> {
        let command = serde_json::json!({
            "type": "robin_search",
            "query": query,
        });
        
        self.execute(command).await
    }
    
    /// Browser automation action
    pub async fn browser_action(&self, action: &str, params: Value) -> Result<Value> {
        let command = serde_json::json!({
            "type": "browser_action",
            "action": action,
            "params": params,
        });
        
        self.execute(command).await
    }
}
