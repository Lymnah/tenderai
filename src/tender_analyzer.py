# tender_analyzer.py
import streamlit as st
import openai
import time
from config import SIMULATION_MODE, ASSISTANT_ID
from utils import load_mock_response, replace_citations
from pypdf import PdfReader
from io import BytesIO
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import os
from datetime import datetime
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    after_log,
)
from prompts import (
    DATES_PROMPT,
    REQUIREMENTS_PROMPT,
    FOLDER_STRUCTURE_PROMPT,
    SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    SYNTHESIZE_FOLDER_STRUCTURE_PROMPT,
    SYNTHESIZE_REQUIREMENTS_PROMPT,
    SYNTHESIZE_DATES_PROMPT,
    format_prompt,
)
from docx import Document

MAX_CONCURRENT_REQUESTS = 10
semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)

# Validate ASSISTANT_ID at the start of the module
if not isinstance(ASSISTANT_ID, str):
    raise ValueError(
        "ASSISTANT_ID must be a string, got: {}".format(type(ASSISTANT_ID))
    )
if not ASSISTANT_ID.strip():
    raise ValueError("ASSISTANT_ID cannot be empty or whitespace")

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# Function to initialize a new logger for each analysis run
def init_logger():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"analysis_{timestamp}.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger()


# Functions to log specific types of data
def log_raw_response(logger, task_name, response, source="AI"):
    logger.info(
        f"Raw response for {task_name} (Source: {source}):\n{response}\n{'-'*50}"
    )


def log_error(logger, message):
    logger.error(message)


# Retry callback to log each attempt
def log_retry(logger):
    def after_retry(retry_state):
        if retry_state.outcome.failed:
            attempt = retry_state.attempt_number
            wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
            error = retry_state.outcome.exception()
            logger.info(
                f"Retry attempt {attempt} for {retry_state.fn.__name__} failed with error: {str(error)}. "
                f"Waiting {wait_time:.2f} seconds before next attempt."
            )
        else:
            logger.info(
                f"Retry succeeded for {retry_state.fn.__name__} after {retry_state.attempt_number} attempts."
            )

    return after_retry


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(openai.RateLimitError),
    after=log_retry(logging.getLogger()),
)
def run_prompt(file_ids, prompt, task_name, logger):
    with semaphore:
        if SIMULATION_MODE:
            time.sleep(0.2)
            response = load_mock_response(task_name)
            log_raw_response(logger, task_name, response, source="Mock")
            return response
        else:
            try:
                thread = openai.beta.threads.create()
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=prompt,
                    attachments=[
                        {"file_id": fid, "tools": [{"type": "file_search"}]}
                        for fid in file_ids
                    ],
                )
                run = openai.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=ASSISTANT_ID.strip(),
                    tools=[{"type": "file_search"}],
                    temperature=0,
                    top_p=0,
                )
                while True:
                    run_status = openai.beta.threads.runs.retrieve(
                        thread_id=thread.id, run_id=run.id
                    )
                    if run_status.status == "completed":
                        break
                    elif run_status.status in ["failed", "cancelled"]:
                        error_msg = f"{task_name} failed: {run_status.status}"
                        log_error(logger, error_msg)
                        return error_msg
                    time.sleep(0.5)
                messages = openai.beta.threads.messages.list(thread_id=thread.id)
                response = "\n".join(
                    content.text.value
                    for msg in messages.data
                    if msg.role == "assistant"
                    for content in msg.content
                    if content.type == "text"
                )
                log_raw_response(logger, task_name, response, source="AI")
                return response if response else "No response generated."
            except Exception as e:
                error_msg = f"Error in {task_name}: {str(e)}"
                log_error(logger, error_msg)
                return error_msg


def generate_summary_in_batches(file_ids, file_id_to_name, logger, batch_size=10):
    """Generate summary in batches to respect attachment limits."""
    summaries = []
    for i in range(0, len(file_ids), batch_size):
        batch_file_ids = file_ids[i : i + batch_size]
        batch_summary = run_prompt(
            batch_file_ids, SUMMARY_PROMPT, "Tender Summary Batch", logger
        )
        summaries.append(batch_summary)
    # Combine batch summaries into a final summary
    final_summary = run_prompt(
        [],
        format_prompt(FINAL_SUMMARY_PROMPT, partial_summaries="\n\n".join(summaries)),
        "Final Tender Summary",
        logger,
    )
    return final_summary


def extract_dates_fallback(file_content, file_name):
    """Fallback date extraction using regex with improved sentence boundary detection."""
    import re
    import datetime

    date_patterns = [
        (r"\d{2}\.\d{2}\.\d{4}(?:\s+at\s+\d{1,2}h)?", "DD.MM.YYYY"),
        (r"\d{4}-\d{2}-\d{2}", "YYYY-MM-DD"),
        (
            r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
            "D Month YYYY",
        ),
        (
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
            "Month YYYY",
        ),
        (r"\d{1,2}/\d{1,2}/\d{4}", "DD/MM/YYYY"),
    ]
    dates = []
    matched_spans = []  # Track spans of matched dates to avoid duplicates
    month_map = {
        "january": "January",
        "february": "February",
        "march": "March",
        "april": "April",
        "may": "May",
        "june": "June",
        "july": "July",
        "august": "August",
        "september": "September",
        "october": "October",
        "november": "November",
        "december": "December",
    }

    def is_valid_date(date_str, pattern_type):
        """Validate if a date string represents a real date."""
        if pattern_type == "Month YYYY":
            month, year = date_str.split()
            year = int(year)
            return 1000 <= year <= 9999
        try:
            if pattern_type in ["DD.MM.YYYY", "DD/MM/YYYY"]:
                day, month, year = map(
                    int, date_str.split(" at ")[0].replace(".", "/").split("/")
                )
                datetime.datetime(year, month, day)
                return True
            elif pattern_type == "YYYY-MM-DD":
                year, month, day = map(int, date_str.split("-"))
                datetime.datetime(year, month, day)
                return True
            elif pattern_type == "D Month YYYY":
                parts = date_str.split()
                day, month, year = parts[0], parts[1], parts[2]
                day = int(day)
                year = int(year)
                month = month_map.get(month.lower(), month)
                month_num = list(month_map.values()).index(month) + 1
                datetime.datetime(year, month_num, day)
                return True
        except (ValueError, IndexError):
            return False
        return False

    for pattern, pattern_type in date_patterns:
        for match in re.finditer(pattern, file_content, re.IGNORECASE):
            start, end = match.start(), match.end()
            if any(
                m_start <= start < m_end or m_start < end <= m_end
                for m_start, m_end in matched_spans
            ):
                continue

            date = match.group()
            is_valid = is_valid_date(date, pattern_type)
            if not is_valid:
                if pattern_type == "D Month YYYY":
                    matched_spans.append((start, end))
                continue

            original_date = date
            for month_lower, month_proper in month_map.items():
                date = re.sub(
                    rf"\b{month_lower}\b", month_proper, date, flags=re.IGNORECASE
                )
            matched_spans.append((start, end))

            # Improved sentence boundary detection
            sentence_start = file_content.rfind(".", 0, start)
            if (
                sentence_start == -1
                or file_content[sentence_start:start].count("\n") > 0
            ):
                sentence_start = file_content.rfind("\n", 0, start)
            if sentence_start == -1:
                sentence_start = 0
            else:
                sentence_start += 1

            sentence_end = file_content.find(".", end)
            if sentence_end == -1 or file_content[end:sentence_end].count("\n") > 0:
                sentence_end = file_content.find("\n", end)
            if sentence_end == -1:
                sentence_end = len(file_content)

            context = (
                file_content[sentence_start:sentence_end].replace("\n", " ").strip()
            )

            # Clean up the context by removing only the matched date
            event = context.replace(original_date, "").strip()
            # Normalize spaces and remove punctuation
            event = re.sub(r"[.,!;\"'()[\]{}]+", " ", event).strip()
            event = re.sub(r"\s+", " ", event).strip()
            if event:
                dates.append(f"- {date}, {event}, Source: {file_name}")

    return "\n".join(dates) if dates else "NO_INFO_FOUND"


def extract_text_from_docx(file):
    """Extract text from a .docx file."""
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


def analyze_file_batch(
    batch_file_ids,
    file_id_to_name,
    progress_log_messages,
    lock,
    uploaded_files,
    batch_number,
    total_batches,
    total_files,
    files_text,
    logger,
    update_progress,
):
    batch_results = []
    batch_start = (batch_number - 1) * len(batch_file_ids) + 1
    batch_end = min(batch_start + len(batch_file_ids) - 1, total_files)
    batch_files = [file_id_to_name[file_id] for file_id in batch_file_ids]
    files_text.markdown(
        f"**Files being analyzed:** {', '.join(batch_files)} ({batch_start}-{batch_end} of {total_files})"
    )

    for file_id in batch_file_ids:
        file_name = file_id_to_name[file_id]
        dates_response = ""
        requirements_response = ""
        folder_structure_response = ""
        dates_source = "AI"  # Track the source of the dates

        with lock:
            progress_log_messages.append(f"Analyzing {file_name}...")

        # Define analysis tasks
        def analyze_task(file_id, prompt, task_name):
            try:
                return run_prompt([file_id], prompt, task_name, logger)
            except Exception as e:
                error_msg = f"Error analyzing {task_name} in {file_name}: {str(e)}"
                log_error(logger, error_msg)
                return error_msg

        # Run tasks in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            dates_future = executor.submit(
                analyze_task,
                file_id,
                format_prompt(DATES_PROMPT, file_name=file_name),
                f"Dates for {file_name}",
            )
            requirements_future = executor.submit(
                analyze_task,
                file_id,
                REQUIREMENTS_PROMPT,
                f"Requirements for {file_name}",
            )
            folder_structure_future = executor.submit(
                analyze_task,
                file_id,
                format_prompt(FOLDER_STRUCTURE_PROMPT, file_name=file_name),
                f"Folder Structure for {file_name}",
            )

            # Collect results and update progress for each task
            dates_response = dates_future.result()
            update_progress(f"Completed Dates for {file_name}", increment=True)
            requirements_response = requirements_future.result()
            update_progress(f"Completed Requirements for {file_name}", increment=True)
            folder_structure_response = folder_structure_future.result()
            update_progress(
                f"Completed Folder Structure for {file_name}", increment=True
            )

        # Fallback for dates if AI returns NO_INFO_FOUND
        if "NO_INFO_FOUND" in dates_response:
            for file in uploaded_files:
                if file.name == file_name:
                    if file.name.lower().endswith(".pdf"):
                        pdf_reader = PdfReader(BytesIO(file.getvalue()))
                        file_content = "\n".join(
                            page.extract_text() or "" for page in pdf_reader.pages
                        )
                        dates_response = extract_dates_fallback(file_content, file_name)
                        dates_source = "Fallback"
                    elif file.name.lower().endswith(".docx"):
                        file_content = extract_text_from_docx(BytesIO(file.getvalue()))
                        dates_response = extract_dates_fallback(file_content, file_name)
                        dates_source = "Fallback"
                    break
            # Add a subtle marker (zero-width space) to indicate fallback
            if (
                dates_source == "Fallback"
                and dates_response
                and dates_response != "NO_INFO_FOUND"
            ):
                dates_response += "[fallback]"

        # Replace citations
        dates_response = replace_citations(dates_response, file_id_to_name)
        requirements_response = replace_citations(
            requirements_response, file_id_to_name
        )
        folder_structure_response = replace_citations(
            folder_structure_response, file_id_to_name
        )

        # Log the source of the dates
        log_raw_response(
            logger, f"Dates for {file_name}", dates_response, source=dates_source
        )

        batch_results.append(
            (dates_response, requirements_response, folder_structure_response)
        )
    return batch_results


def analyze_tender(
    uploaded_file_ids,
    file_id_to_name,
    progress_bar,
    status_text,
    files_text,
    uploaded_files,
    total_files,
):
    """Analyze tender documents in batches and update progress."""
    logger = init_logger()
    batch_size = 3
    total_batches = (len(uploaded_file_ids) + batch_size - 1) // batch_size
    total_tasks = len(uploaded_file_ids) * 3 + 1  # 3 tasks per file + summary
    current_task = 0
    progress_log_messages = []
    all_dates = []
    all_requirements = []
    all_folder_structures = []
    lock = threading.Lock()

    def update_progress(message, increment=True):
        nonlocal current_task
        with lock:
            if increment:
                current_task += 1
            progress = min(current_task / total_tasks, 1.0)
            progress_bar.progress(progress)
            status_text.text(message)
            msg = f"[{time.strftime('%H:%M:%S')}] {message}"
            progress_log_messages.append(msg)

    # Process files in batches
    for i in range(0, len(uploaded_file_ids), batch_size):
        batch_number = i // batch_size + 1
        batch_file_ids = uploaded_file_ids[i : i + batch_size]
        batch_start = i + 1
        batch_end = min(i + batch_size, total_files)
        # Update status without incrementing task
        update_progress(
            f"Starting analysis for files {batch_start}-{batch_end} of {total_files} (Batch {batch_number}/{total_batches})",
            increment=False,
        )

        batch_results = analyze_file_batch(
            batch_file_ids,
            file_id_to_name,
            progress_log_messages,
            lock,
            uploaded_files,
            batch_number,
            total_batches,
            total_files,
            files_text,
            logger,
            update_progress,
        )
        for dates, requirements, folder_structure in batch_results:
            all_dates.append(dates)
            all_requirements.append(requirements)
            all_folder_structures.append(folder_structure)

    # Summary task
    update_progress("Generating tender summary...", increment=True)
    try:
        if len(uploaded_file_ids) > 10:
            summary_response = generate_summary_in_batches(
                uploaded_file_ids, file_id_to_name, logger
            )
        else:
            summary_response = run_prompt(
                uploaded_file_ids, SUMMARY_PROMPT, "Tender Summary", logger
            )
    except Exception as e:
        error_msg = f"Error generating summary: {str(e)}"
        log_error(logger, error_msg)
        summary_response = error_msg
    summary_response = replace_citations(summary_response, file_id_to_name)
    update_progress("Analysis complete", increment=True)

    # Clean up OpenAI files
    for file_id in uploaded_file_ids:
        try:
            openai.files.delete(file_id)
        except Exception as e:
            st.warning(f"Failed to delete file {file_id}: {str(e)}")
            log_error(logger, f"Failed to delete file {file_id}: {str(e)}")

    return (
        all_dates,
        all_requirements,
        all_folder_structures,
        summary_response,
        progress_log_messages,
    )


def synthesize_results(
    all_dates,
    all_requirements,
    all_folder_structures,
    uploaded_file_ids,
    file_id_to_name,
    logger,
):
    """Synthesize per-file analysis results into consolidated outputs."""
    # Synthesize dates
    dates_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{dates}"
            for file_id, dates in zip(uploaded_file_ids, all_dates)
            if dates.strip() and dates.strip() != "NO_INFO_FOUND"
        ]
    )
    if dates_data:
        synthesized_dates = run_prompt(
            [],
            format_prompt(SYNTHESIZE_DATES_PROMPT, dates_data=dates_data),
            "Synthesize Dates",
            logger,
        )
    else:
        synthesized_dates = "NO_INFO_FOUND"

    # Synthesize requirements
    requirements_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{reqs}"
            for file_id, reqs in zip(uploaded_file_ids, all_requirements)
            if reqs.strip() and reqs.strip() != "NO_INFO_FOUND"
        ]
    )
    if requirements_data:
        synthesized_requirements = run_prompt(
            [],
            format_prompt(
                SYNTHESIZE_REQUIREMENTS_PROMPT, requirements_data=requirements_data
            ),
            "Synthesize Requirements",
            logger,
        )
    else:
        synthesized_requirements = "NO_INFO_FOUND"

    # Synthesize folder structures
    folder_structure_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{struct}"
            for file_id, struct in zip(uploaded_file_ids, all_folder_structures)
            if struct.strip() and struct.strip() != "NO_INFO_FOUND"
        ]
    )
    if folder_structure_data:
        synthesized_folder_structure = run_prompt(
            [],
            format_prompt(
                SYNTHESIZE_FOLDER_STRUCTURE_PROMPT,
                folder_structure_data=folder_structure_data,
            ),
            "Synthesize Folder Structure",
            logger,
        )
    else:
        synthesized_folder_structure = "NO_INFO_FOUND"

    return {
        "synthesized_dates": synthesized_dates,
        "synthesized_requirements": synthesized_requirements,
        "synthesized_folder_structure": synthesized_folder_structure,
    }
