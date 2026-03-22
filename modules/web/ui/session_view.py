import streamlit as st
from datetime import datetime
from modules.session.session_manager import SessionManager


def render_session_view(session_manager: SessionManager):
    """
    Renders the Session Management interface.
    Allows creating new sessions and loading existing ones.
    """
    st.title("🗂️ Session Manager")
    st.write("Manage your security assessment sessions.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Create New Session")
        with st.form("create_session_form"):
            name = st.text_input(
                "Session Name", value=f"Op-{datetime.now().strftime('%Y%m%d-%H%M')}"
            )
            target = st.text_input("Target (Domain/IP)", placeholder="example.com")
            mode = st.selectbox(
                "Operational Mode",
                ["offensive", "defensive"],
                help="Offensive: Active Scanning allowed. Defensive: Passive/Analysis only.",
            )
            description = st.text_area(
                "Description", placeholder="Objective of this assessment..."
            )

            submitted = st.form_submit_button("🚀 Launch Session", type="primary")
            if submitted:
                if not target:
                    st.error("Target is required.")
                else:
                    try:
                        session_id = session_manager.create_session(
                            name=name, mode=mode, description=description
                        )
                        # Set initial target in task state
                        session_manager.update_session_state(
                            {"task_state": {"target": target}}
                        )
                        st.session_state.active_session_id = session_id
                        st.success(f"Session '{name}' created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create session: {e}")

    with col2:
        st.subheader("Existing Sessions")
        sessions = session_manager.list_sessions()

        if not sessions:
            st.info("No active sessions found.")
        else:
            # Convert to DataFrame for nicer display? Or just list
            for s in sessions:
                with st.expander(
                    f"{s['name']}  |  {s['mode'].upper()}  |  {s['updated_at'][:16]}"
                ):
                    st.caption(f"ID: {s['id']}")

                    if st.button("📂 Load Session", key=f"load_{s['id']}"):
                        session_manager.resume_session(s["id"])
                        st.session_state.active_session_id = s["id"]
                        st.rerun()

                    if st.button("🗑️ Delete", key=f"del_{s['id']}"):
                        session_manager.delete_session(s["id"])
                        st.rerun()
