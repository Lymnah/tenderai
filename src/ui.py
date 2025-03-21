# ui.py
import streamlit as st
from io import BytesIO
import PyPDF2
from config import ASSISTANT_ID, SIMULATION_MODE
import time
from utils import replace_citations
from tender_analyzer import analyze_tender
import openai


def clean_dates_response(response, file_name):
    """Clean up the dates response by consolidating 'No important dates found' messages."""
    lines = response.split("\n")
    cleaned_lines = []
    seen_no_dates = False
    no_dates_message = (
        f"\nNo important dates, milestones, or deadlines found in {file_name}."
    )

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check for "No important dates found" messages
        if "No important dates" in line:
            if not seen_no_dates:
                cleaned_lines.append(no_dates_message)
                seen_no_dates = True
            continue
        # Include other lines (e.g., actual date entries or additional details)
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def render_main_content(uploaded_files, uploaded_file_ids, file_id_to_name, thread_id):
    if uploaded_files:
        # Create tabs for Results and Progress Log at the start
        tab1, tab2 = st.tabs(["Results", "Progress Log"])

        # Tab 1: Results (initially empty, will be populated after analysis)
        with tab1:
            st.header("📊 Tender Analysis Results", divider=True)
            results_placeholder = st.empty()
            results_placeholder.info(
                "Analysis results will appear here once processing is complete."
            )

        # Tab 2: Progress Log
        with tab2:
            st.header("📜 Progress Log", divider=True)
            progress_log_placeholder = st.empty()  # Single placeholder for the log

        # Analysis with enhanced feedback
        with tab1:
            subheader_analysis = st.subheader("Analyzing Documents...")
            progress_bar = st.progress(0)
            status_text = st.empty()

        (
            all_dates,
            all_requirements,
            all_folder_structures,
            summary_response,
            progress_log_messages,
        ) = analyze_tender(
            uploaded_file_ids,
            file_id_to_name,
            progress_bar,
            status_text,
            progress_log_placeholder,
        )

        # Clear the progress indicators from the Results tab
        progress_bar.empty()
        status_text.empty()
        subheader_analysis.empty()

        # Populate the Results tab with analysis results
        with tab1:
            results_placeholder.empty()  # Clear the placeholder message
            # Tender Summary Section
            st.subheader("📝 Tender Summary")
            with st.expander("View Tender Summary", expanded=True):
                st.markdown(summary_response, unsafe_allow_html=False)

            # Important Dates Section
            st.subheader("🕒 Important Dates and Milestones")
            with st.expander("View Dates and Milestones", expanded=True):
                if not all_dates:
                    st.markdown(
                        "No important dates found in any of the provided files."
                    )
                else:
                    consolidated_dates = (
                        "Consolidated Important Dates and Milestones:\n\n"
                    )
                    for i, file_id in enumerate(uploaded_file_ids):
                        file_name = file_id_to_name[file_id]
                        dates_response = all_dates[i]
                        if dates_response.strip():
                            # Fix incorrect file references
                            dates_response = replace_citations(
                                dates_response,
                                file_id_to_name,
                                intended_file_name=file_name,
                            )
                            # Clean up repeated "No important dates found" messages
                            cleaned_response = clean_dates_response(
                                dates_response, file_name
                            )
                            consolidated_dates += f"Dates from {file_name}:\n"
                            consolidated_dates += cleaned_response + "\n\n---\n\n"
                    st.markdown(consolidated_dates, unsafe_allow_html=False)

            # Technical Requirements Section
            st.subheader("🔧 Technical Requirements")
            with st.expander("View Technical Requirements", expanded=True):
                if not all_requirements:
                    st.markdown(
                        "No technical requirements found in any of the provided files."
                    )
                else:
                    consolidated_requirements = (
                        "Consolidated Technical Requirements:\n\n"
                    )
                    for i, file_id in enumerate(uploaded_file_ids):
                        file_name = file_id_to_name[file_id]
                        requirements_response = all_requirements[i]
                        if requirements_response.strip():
                            # Fix incorrect file references
                            requirements_response = replace_citations(
                                requirements_response,
                                file_id_to_name,
                                intended_file_name=file_name,
                            )
                            consolidated_requirements += (
                                f"Requirements from {file_name}:\n"
                            )
                            consolidated_requirements += (
                                requirements_response + "\n\n---\n\n"
                            )
                    st.markdown(consolidated_requirements, unsafe_allow_html=False)

            # Folder Structure Section
            st.subheader("📁 Required Folder Structure")
            with st.expander("View Folder Structure", expanded=True):
                if not all_folder_structures:
                    st.markdown(
                        "No folder structure specified in any of the provided files."
                    )
                else:
                    consolidated_folder_structure = (
                        "Consolidated Folder Structure for Tender Submission:\n\n"
                    )
                    for i, file_id in enumerate(uploaded_file_ids):
                        file_name = file_id_to_name[file_id]
                        folder_structure_response = all_folder_structures[i]
                        if folder_structure_response.strip():
                            # Fix incorrect file references
                            folder_structure_response = replace_citations(
                                folder_structure_response,
                                file_id_to_name,
                                intended_file_name=file_name,
                            )
                            consolidated_folder_structure += (
                                f"Folder Structure from {file_name}:\n"
                            )
                            consolidated_folder_structure += (
                                folder_structure_response + "\n\n---\n\n"
                            )
                    st.markdown(consolidated_folder_structure, unsafe_allow_html=False)

            # Download Full Report
            full_report = (
                "Tender Analysis Report\n\n"
                "## Important Dates and Milestones\n" + consolidated_dates + "\n\n"
                "## Tender Summary\n" + summary_response + "\n\n"
                "## Technical Requirements\n" + consolidated_requirements + "\n\n"
                "## Required Folder Structure\n" + consolidated_folder_structure
            )
            st.download_button(
                "📥 Download Full Report",
                full_report,
                file_name="tender_analysis_report.txt",
                mime="text/plain",
            )

            # Chat Interface
            st.subheader("💬 Chat with Assistant")
            if "thread_id" not in locals():
                st.info("Please upload and analyze a document first.")
            else:
                # Initialize chat history
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []

                # Display chat history
                for chat in st.session_state.chat_history:
                    st.markdown(
                        f"<div class='chat-message user-message'><strong>You:</strong> {chat['user']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div class='chat-message assistant-message'><strong>Assistant:</strong> {chat['assistant']}</div>",
                        unsafe_allow_html=True,
                    )

                # Chat input form
                with st.form(key="chat_form"):
                    user_query = st.text_area(
                        "Ask a question about the analyzed documents:", height=100
                    )
                    submit_button = st.form_submit_button("Send")

                    if submit_button and user_query.strip():
                        # Streamline loading indicator for chat as well
                        spinner_placeholder = st.empty()
                        if SIMULATION_MODE:
                            # Simulate chat response time (1 seconds)
                            with spinner_placeholder.container():
                                st.spinner("Generating response... (Status: mock)")
                            time.sleep(1)
                            assistant_response = (
                                "This is a mock chat response to your query: "
                                + user_query
                            )
                        else:
                            openai.beta.threads.messages.create(
                                thread_id=thread_id, role="user", content=user_query
                            )
                            run = openai.beta.threads.runs.create(
                                thread_id=thread_id,
                                assistant_id=ASSISTANT_ID.strip(),
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
                                time.sleep(0.5)  # Reduced polling interval
                            spinner_placeholder.empty()

                            messages = openai.beta.threads.messages.list(
                                thread_id=thread_id
                            )
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
                        st.rerun()  # Refresh to show updated chat history
