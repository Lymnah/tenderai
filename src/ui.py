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


def clean_dates_response(response, file_name):
    """Clean up the dates response by removing 'No important dates found' if dates are present."""
    lines = response.split("\n")
    cleaned_lines = []
    no_dates_message = (
        f"No important dates, milestones, or deadlines found in {file_name}."
    )
    has_dates = False

    # First pass: Check if there are any dates (lines that look like date entries)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Broadened regex to match various date formats:
        # - DD.MM.YYYY (e.g., "21.04.2021")
        # - YYYY-MM-DD (e.g., "2021-04-21")
        # - Month DD, YYYY (e.g., "April 21, 2021")
        # - Month YYYY (e.g., "May 2021")
        # - DD Month YYYY (e.g., "21 April 2021")
        if (
            re.match(
                r"^\d{2}\.\d{2}\.\d{4}|^\d{4}-\d{2}-\d{2}|^\w+\s+\d{1,2},\s+\d{4}|^\w+\s+\d{4}|^\d{1,2}\s+\w+\s+\d{4}",
                line,
            )
            or "Source:" in line
            or any(
                keyword in line.lower()
                for keyword in [
                    "deadline",
                    "milestone",
                    "date",
                    "schedule",
                    "due",
                    "submission",
                    "contract",
                ]
            )
        ):
            has_dates = True
            break

    # Second pass: Build the cleaned response
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip "No important dates" message if dates were found
        if no_dates_message in line and has_dates:
            continue
        cleaned_lines.append(line)

    # If no dates were found and the "No important dates" message is not already in the response, add it
    if not has_dates and no_dates_message not in cleaned_lines:
        cleaned_lines.append(no_dates_message)

    return "\n".join(cleaned_lines)


def clean_summary_response(response):
    """Clean up the summary response by consolidating repeated citations."""
    # Find all citations in the format 【file_name】
    citations = re.findall(r"【.*?】", response)
    if not citations:
        return response

    # Get unique citations
    unique_citations = []
    seen = set()
    for citation in citations:
        if citation not in seen:
            unique_citations.append(citation)
            seen.add(citation)

    # Remove all citations from the response
    response_without_citations = re.sub(r"【.*?】", "", response).strip()

    # Add consolidated citations at the end
    if unique_citations:
        consolidated_citations = " ".join(unique_citations)
        response = (
            f"{response_without_citations}\n\n**Sources:** {consolidated_citations}"
        )
    else:
        response = response_without_citations

    return response


def render_main_content(
    uploaded_files, uploaded_file_ids, file_id_to_name, thread_id, analysis_results
):
    # Extract analysis results from session state
    all_dates = analysis_results["all_dates"]
    all_requirements = analysis_results["all_requirements"]
    all_folder_structures = analysis_results["all_folder_structures"]
    summary_response = analysis_results["summary_response"]
    progress_log_messages = analysis_results["progress_log_messages"]

    # Display Results in Dedicated Sections
    st.header("📊 Tender Analysis Results", divider=True)

    # Tender Summary Section
    st.subheader("📝 Tender Summary")
    with st.expander("View Tender Summary", expanded=True):
        # Clean up the summary response
        cleaned_summary = clean_summary_response(summary_response)
        st.markdown(cleaned_summary, unsafe_allow_html=False)

    # Important Dates Section
    st.subheader("🕒 Important Dates and Milestones")
    with st.expander("View Dates and Milestones", expanded=True):
        if not all_dates:
            st.markdown("No important dates found in any of the provided files.")
        else:
            consolidated_dates = "Consolidated Important Dates and Milestones:\n\n"
            for i, file_id in enumerate(uploaded_file_ids):
                file_name = file_id_to_name[file_id]
                dates_response = all_dates[i] if i < len(all_dates) else ""
                if dates_response.strip():
                    # Fix incorrect file references
                    dates_response = replace_citations(
                        dates_response,
                        file_id_to_name,
                        intended_file_name=file_name,
                    )
                    # Clean up "No important dates found" messages
                    cleaned_response = clean_dates_response(dates_response, file_name)
                    consolidated_dates += f"Dates from {file_name}:\n"
                    consolidated_dates += cleaned_response + "\n\n---\n\n"
            st.markdown(consolidated_dates, unsafe_allow_html=False)

    # Technical Requirements Section
    st.subheader("🔧 Technical Requirements")
    with st.expander("View Technical Requirements", expanded=True):
        if not all_requirements:
            st.markdown("No technical requirements found in any of the provided files.")
        else:
            consolidated_requirements = "Consolidated Technical Requirements:\n\n"
            for i, file_id in enumerate(uploaded_file_ids):
                file_name = file_id_to_name[file_id]
                requirements_response = (
                    all_requirements[i] if i < len(all_requirements) else ""
                )
                if requirements_response.strip():
                    # Fix incorrect file references
                    requirements_response = replace_citations(
                        requirements_response,
                        file_id_to_name,
                        intended_file_name=file_name,
                    )
                    consolidated_requirements += f"Requirements from {file_name}:\n"
                    consolidated_requirements += requirements_response + "\n\n---\n\n"
            st.markdown(consolidated_requirements, unsafe_allow_html=False)

    # Folder Structure Section
    st.subheader("📁 Required Folder Structure")
    with st.expander("View Folder Structure", expanded=True):
        if not all_folder_structures:
            st.markdown("No folder structure specified in any of the provided files.")
        else:
            consolidated_folder_structure = (
                "Consolidated Folder Structure for Tender Submission:\n\n"
            )
            for i, file_id in enumerate(uploaded_file_ids):
                file_name = file_id_to_name[file_id]
                folder_structure_response = (
                    all_folder_structures[i] if i < len(all_folder_structures) else ""
                )
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
        "## Tender Summary\n" + cleaned_summary + "\n\n"
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
                        "This is a mock chat response to your query: " + user_query
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
                st.rerun()  # Refresh to show updated chat history
