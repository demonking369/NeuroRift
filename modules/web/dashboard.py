import streamlit as st
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# --- Path Setup ---
BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
sys.path.append(str(BASE_DIR))

# --- CSS & Config ---
st.set_page_config(
    page_title="NeuroRift v2.0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def local_css(file_name):
    if Path(file_name).exists():
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css(str(ASSETS_DIR / "neurorift.css"))

# --- Imports ---
try:
    from neurorift_main import NeuroRift
    from modules.web.ui.session_view import render_session_view
    from modules.web.ui.orchestration_view import render_orchestration_view
except ImportError as e:
    st.error(f"Failed to import NeuroRift components: {e}")
    st.stop()

# --- Initialization ---
if "neurorift" not in st.session_state:
    with st.spinner("Initializing NeuroRift Core..."):
        st.session_state.neurorift = NeuroRift()

if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

# Shortcut references
nr = st.session_state.neurorift
session_manager = nr.session_manager


# --- Main Controller ---
def main():
    # Sidebar Global Controls
    with st.sidebar:
        st.title("🛡️ NeuroRift")
        st.caption("Intelligence Amplified")

        if st.session_state.active_session_id:
            st.divider()
            sess = session_manager.get_current_session()
            if sess:
                st.info(f"Active: {sess['session']['name']}")
                if st.button("Close Session"):
                    st.session_state.active_session_id = None
                    st.rerun()

        st.divider()
        st.caption(f"v{nr.version}")

    # View Routing
    if not st.session_state.active_session_id:
        # Route: Session Management
        render_session_view(session_manager)
    else:
        # Route: Orchestration
        render_orchestration_view(
            session_manager,
            nr.execution_manager,
            nr.planner,
            nr.operator,
            nr.analyst,
            nr.scribe,
        )


if __name__ == "__main__":
    main()
