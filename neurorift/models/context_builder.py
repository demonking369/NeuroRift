class ContextBuilder:
    def build(self, session, memories):
        return {"session": session.session_id, "memories": memories}
