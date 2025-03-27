# ui.py
import streamlit as st
from io import BytesIO
import PyPDF2
from config import ASSISTANT_ID, SIMULATION_MODE
import time
from utils import replace_citations
from tender_analyzer import analyze_tender
import openai
import re


def render_main_content(
    uploaded_files, uploaded_file_ids, file_id_to_name, thread_id, analysis_results
):
    # Extract analysis results
    synthesized_dates = analysis_results.get("synthesized_dates", "")
    synthesized_requirements = analysis_results.get("synthesized_requirements", "")
    synthesized_folder_structure = analysis_results.get(
        "synthesized_folder_structure", ""
    )
    synthesized_client_info = analysis_results.get("synthesized_client_info", "")  # New
    summary_response = analysis_results["summary_response"]
    all_dates = analysis_results["all_dates"]
    all_requirements = analysis_results["all_requirements"]
    all_folder_structures = analysis_results["all_folder_structures"]
    progress_log_messages = analysis_results["progress_log_messages"]

    # Consolidated Analysis Section
    st.header("📊 Consolidated Tender Analysis", divider=True)
    # Client Information (New Section)
    st.subheader("👤 Client Information")
    with st.expander("View Client Information", expanded=True):
        if (
            synthesized_client_info.strip()
            and synthesized_client_info.strip() != "NO_INFO_FOUND"
        ):
            st.markdown(synthesized_client_info, unsafe_allow_html=False)
        else:
            st.markdown("No client information found.")

    # Tender Summary
    st.subheader("📝 Tender Summary")
    with st.expander("View Tender Summary", expanded=True):
        if summary_response.strip() and summary_response.strip() != "NO_INFO_FOUND":
            summary_response = replace_citations(summary_response, file_id_to_name)
            st.markdown(summary_response, unsafe_allow_html=False)
        else:
            st.markdown("No summary generated from the provided files.")

    # Consolidated Dates
    st.subheader("🕒 All Important Dates and Milestones")
    with st.expander("View Consolidated Dates", expanded=True):
        if synthesized_dates.strip() and synthesized_dates.strip() != "NO_INFO_FOUND":
            st.markdown(synthesized_dates, unsafe_allow_html=False)
        else:
            st.markdown("No important dates found across all files.")

    # Consolidated Requirements
    st.subheader("🔧 All Technical Requirements")
    with st.expander("View Consolidated Requirements", expanded=True):
        if (
            synthesized_requirements.strip()
            and synthesized_requirements.strip() != "NO_INFO_FOUND"
        ):
            st.markdown(synthesized_requirements, unsafe_allow_html=False)
        else:
            st.markdown("No technical requirements found across all files.")

    # Consolidated Folder Structure
    st.subheader("📁 Consolidated Required Folder Structure")
    with st.expander("View Consolidated Folder Structure", expanded=True):
        if (
            synthesized_folder_structure.strip()
            and synthesized_folder_structure.strip() != "NO_INFO_FOUND"
        ):
            st.markdown(synthesized_folder_structure, unsafe_allow_html=False)
        else:
            st.markdown("No folder structure information found across all files.")

    # Per-File Analysis Section
    st.header("📄 Per-File Analysis", divider=True)

    # Per-File Dates
    st.subheader("🕒 Important Dates and Milestones per File")
    with st.expander("View Dates per File", expanded=False):
        consolidated_dates = ""
        for i, file_id in enumerate(uploaded_file_ids):
            file_name = file_id_to_name[file_id]
            dates_response = all_dates[i] if i < len(all_dates) else ""
            if dates_response.strip() and dates_response.strip() != "NO_INFO_FOUND":
                dates_response = replace_citations(
                    dates_response, file_id_to_name, intended_file_name=file_name
                )
                consolidated_dates += (
                    f"Dates from {file_name}:\n{dates_response}\n\n---\n\n"
                )
        if consolidated_dates:
            st.markdown(consolidated_dates, unsafe_allow_html=False)
        else:
            st.markdown("No important dates extracted from the provided files.")

    # Per-File Requirements
    st.subheader("🔧 Technical Requirements per File")
    with st.expander("View Requirements per File", expanded=False):
        consolidated_requirements = ""
        for i, file_id in enumerate(uploaded_file_ids):
            file_name = file_id_to_name[file_id]
            requirements_response = (
                all_requirements[i] if i < len(all_requirements) else ""
            )
            if (
                requirements_response.strip()
                and requirements_response.strip() != "NO_INFO_FOUND"
            ):
                requirements_response = replace_citations(
                    requirements_response, file_id_to_name, intended_file_name=file_name
                )
                consolidated_requirements += f"Requirements from {file_name}:\n{requirements_response}\n\n---\n\n"
        if consolidated_requirements:
            st.markdown(consolidated_requirements, unsafe_allow_html=False)
        else:
            st.markdown("No technical requirements extracted from the provided files.")

    # Per-File Folder Structure
    st.subheader("📁 Required Folder Structure per File")
    with st.expander("View Folder Structure per File", expanded=False):
        consolidated_folder_structure = ""
        for i, file_id in enumerate(uploaded_file_ids):
            file_name = file_id_to_name[file_id]
            folder_structure_response = (
                all_folder_structures[i] if i < len(all_folder_structures) else ""
            )
            if (
                folder_structure_response.strip()
                and folder_structure_response.strip() != "NO_INFO_FOUND"
            ):
                folder_structure_response = replace_citations(
                    folder_structure_response,
                    file_id_to_name,
                    intended_file_name=file_name,
                )
                consolidated_folder_structure += f"Folder Structure from {file_name}:\n{folder_structure_response}\n\n---\n\n"
        if consolidated_folder_structure:
            st.markdown(consolidated_folder_structure, unsafe_allow_html=False)
        else:
            st.markdown("No folder structure extracted from the provided files.")

    # Update Download Report
    full_report = "Tender Analysis Report\n\n"
    if (
        synthesized_client_info.strip()
        and synthesized_client_info.strip() != "NO_INFO_FOUND"
    ):
        full_report += "## Client Information\n" + synthesized_client_info + "\n\n"
    if synthesized_dates.strip() and synthesized_dates.strip() != "NO_INFO_FOUND":
        full_report += "## Consolidated Dates\n" + synthesized_dates + "\n\n"
    if (
        synthesized_requirements.strip()
        and synthesized_requirements.strip() != "NO_INFO_FOUND"
    ):
        full_report += (
            "## Consolidated Requirements\n" + synthesized_requirements + "\n\n"
        )
    if (
        synthesized_folder_structure.strip()
        and synthesized_folder_structure.strip() != "NO_INFO_FOUND"
    ):
        full_report += (
            "## Consolidated Folder Structure\n" + synthesized_folder_structure + "\n\n"
        )
    if summary_response.strip() and summary_response.strip() != "NO_INFO_FOUND":
        full_report += "## Tender Summary\n" + summary_response + "\n\n"
    if consolidated_dates:
        full_report += (
            "## Important Dates and Milestones per File\n" + consolidated_dates + "\n\n"
        )
    if consolidated_requirements:
        full_report += (
            "## Technical Requirements per File\n" + consolidated_requirements + "\n\n"
        )
    if consolidated_folder_structure:
        full_report += (
            "## Required Folder Structure per File\n"
            + consolidated_folder_structure
            + "\n\n"
        )
    st.download_button(
        "📥 Download Full Report",
        full_report,
        file_name="tender_analysis_report.txt",
        mime="text/plain",
    )

    # Chat Interface (unchanged from original)
    st.subheader("💬 Chat with Assistant")
    if "thread_id" not in locals():
        st.info("Please upload and analyze a document first.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for chat in st.session_state.chat_history:
            st.markdown(
                f"<div class='chat-message user-message'><strong>You:</strong> {chat['user']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='chat-message assistant-message'><strong>Assistant:</strong> {chat['assistant']}</div>",
                unsafe_allow_html=True,
            )

        with st.form(key="chat_form"):
            user_query = st.text_area(
                "Ask a question about the analyzed documents:", height=100
            )
            submit_button = st.form_submit_button("Send")

            if submit_button and user_query.strip():
                spinner_placeholder = st.empty()
                if SIMULATION_MODE:
                    with spinner_placeholder.container():
                        st.spinner("Generating response... (Status: mock)")
                    time.sleep(1)
                    assistant_response = (
                        "This is a mock chat response to your query: " + user_query
                    )
                else:
                    openai.beta.threads.messages.create(
                        thread_id=thread_id, role="user", content=user_query
                    )
                    run = openai.beta.threads.runs.create(
                        thread_id=thread_id, assistant_id=ASSISTANT_ID.strip()
                    )
                    while True:
                        run_status = openai.beta.threads.runs.retrieve(
                            thread_id=thread_id, run_id=run.id
                        )
                        with spinner_placeholder.container():
                            st.spinner(
                                f"Generating response... (Status: {run_status.status})"
                            )
                        if run_status.status == "completed":
                            break
                        time.sleep(0.5)
                    spinner_placeholder.empty()
                    messages = openai.beta.threads.messages.list(thread_id=thread_id)
                    assistant_response = next(
                        (
                            msg.content[0].text.value
                            for msg in messages.data
                            if msg.role == "assistant"
                        ),
                        "No response generated.",
                    )
                assistant_response = replace_citations(
                    assistant_response, file_id_to_name
                )
                st.session_state.chat_history.append(
                    {"user": user_query, "assistant": assistant_response}
                )
                st.rerun()
