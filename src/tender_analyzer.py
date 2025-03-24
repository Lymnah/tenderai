# tender_analyzer.py
import streamlit as st
import openai
import time
from config import SIMULATION_MODE, ASSISTANT_ID
from utils import load_mock_response, replace_citations
import PyPDF2
from io import BytesIO
import re


def run_prompt(
    file_ids,
    prompt,
    task_name,
    progress_callback=None,
    total_tasks=None,
    current_task=None,
):
    """Run a prompt with OpenAI or simulate a response."""
    if SIMULATION_MODE:
        time.sleep(0.2)
        return load_mock_response(task_name)
    else:
        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
            attachments=[
                {"file_id": fid, "tools": [{"type": "file_search"}]} for fid in file_ids
            ],
        )
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID.strip(),
            tools=[{"type": "file_search"}],
        )
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled"]:
                return f"{task_name} failed: {run_status.status}"
            time.sleep(0.5)
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        response = "\n".join(
            content.text.value
            for msg in messages.data
            if msg.role == "assistant"
            for content in msg.content
            if content.type == "text"
        )
        return response if response else "No response generated."


def extract_dates_fallback(file_content, file_name):
    """Fallback date extraction using regex."""
    date_patterns = [
        r"\d{2}\.\d{2}\.\d{4}",  # DD.MM.YYYY
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
    ]
    dates = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, file_content, re.IGNORECASE):
            dates.append(f"- {match.group()}, Source: {file_name}")
    return (
        "\n".join(dates)
        or f"No important dates, milestones, or deadlines found in {file_name}."
    )


def analyze_tender(uploaded_file_ids, file_id_to_name, progress_bar, status_text):
    """Analyze tender documents and update progress."""
    total_tasks = len(uploaded_file_ids) * 3 + 1  # 3 tasks per file + summary
    current_task = 0
    progress_log_messages = []
    all_dates, all_requirements, all_folder_structures = [], [], []

    def update_progress(message):
        nonlocal current_task
        current_task += 1
        progress = min(current_task / total_tasks, 1.0)
        progress_bar.progress(progress)
        status_text.text(message)
        msg = f"[{time.strftime('%H:%M:%S')}] {message}"
        progress_log_messages.append(msg)

    for file_id in uploaded_file_ids:
        file_name = file_id_to_name[file_id]

        # Dates
        update_progress(f"Looking for dates in {file_name}...")
        dates_prompt = f"""
        Extract all important dates, milestones, and deadlines from "{file_name}".
        Format each as: - [date and time], [time zone], [event], Source: {file_name}
        E.g., - 21.04.2021, CET, Submission deadline, Source: {file_name}
        If none found, return: "No important dates, milestones, or deadlines found in {file_name}."
        """
        dates_response = run_prompt([file_id], dates_prompt, f"Dates for {file_name}")
        if "No important dates" in dates_response:
            for file in st.session_state.uploaded_files:
                if file.name == file_name and file.name.endswith(".pdf"):
                    pdf_reader = PyPDF2.PdfReader(BytesIO(file.getvalue()))
                    file_content = "\n".join(
                        page.extract_text() or "" for page in pdf_reader.pages
                    )
                    dates_response = extract_dates_fallback(file_content, file_name)
                    break
        all_dates.append(replace_citations(dates_response, file_id_to_name))

        # Requirements
        update_progress(f"Looking for requirements in {file_name}...")
        requirements_prompt = """
        Extract technical requirements from the tender document, categorized as:
        - Mandatory Requirements
        - Optional Requirements
        - Legal Requirements
        - Financial Requirements
        - Security Requirements
        - Certifications
        List details under each. If none in a category, state: "[Category] requirements not found in [file name]."
        """
        requirements_response = run_prompt(
            [file_id], requirements_prompt, f"Requirements for {file_name}"
        )
        all_requirements.append(
            replace_citations(requirements_response, file_id_to_name)
        )

        # Folder Structure
        update_progress(f"Looking for folder structure in {file_name}...")
        folder_structure_prompt = """
        Extract the required folder structure for tender submission from "{file_name}".
        Format as a hierarchical list, e.g.:
        - Main Folder
          - Subfolder 1: [Document 1]
        If none, return: "No folder structure specified in {file_name}."
        """
        folder_structure_response = run_prompt(
            [file_id], folder_structure_prompt, f"Folder Structure for {file_name}"
        )
        all_folder_structures.append(
            replace_citations(folder_structure_response, file_id_to_name)
        )

    # Summary
    update_progress("Generating tender summary...")
    summary_prompt = """
    Summarize the tender across all documents:
    - **Purpose**: Overall purpose
    - **Main Deliverables**: Key deliverables
    - **Key Objectives**: Objectives or priorities
    - **Scope and Scale**: Project scope
    - **Key Dates**: Important dates
    - **Submission Requirements**: Submission needs
    Cite sources as [file name] where applicable.
    """
    summary_response = run_prompt(uploaded_file_ids, summary_prompt, "Tender Summary")
    summary_response = replace_citations(summary_response, file_id_to_name)

    # Clean up OpenAI files
    for file_id in uploaded_file_ids:
        try:
            openai.files.delete(file_id)
        except Exception as e:
            st.warning(f"Failed to delete file {file_id}: {str(e)}")

    return (
        all_dates,
        all_requirements,
        all_folder_structures,
        summary_response,
        progress_log_messages,
    )
