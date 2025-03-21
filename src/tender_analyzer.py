# tender_analyzer.py
import streamlit as st
import openai
import time
from config import SIMULATION_MODE, ASSISTANT_ID
from utils import load_mock_response, replace_citations


def run_prompt(
    file_ids,
    prompt,
    task_name,
    progress_callback=None,
    total_tasks=None,
    current_task=None,
):
    if SIMULATION_MODE:
        time.sleep(0.2)  # Simulate processing time
        return load_mock_response(task_name)
    else:
        # Create a new thread for each prompt to avoid message accumulation
        thread = openai.beta.threads.create()
        thread_id = thread.id

        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
            attachments=[
                {"file_id": file_id, "tools": [{"type": "file_search"}]}
                for file_id in file_ids
            ],
        )
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID.strip(),
            tools=[{"type": "file_search"}],
        )
        spinner_placeholder = st.empty()
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )
            with spinner_placeholder.container():
                st.spinner(f"Processing {task_name}... (Status: {run_status.status})")
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled"]:
                st.error(f"{task_name} failed with status: {run_status.status}")
                return "No response generated."
            time.sleep(0.5)  # Reduced polling interval
        spinner_placeholder.empty()
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        assistant_responses = [msg for msg in messages.data if msg.role == "assistant"]
        if not assistant_responses:
            return "No response generated."
        response = "\n".join(
            content.text.value
            for msg in assistant_responses
            for content in msg.content
            if content.type == "text"
        )
        # Log the raw response for debugging
        return response


def analyze_tender(
    uploaded_file_ids, file_id_to_name, progress_bar, status_text, progress_log
):
    # Double the total tasks to account for both "Looking for..." and "Completed..." updates
    total_tasks = (
        len(uploaded_file_ids) * 3 + 1
    ) * 2  # 3 tasks per file + 1 summary, 2 updates per task
    current_task = 0
    progress_log_messages = []

    def update_progress(progress, message):
        nonlocal current_task, progress_log_messages
        current_task += 1
        progress = min(progress, 1.0)  # Clamp progress to [0.0, 1.0]
        progress_bar.progress(progress)
        status_text.text(message)
        progress_log_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        progress_log.markdown(
            "<div class='progress-log'>"
            + "<br>".join(progress_log_messages)
            + "</div>",
            unsafe_allow_html=True,
        )

    all_dates = []
    all_requirements = []
    all_folder_structures = []

    for file_id in uploaded_file_ids:
        file_name = file_id_to_name[file_id]

        # Dates extraction
        update_progress(
            current_task / total_tasks, f"Looking for dates in {file_name}..."
        )
        dates_prompt = """
        Extract all important dates, milestones, and deadlines from the provided tender document. Include the following details for each date:
        - The specific date and time (if available).
        - The time zone (infer if not specified, e.g., CET/CEST for Swiss documents).
        - The purpose or event associated with the date (e.g., submission deadline, site visit, contract start).
        - The source file where the date was found (cite explicitly).
        Format the output as a list, with each entry in the format:
        - Date: [date and time], Time Zone: [time zone], Event: [event], Source: [file name]
        If no dates are found, state: "No important dates found in [file name]."
        """
        dates_response = run_prompt([file_id], dates_prompt, f"Dates for {file_name}")
        dates_response = replace_citations(dates_response, file_id_to_name)
        all_dates.append(dates_response)
        update_progress(current_task / total_tasks, f"Completed Dates for {file_name}")

        # Requirements extraction
        update_progress(
            current_task / total_tasks, f"Looking for requirements in {file_name}..."
        )
        requirements_prompt = """
        Extract the technical requirements from the provided tender document. Categorize the requirements as follows:
        - Mandatory Requirements: List all requirements that must be met.
        - Optional Requirements: List any requirements that are not mandatory.
        - Legal Requirements: List any legal or regulatory requirements.
        - Financial Requirements: List any financial requirements (e.g., budget, payment terms).
        - Security Requirements: List any security-related requirements.
        - Certifications: List any required certifications or qualifications.
        For each category, provide a detailed list of the requirements, citing the source file explicitly. If a category has no requirements, state: "[Category] requirements not found in [file name]."
        Format the output with clear headings for each category.
        """
        requirements_response = run_prompt(
            [file_id], requirements_prompt, f"Requirements for {file_name}"
        )
        requirements_response = replace_citations(
            requirements_response, file_id_to_name
        )
        all_requirements.append(requirements_response)
        update_progress(
            current_task / total_tasks, f"Completed Requirements for {file_name}"
        )

        # Folder structure extraction
        update_progress(
            current_task / total_tasks,
            f"Looking for folder structure in {file_name}...",
        )
        folder_structure_prompt = """
        Extract the required folder structure for tender submission from the provided document. Include the following details:
        - The exact folder and subfolder structure as specified in the tender.
        - The documents that must be included in each folder or subfolder.
        - Cite the source file explicitly.
        Format the output as a hierarchical list, e.g.:
        - Main Folder
          - Subfolder 1: [Document 1], [Document 2]
          - Subfolder 2: [Document 3]
        If no folder structure is specified, state: "No folder structure specified in [file name]."
        Ensure the output is accurate and does not include any hallucinated information.
        """
        folder_structure_response = run_prompt(
            [file_id], folder_structure_prompt, f"Folder Structure for {file_name}"
        )
        folder_structure_response = replace_citations(
            folder_structure_response, file_id_to_name
        )
        all_folder_structures.append(folder_structure_response)
        update_progress(
            current_task / total_tasks, f"Completed Folder Structure for {file_name}"
        )

    # Summary extraction
    update_progress(current_task / total_tasks, "Generating tender summary...")
    summary_prompt = """
    Provide a holistic summary of the tender based on all the provided documents. Focus on what the client is asking for, including:
    - The overall purpose of the tender.
    - The main deliverables or services required.
    - Any key objectives or priorities mentioned.
    - A brief overview of the scope and scale of the project.
    Synthesize the information from all files to create a cohesive summary. Cite the source files where relevant. Format the output as a concise paragraph (150-200 words).
    """
    summary_response = run_prompt(uploaded_file_ids, summary_prompt, "Tender Summary")
    summary_response = replace_citations(summary_response, file_id_to_name)
    update_progress(current_task / total_tasks, "Completed Tender Summary")

    # Delete the files from OpenAI after all tasks are complete
    for file_id in uploaded_file_ids:
        try:
            openai.files.delete(file_id)
        except Exception as e:
            st.warning(f"Failed to delete file {file_id}: {str(e)}")

    return all_dates, all_requirements, all_folder_structures, summary_response
