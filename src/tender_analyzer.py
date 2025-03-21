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

        # Log the file_ids being sent
        print(f"Sending prompt for {task_name} with file_ids: {file_ids}")

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

        # Extract text content and log non-text content
        response_parts = []
        for msg in assistant_responses:
            for content in msg.content:
                if content.type == "text":
                    response_parts.append(content.text.value)
                else:
                    print(f"Non-text content found in {task_name}: {content.type}")
        response = "\n".join(response_parts)

        # Log the raw response for debugging
        print(f"Raw OpenAI response for {task_name}:\n{response}\n---")

        return response


def analyze_tender(
    uploaded_file_ids,
    file_id_to_name,
    progress_bar,
    status_text,
    progress_log_placeholder,
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
        # Update the progress log in the placeholder
        progress_log_placeholder.markdown(
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
        dates_prompt = f"""
        You are processing the file "{file_name}". This is the only file you should analyze for this task. Do not reference or consider any other files. Extract all important dates, milestones, and deadlines from this tender document. Include the following details for each entry:
        - The specific date and time (if available, otherwise state "No specific time mentioned").
        - The time zone (infer if not specified, e.g., CET/CEST for Swiss documents; if unable to infer, state "No specific time zone provided").
        - The purpose or event associated with the date or milestone (e.g., submission deadline, site visit, contract start).
        - The source file where the information was found (cite explicitly as "{file_name}").
        Format the output as a list, with each entry on a new line, strictly in the format:
        - [date and time], [time zone], [event], Source: [file name]
        For example:
        - 21.04.2021, No specific time zone provided, Deadline for submitting questions, Source: {file_name}
        - 30.04.2021 at 12:00, No specific time zone provided, Deadline for submitting offers, Source: {file_name}
        Each date must be on a separate line, and the format must be followed exactly. Do not combine dates into a single line or deviate from the specified format.
        If no dates, milestones, or deadlines are found, state exactly: "No important dates, milestones, or deadlines found in {file_name}." and nothing else. Do not include this message if any dates are found.
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
        For each category, provide a detailed list of the requirements. If a category has no requirements, state: "[Category] requirements not found in [file name]."
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
        If no folder structure is specified, state: "No folder structure specified in {file_name}."
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
    Provide a holistic summary of the tender based on all the provided documents. Focus on the following aspects and present them as a structured list with bullet points:
    - **Purpose**: The overall purpose of the tender.
    - **Main Deliverables**: The main deliverables or services required.
    - **Key Objectives**: Any key objectives or priorities mentioned.
    - **Scope and Scale**: A brief overview of the scope and scale of the project.
    - **Key Dates**: Important dates or deadlines (e.g., submission deadline, contract signing).
    - **Submission Requirements**: Key requirements for submitting the offer (e.g., documents, format).
    Cite the source files where relevant, using the format [file name] after each bullet point where applicable. If a bullet point applies to multiple files, consolidate the citations into a single reference at the end of the bullet point. Do not repeat the same citation multiple times for the same point.
    Format the output as a concise list (150-200 words total), with each bullet point on a new line.
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

    return (
        all_dates,
        all_requirements,
        all_folder_structures,
        summary_response,
        progress_log_messages,
    )
