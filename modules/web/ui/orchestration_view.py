import streamlit as st
import asyncio
import pandas as pd
from modules.orchestration.execution_manager import ExecutionManager
from modules.ai.agents import NRPlanner, NROperator, NRAnalyst, NRScribe
from modules.orchestration.data_models import (
    SessionContext,
    ToolExecutionResult,
    ScanRequest,
)
from modules.tools.base import ToolMode


def render_orchestration_view(
    session_manager, execution_manager, planner, operator, analyst, scribe
):
    """
    Renders the Orchestration View.
    Handles the 4-step workflow: Plan -> Approve -> Execute -> Report.
    """
    session = session_manager.get_current_session()
    if not session:
        st.error("No active session.")
        return

    # Header
    target = session["task_state"].get("target") or "Unknown"
    mode = session["session"]["mode"]
    st.markdown(f"### 🎯 Target: `{target}` | Mode: `{mode.upper()}`")

    # Workflow Steps (Tabs)
    tab_manual, tab_plan, tab_exec, tab_results, tab_report = st.tabs(
        ["0. Manual", "1. Plan", "2. Execute", "3. Results", "4. Report"]
    )

    # --- TAB 0: MANUAL OPERATIONS ---
    with tab_manual:
        st.markdown("#### Manual Control")
        st.info("Execute specific tools directly without AI planning.")

        tools = execution_manager.list_tools()
        tool_names = [t["name"] for t in tools]

        c1, c2 = st.columns([1, 2])
        with c1:
            selected_tool = st.selectbox("Select Tool", tool_names)
        with c2:
            import json

            # Default helper based on tool
            default_args = "{}"
            if selected_tool == "nmap":
                default_args = '{"flags": ["-F"]}'
            elif selected_tool == "masscan":
                default_args = '{"ports": "80,443", "rate": "100"}'

            args_input = st.text_area(
                "Arguments (JSON)", value=default_args, height=100
            )

        if st.button("🚀 Run Tool Manually", type="primary"):
            try:
                args = json.loads(args_input)

                # Setup proper context
                tool_mode = (
                    ToolMode.OFFENSIVE if mode == "offensive" else ToolMode.DEFENSIVE
                )
                context = SessionContext(
                    session_id=session["session"]["id"], mode=tool_mode, target=target
                )

                req = ScanRequest(tool_name=selected_tool, target=target, args=args)

                with st.spinner(f"Running {selected_tool}..."):
                    result = asyncio.run(execution_manager.execute_tool(req, context))

                if result.status == "success":
                    st.success("Execution Successful")
                    with st.expander("Output", expanded=True):
                        st.code(result.raw_output)

                    # Optional: Add to findings automatically?
                    # For manual mode, maybe just raw output is enough, or optional analysis.
                    if st.button("Analyze this output with AI?"):
                        # Hook into analyst
                        pass
                else:
                    st.error(f"Execution Failed: {result.error}")

            except json.JSONDecodeError:
                st.error("Invalid JSON format for arguments.")
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 1: PLAN ---
    with tab_plan:
        st.markdown("#### Mission Planning")
        task_desc = st.text_area(
            "Mission Objective",
            value=session.get("task_state", {})
            .get("plan", {})
            .get("goal", f"Perform a {mode} security assessment on {target}"),
        )

        if st.button("Generate Plan"):
            with st.spinner("AI Planner is strategizing..."):
                available_tools = execution_manager.list_tools()
                requests = asyncio.run(planner.create_plan(task_desc, available_tools))

                # Store plan in session state
                st.session_state.current_plan = requests
                # Update session data
                session_manager.update_session_state(
                    {
                        "task_state": {
                            "plan": {
                                "goal": task_desc,
                                "steps": [r.dict() for r in requests],
                            }
                        }
                    }
                )

        # Display Plan
        if "current_plan" in st.session_state and st.session_state.current_plan:
            st.success(f"Plan Generated: {len(st.session_state.current_plan)} steps")

            steps_data = []
            for i, req in enumerate(st.session_state.current_plan):
                steps_data.append(
                    {
                        "Step": i + 1,
                        "Tool": req.tool_name,
                        "Args": str(req.args),
                        "Reasoning": getattr(
                            req, "reasoning", "N/A"
                        ),  # Assuming we added reasoning to Request or handle separately
                    }
                )

            st.table(pd.DataFrame(steps_data))

            if st.button("✅ Approve Plan"):
                st.session_state.plan_approved = True
                st.session_state.execution_ready = True
                st.info("Plan approved! Move to the Execute tab.")
        else:
            st.info("No plan generated yet.")

    # --- TAB 2: EXECUTE ---
    with tab_exec:
        st.markdown("#### Mission Execution")

        if not st.session_state.get("plan_approved"):
            st.warning("Please generate and approve a plan first.")
        else:
            if st.button("▶️ Start Execution", type="primary"):
                # Setup context
                tool_mode = (
                    ToolMode.OFFENSIVE if mode == "offensive" else ToolMode.DEFENSIVE
                )
                context = SessionContext(
                    session_id=session["session"]["id"], mode=tool_mode, target=target
                )

                # Progress container
                prog_container = st.container()

                async def run_pipeline():
                    results = []
                    total = len(st.session_state.current_plan)

                    progress_bar = prog_container.progress(0, text="Starting...")

                    for i, req in enumerate(st.session_state.current_plan):
                        progress_bar.progress(
                            (i) / total, text=f"Running {req.tool_name}..."
                        )

                        # Run tool
                        result = await execution_manager.execute_tool(req, context)
                        results.append(result)

                        # Show intermediate status
                        if result.status == "success":
                            prog_container.success(f"✅ {req.tool_name}: Success")
                        else:
                            prog_container.error(
                                f"❌ {req.tool_name}: Failed - {result.error}"
                            )

                    progress_bar.progress(1.0, text="Execution Complete")
                    return results

                with st.spinner("Executing tools..."):
                    execution_results = asyncio.run(run_pipeline())
                    st.session_state.execution_results = execution_results
                    st.success("All steps completed.")

    # --- TAB 3: RESULTS ---
    with tab_results:
        st.markdown("#### Mission Analysis")

        if "execution_results" in st.session_state:
            results = st.session_state.execution_results

            # Run Analyst
            if st.button("🧠 Run AI Analysis"):
                with st.spinner("Analyzing output..."):
                    findings = asyncio.run(analyst.analyze_results(results))
                    st.session_state.findings = findings

            if "findings" in st.session_state:
                findings = st.session_state.findings
                if findings:
                    for f in findings:
                        with st.expander(f"[{f.severity}] {f.title}"):
                            st.write(f"**Tool:** {f.tool_source}")
                            st.write(f"**Description:** {f.description}")
                else:
                    st.info("No significant findings identified.")

            # Show Raw Output
            st.divider()
            st.markdown("**Raw Tool Output**")
            for res in results:
                with st.expander(f"{res.tool_name} Output"):
                    st.code(res.raw_output)
        else:
            st.info("No execution results yet.")

    # --- TAB 4: REPORT ---
    with tab_report:
        st.markdown("#### Report Generation")

        if "findings" in st.session_state:
            if st.button("📝 Generate Report"):
                with st.spinner("Compiling report..."):
                    # task_desc might be in local scope, grab from session if needed
                    goal = (
                        session.get("task_state", {})
                        .get("plan", {})
                        .get("goal", f"Scan {target}")
                    )
                    report_content = asyncio.run(
                        scribe.generate_report(goal, st.session_state.findings)
                    )
                    st.session_state.report_content = report_content

            if "report_content" in st.session_state:
                st.markdown(st.session_state.report_content)
                st.download_button(
                    "Download Report (MD)",
                    st.session_state.report_content,
                    file_name=f"report_{session['session']['id']}.md",
                )
        else:
            st.warning("No findings available to report on.")
