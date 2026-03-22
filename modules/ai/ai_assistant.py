import os


class AIAssistant:
    def ask_ai(self, query, context=None, debug=False):
        try:
            response = self.llm.ask(query, context=context, debug=debug)
            if not response or not response.strip():
                response = "[AI Fallback] No answer generated. Please check your query or try again."
            self._log_ai_interaction(query, response, debug)
            return response
        except Exception as e:
            self._log_ai_interaction(query, f"[AI ERROR] {e}", debug)
            return f"[AI ERROR] {e}"

    def recommend_tools(self, context):
        try:
            tools = self.llm.recommend_tools(context)
            if not tools or not isinstance(tools, list) or not tools:
                tools = ["nmap", "subfinder", "httpx", "nuclei"]
            self._log_ai_interaction("recommend_tools", str(tools), False)
            return tools
        except Exception as e:
            self._log_ai_interaction("recommend_tools", f"[AI ERROR] {e}", False)
            return ["nmap", "subfinder", "httpx", "nuclei"]

    def _log_ai_interaction(self, query, response, debug):
        log_path = os.path.expanduser("~/.neurorift/sessions/logs/ai_controller.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"[QUERY] {query}\n[RESPONSE] {response}\n[DEBUG] {debug}\n\n")
