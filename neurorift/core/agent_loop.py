class AgentLoop:
    async def handle_message(self, session, message: str) -> dict:
        return {"success": True, "response": f"Session {session.session_id}: {message}"}
