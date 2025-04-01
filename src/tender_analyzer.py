# tender_analyzer.py

MAX_CONCURRENT_REQUESTS = 5
MAX_THREAD_WORKERS = 4
BATCH_SIZE = 4

import streamlit as st
import openai
import time
from config import ASSISTANT_ID
from utils import load_mock_response, replace_citations
from pypdf import PdfReader
from io import BytesIO
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
    CLIENT_INFO_PROMPT,
    DATES_PROMPT,
    REQUIREMENTS_PROMPT,
    FOLDER_STRUCTURE_PROMPT,
    SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    SYNTHESIZE_CLIENT_INFO_PROMPT,
    SYNTHESIZE_FOLDER_STRUCTURE_PROMPT,
    SYNTHESIZE_REQUIREMENTS_PROMPT,
    SYNTHESIZE_DATES_PROMPT,
    format_prompt,
)
from docx import Document

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
    # Truncate response to 1000 characters to avoid log truncation
    if len(response) > 1000:
        response = response[:1000] + "... (truncated)"
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
    retry=retry_if_exception_type(
        (openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError)
    ),
    after=log_retry(logging.getLogger()),
)
def run_prompt(file_ids, prompt, task_name, logger, simulation_mode):
    with semaphore:
        if simulation_mode:
            response = load_mock_response(task_name)
            log_raw_response(logger, task_name, response, source="Mock")
            return response, {}
        else:
            try:
                # Create a thread
                thread = openai.beta.threads.create()

                # Create a message in the thread
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=prompt,
                    attachments=[
                        {"file_id": fid, "tools": [{"type": "file_search"}]}
                        for fid in file_ids
                    ],
                )

                # Create a run
                run = openai.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=ASSISTANT_ID.strip(),
                    tools=[{"type": "file_search"}],
                )

                # Poll the run status
                while True:
                    run_status_response = openai.beta.threads.runs.retrieve(
                        thread_id=thread.id, run_id=run.id
                    )
                    if run_status_response.status == "completed":
                        break
                    elif run_status_response.status in ["failed", "cancelled"]:
                        error_msg = f"{task_name} failed with status: {run_status_response.status}"
                        log_error(logger, error_msg)
                        return error_msg, {}
                    time.sleep(1)

                # Retrieve messages with raw response to access headers
                raw_response = openai.beta.threads.messages.with_raw_response.list(
                    thread_id=thread.id
                )
                messages_response = (
                    raw_response.parse()
                )  # Parse to get SyncCursorPage[Message]
                response_headers = (
                    raw_response.headers
                )  # Access headers from LegacyAPIResponse

                # Extract the assistant's response
                response = "\n".join(
                    content.text.value
                    for msg in messages_response.data
                    if msg.role == "assistant"
                    for content in msg.content
                    if content.type == "text"
                )
                log_raw_response(logger, task_name, response, source="AI")

                # Extract rate limit headers
                rate_limit_headers = {
                    "remaining_requests": response_headers.get(
                        "x-ratelimit-remaining-requests", "N/A"
                    ),
                    "limit_requests": response_headers.get(
                        "x-ratelimit-limit-requests", "N/A"
                    ),
                    "reset_requests": response_headers.get(
                        "x-ratelimit-reset-requests", "N/A"
                    ),
                    "remaining_tokens": response_headers.get(
                        "x-ratelimit-remaining-tokens", "N/A"
                    ),
                    "limit_tokens": response_headers.get(
                        "x-ratelimit-limit-tokens", "N/A"
                    ),
                    "reset_tokens": response_headers.get(
                        "x-ratelimit-reset-tokens", "N/A"
                    ),
                }
                logger.info(f"Rate limit info for {task_name}: {rate_limit_headers}")

                return (
                    response if response else "No response generated."
                ), rate_limit_headers

            except openai.APIError as e:
                if isinstance(e, openai.RateLimitError):
                    retry_after = getattr(e, "headers", {}).get("Retry-After", "N/A")
                    error_msg = f"OpenAI API request exceeded rate limit in {task_name}: {str(e)}, Retry-After: {retry_after}s"
                else:
                    error_msg = (
                        f"OpenAI API returned an API Error in {task_name}: {str(e)}"
                    )
                log_error(logger, error_msg)
                return error_msg, {}
            except Exception as e:
                error_msg = f"Unexpected error in {task_name}: {str(e)}"
                log_error(logger, error_msg)
                return error_msg, {}


def generate_summary_in_batches(
    file_ids,
    file_id_to_name,
    logger,
    all_dates,
    all_requirements,
    batch_size=10,
    simulation_mode=False,
):
    summaries = []
    for i in range(0, len(file_ids), batch_size):
        batch_file_ids = file_ids[i : i + batch_size]
        batch_summary, _ = run_prompt(
            batch_file_ids,
            SUMMARY_PROMPT,
            "Tender Summary Batch",
            logger,
            simulation_mode,
        )
        summaries.append(batch_summary)

    dates_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{dates}"
            for file_id, dates in zip(file_ids, all_dates)
            if dates.strip() and dates.strip() != "NO_INFO_FOUND"
        ]
    )
    synthesized_dates, _ = (
        run_prompt(
            [],
            format_prompt(SYNTHESIZE_DATES_PROMPT, dates_data=dates_data),
            "Synthesize Dates for Summary",
            logger,
            simulation_mode,
        )
        if dates_data
        else ("NO_INFO_FOUND", {})
    )

    requirements_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{reqs}"
            for file_id, reqs in zip(file_ids, all_requirements)
            if reqs.strip() and reqs.strip() != "NO_INFO_FOUND"
        ]
    )
    synthesized_requirements, _ = (
        run_prompt(
            [],
            format_prompt(
                SYNTHESIZE_REQUIREMENTS_PROMPT, requirements_data=requirements_data
            ),
            "Synthesize Requirements for Summary",
            logger,
            simulation_mode,
        )
        if requirements_data
        else ("NO_INFO_FOUND", {})
    )

    final_summary, _ = run_prompt(
        [],
        format_prompt(
            FINAL_SUMMARY_PROMPT,
            partial_summaries="\n\n".join(summaries),
            synthesized_dates=synthesized_dates,
            synthesized_requirements=synthesized_requirements,
        ),
        "Final Tender Summary",
        logger,
        simulation_mode,
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
    simulation_mode,
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
        logger.info(f"Starting analysis for {file_name}")

        with lock:
            progress_log_messages.append(f"Analyzing {file_name}...")

        def analyze_task(file_id, prompt, task_name, simulation_mode):
            try:
                response, rate_limit_headers = run_prompt(
                    [file_id], prompt, task_name, logger, simulation_mode
                )
                # Log rate limit headers for monitoring
                try:
                    remaining_requests = rate_limit_headers.get(
                        "remaining_requests", "N/A"
                    )
                    remaining_tokens = rate_limit_headers.get("remaining_tokens", "N/A")
                    if remaining_requests != "N/A":
                        remaining_requests = int(remaining_requests)
                        if remaining_requests < 50:
                            warning_msg = f"Low remaining requests: {remaining_requests} for {task_name}"
                            logger.warning(warning_msg)
                            with lock:
                                progress_log_messages.append(warning_msg)
                    if remaining_tokens != "N/A":
                        remaining_tokens = int(remaining_tokens)
                        if remaining_tokens < 10000:
                            warning_msg = f"Low remaining tokens: {remaining_tokens} for {task_name}"
                            logger.warning(warning_msg)
                            with lock:
                                progress_log_messages.append(warning_msg)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not parse rate limit headers for {task_name}: {rate_limit_headers}"
                    )
                return response
            except Exception as e:
                error_msg = f"Error analyzing {task_name} in {file_name}: {str(e)}"
                log_error(logger, error_msg)
                return error_msg

        with ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
            futures = {
                "dates": executor.submit(
                    analyze_task,
                    file_id,
                    format_prompt(DATES_PROMPT, file_name=file_name),
                    f"Dates for {file_name}",
                    simulation_mode,
                ),
                "requirements": executor.submit(
                    analyze_task,
                    file_id,
                    REQUIREMENTS_PROMPT,
                    f"Requirements for {file_name}",
                    simulation_mode,
                ),
                "folder_structure": executor.submit(
                    analyze_task,
                    file_id,
                    format_prompt(FOLDER_STRUCTURE_PROMPT, file_name=file_name),
                    f"Folder Structure for {file_name}",
                    simulation_mode,
                ),
                "client_info": executor.submit(
                    analyze_task,
                    file_id,
                    format_prompt(CLIENT_INFO_PROMPT, file_name=file_name),
                    f"Client Info for {file_name}",
                    simulation_mode,
                ),
            }

            results = {
                "dates": "",
                "requirements": "",
                "folder_structure": "",
                "client_info": "",
            }
            for future in as_completed(futures.values()):
                task_name = [k for k, v in futures.items() if v == future][0]
                try:
                    results[task_name] = future.result()
                    update_progress(
                        f"Completed {task_name.capitalize()} for {file_name}",
                        increment=True,
                    )
                except Exception as e:
                    logger.error(
                        f"Task {task_name} for {file_name} failed after retries: {e}"
                    )
                    results[task_name] = f"Error: {e}"

        dates_response = results["dates"]
        requirements_response = results["requirements"]
        folder_structure_response = results["folder_structure"]
        client_info_response = results["client_info"]
        dates_source = "AI"

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
            if (
                dates_source == "Fallback"
                and dates_response
                and dates_response != "NO_INFO_FOUND"
            ):
                dates_response += " [fallback]"

        dates_response = replace_citations(dates_response, file_id_to_name)
        requirements_response = replace_citations(
            requirements_response, file_id_to_name
        )
        folder_structure_response = replace_citations(
            folder_structure_response, file_id_to_name
        )
        client_info_response = replace_citations(client_info_response, file_id_to_name)

        log_raw_response(
            logger, f"Dates for {file_name}", dates_response, source=dates_source
        )
        log_raw_response(logger, f"Requirements for {file_name}", requirements_response)
        log_raw_response(
            logger, f"Folder Structure for {file_name}", folder_structure_response
        )
        log_raw_response(logger, f"Client Info for {file_name}", client_info_response)

        logger.info(f"Completed analysis for {file_name}")

        batch_results.append(
            (
                dates_response,
                requirements_response,
                folder_structure_response,
                client_info_response,
            )
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
    simulation_mode,
):
    logger = init_logger()
    batch_size = BATCH_SIZE
    total_batches = (len(uploaded_file_ids) + batch_size - 1) // batch_size
    total_tasks = len(uploaded_file_ids) * 4 + 1  # 4 tasks per file + summary
    current_task = 0
    progress_log_messages = []
    all_dates = []
    all_requirements = []
    all_folder_structures = []
    all_client_infos = []
    lock = threading.Lock()

    file_names = [file_id_to_name[file_id] for file_id in uploaded_file_ids]
    logger.info(f"Starting analysis for {total_files} files: {', '.join(file_names)}")

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

    for i in range(0, len(uploaded_file_ids), batch_size):
        batch_number = i // batch_size + 1
        batch_file_ids = uploaded_file_ids[i : i + batch_size]
        batch_start = i + 1
        batch_end = min(i + batch_size, total_files)
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
            simulation_mode,
        )
        for dates, requirements, folder_structure, client_info in batch_results:
            all_dates.append(dates)
            all_requirements.append(requirements)
            all_folder_structures.append(folder_structure)
            all_client_infos.append(client_info)

    update_progress("Generating tender summary...", increment=True)
    try:
        if len(uploaded_file_ids) > 10:
            summary_response = generate_summary_in_batches(
                uploaded_file_ids,
                file_id_to_name,
                logger,
                all_dates,
                all_requirements,
                BATCH_SIZE,
                simulation_mode,
            )
        else:
            summary_response, _ = run_prompt(
                uploaded_file_ids,
                SUMMARY_PROMPT,
                "Tender Summary",
                logger,
                simulation_mode,
            )
    except Exception as e:
        error_msg = f"Error generating summary: {str(e)}"
        log_error(logger, error_msg)
        summary_response = error_msg
    summary_response = replace_citations(summary_response, file_id_to_name)
    update_progress("Analysis complete", increment=True)

    if "Error" not in summary_response:
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
        all_client_infos,
        summary_response,
        progress_log_messages,
    )


def synthesize_results(
    all_dates,
    all_requirements,
    all_folder_structures,
    all_client_infos,
    uploaded_file_ids,
    file_id_to_name,
    logger,
    simulation_mode,
):
    dates_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{dates}"
            for file_id, dates in zip(uploaded_file_ids, all_dates)
            if dates.strip() and dates.strip() != "NO_INFO_FOUND"
        ]
    )
    if dates_data:
        synthesized_dates, _ = run_prompt(
            [],
            format_prompt(SYNTHESIZE_DATES_PROMPT, dates_data=dates_data),
            "Synthesize Dates",
            logger,
            simulation_mode,
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
        synthesized_requirements, _ = run_prompt(
            [],
            format_prompt(
                SYNTHESIZE_REQUIREMENTS_PROMPT, requirements_data=requirements_data
            ),
            "Synthesize Requirements",
            logger,
            simulation_mode,
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
    if folder_structure_data or synthesized_requirements != "NO_INFO_FOUND":
        synthesized_folder_structure, _ = run_prompt(
            [],
            format_prompt(
                SYNTHESIZE_FOLDER_STRUCTURE_PROMPT,
                folder_structure_data=folder_structure_data,
                requirements_data=synthesized_requirements,
            ),
            "Synthesize Folder Structure",
            logger,
            simulation_mode,
        )
    else:
        synthesized_folder_structure = "NO_INFO_FOUND"

    # Synthesize client information
    client_info_data = "\n\n".join(
        [
            f"File: {file_id_to_name[file_id]}\n{client_info}"
            for file_id, client_info in zip(uploaded_file_ids, all_client_infos)
            if client_info.strip() and client_info.strip() != "NO_INFO_FOUND"
        ]
    )
    if client_info_data:
        synthesized_client_info, _ = run_prompt(
            [],
            format_prompt(
                SYNTHESIZE_CLIENT_INFO_PROMPT, client_info_data=client_info_data
            ),
            "Synthesize Client Info",
            logger,
            simulation_mode,
        )
    else:
        synthesized_client_info = "NO_INFO_FOUND"

    return {
        "synthesized_dates": synthesized_dates,
        "synthesized_requirements": synthesized_requirements,
        "synthesized_folder_structure": synthesized_folder_structure,
        "synthesized_client_info": synthesized_client_info,
    }
