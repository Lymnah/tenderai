import streamlit as st
import openai
import os
import tempfile
import dotenv
import time
import json
import re
import PyPDF2
from io import BytesIO
import base64

# Global variable to toggle simulation mode
SIMULATION_MODE = (
    False  # Set to True to use mock responses, False to use real OpenAI API
)

# Load environment variables
dotenv.load_dotenv()

# Load API Key (only required if not in simulation mode)
if not SIMULATION_MODE:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        st.error(
            "⚠️ OpenAI API Key is missing! Please set `OPENAI_API_KEY` in your environment variables."
        )
        st.stop()
    openai.api_key = OPENAI_API_KEY

    # Use an existing Assistant ID from environment variable
    ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
    if not ASSISTANT_ID:
        st.error(
            "⚠️ Assistant ID is missing! Set `OPENAI_ASSISTANT_ID` in your environment variables."
        )
        st.stop()

# Streamlit UI
st.set_page_config(page_title="INOX Tender AI", layout="wide")

# Custom CSS for styling
st.markdown(
    """
<style>
    .stTextArea textarea { 
        border: 2px solid #007bff; 
        border-radius: 5px; 
        background-color: #2a2a2a; 
        color: #d3d3d3; 
    }
    .stButton button { 
        background-color: #007bff; 
        color: white; 
        border-radius: 5px; 
        padding: 10px 20px; 
        font-size: 16px; 
        transition: background-color 0.3s ease; 
    }
    .stButton button:hover { 
        background-color: #0056b3; 
    }
    .stDownloadButton button { 
        background-color: #28a745; 
        color: white; 
        border-radius: 5px; 
        padding: 10px 20px; 
        font-size: 16px; 
        transition: background-color 0.3s ease; 
    }
    .stDownloadButton button:hover { 
        background-color: #218838; 
    }
    .analysis-section { 
        margin-bottom: 20px; 
    }
    .chat-message { 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); 
    }
    .user-message { 
        background-color: #3a3a3a; 
        color: #d3d3d3; 
    }
    .assistant-message { 
        background-color: #007bff; 
        color: white; 
    }
    .st-expander { 
        margin-bottom: 20px; 
        background-color: #2a2a2a; 
        border-radius: 8px; 
        padding: 15px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); 
    }
    .st-expander div { 
        padding: 10px; 
    }
    .stMarkdown { 
        margin-bottom: 15px; 
        font-size: 16px; 
        color: #d3d3d3; 
        line-height: 1.6; 
    }
    h1 { 
        font-size: 32px; 
        color: #ffffff; 
        text-align: center; 
        margin-bottom: 20px; 
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5); 
    }
    h2 { 
        font-size: 24px; 
        color: #ffffff; 
        margin-top: 30px; 
    }
    h3 { 
        font-size: 20px; 
        color: #ffffff; 
    }
    hr { 
        border: 1px solid #444; 
        margin: 20px 0; 
    }
    .section-heading { 
        font-size: 20px; 
        margin-bottom: 10px; 
        color: #007bff; 
        font-weight: bold; 
    }
    .spinner-text { 
        font-size: 16px; 
        color: #d3d3d3; 
    }
    .stSpinner {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    .stSpinner > div {
        font-size: 16px;
        color: #d3d3d3;
        margin-top: 10px;
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
        padding: 20px 30px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    }
    /* Sidebar logo container */
    .sidebar-logo-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        margin-top: 0px;
    }
    .sidebar-logo {
        max-height: 50px; /* Slightly smaller for sidebar */
    }
    /* File uploader styling */
    .stFileUploader {
        background-color: #2a2a2a;
        border: 2px dashed #007bff;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    .stFileUploader div {
        color: #d3d3d3;
    }
    /* Success and error messages */
    .stSuccess {
        background-color: #1a3c34;
        color: #a3d9b1;
        border-radius: 5px;
        padding: 10px;
    }
    .stError {
        background-color: #4a1a1a;
        color: #ff9999;
        border-radius: 5px;
        padding: 10px;
    }
    .stWarning {
        background-color: #4a3c1a;
        color: #ffcc99;
        border-radius: 5px;
        padding: 10px;
    }
    /* Progress log styling */
    .progress-log {
        background-color: #2a2a2a;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
        max-height: 200px;
        overflow-y: auto;
        color: #d3d3d3;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Function to load and encode image as base64
def load_image_as_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        st.error(
            f"Image file {image_path} not found. Please ensure it is in the same directory as app.py."
        )
        return None


# Load logos
your_company_logo = load_image_as_base64("your_company_logo.png")
client_company_logo = load_image_as_base64("client_company_logo.png")

# Sidebar
with st.sidebar:
    # Display logos at the top of the sidebar
    if your_company_logo and client_company_logo:
        st.markdown(
            f"""
            <div class="sidebar-logo-container">
                <img src="{your_company_logo}" class="sidebar-logo" alt="Your Company Logo">
                <img src="{client_company_logo}" class="sidebar-logo" alt="Client Company Logo">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "One or both logos could not be loaded. Please check the file paths."
        )

    st.header("📂 Upload Documents")
    uploaded_files = st.file_uploader(
        "Add your documents (PDF, DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded.")

        # File Upload Feedback: Display a preview of the first page of the PDF
        st.subheader("🔍 File Preview")
        for file in uploaded_files:
            if file.size > 200 * 1024 * 1024:  # 200MB in bytes
                st.error(f"File {file.name} exceeds the 200MB limit.")
                continue
            if file.name.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(BytesIO(file.getvalue()))
                    first_page = pdf_reader.pages[0]
                    text = first_page.extract_text()
                    st.text_area(
                        f"Preview of {file.name} (First Page):",
                        text[:500] + "..." if len(text) > 500 else text,
                        height=150,
                        disabled=True,
                    )
                except Exception as e:
                    st.warning(f"Could not preview {file.name}: {str(e)}")
            else:
                st.warning(
                    f"Preview not available for {file.name} (only PDFs supported)."
                )

# Main Content
st.title("INOX Tender AI - Assistance aux Appels d'Offres")

# Dictionary to map file IDs to original filenames
file_id_to_name = {}


# Mock response function
def load_mock_response(prompt_type):
    try:
        with open("mock_response.txt", "r", encoding="utf-8") as f:
            base_response = f.read()
        # Simulate different responses based on prompt type
        if "dates" in prompt_type.lower():
            return f"Mock Dates Response for {prompt_type}:\n- Date: 2025-04-15 14:00, Time Zone: CET, Event: Submission Deadline, Source: mock_file.pdf"
        elif "requirements" in prompt_type.lower():
            return f"Mock Requirements Response for {prompt_type}:\n**Mandatory Requirements**\n- Must have ISO 9001 certification [mock_file.pdf]\n**Optional Requirements**\n- None [mock_file.pdf]\n**Legal Requirements**\n- Compliance with GDPR [mock_file.pdf]\n**Financial Requirements**\n- Minimum budget of 500k EUR [mock_file.pdf]\n**Security Requirements**\n- Must have cybersecurity certification [mock_file.pdf]\n**Certifications**\n- ISO 9001 [mock_file.pdf]"
        elif "folder structure" in prompt_type.lower():
            return f"Mock Folder Structure Response for {prompt_type}:\n- Main Submission Folder\n  - Technical Docs: Technical Proposal, Specs Sheet [mock_file.pdf]\n  - Financial Docs: Budget Plan [mock_file.pdf]"
        elif "summary" in prompt_type.lower():
            return f"Mock Tender Summary Response for {prompt_type}:\nThe client is seeking a comprehensive solution for a construction project, requiring technical expertise, financial stability, and compliance with legal standards. Key deliverables include a detailed technical proposal and a financial plan. The project aims to build a new facility by 2026, with a focus on sustainability. [mock_file.pdf]"
        return base_response
    except FileNotFoundError:
        st.error("Mock response file 'mock_response.txt' not found.")
        return "No response generated."


if uploaded_files:
    # Upload files to OpenAI (or simulate) and store file ID mapping with a loading indicator
    uploaded_file_ids = []
    failed_uploads = []
    total_files = len(uploaded_files)

    # Use a single spinner for the entire upload process
    with st.spinner(""):
        # Placeholder for dynamic status text
        status_text = st.empty()
        # Progress bar for visual feedback
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            # Update status text
            file_size = (
                f"{file.size / 1024:.1f}KB"
                if file.size < 1024 * 1024
                else f"{file.size / (1024 * 1024):.1f}MB"
            )
            status_text.text(
                f"Uploading file {i+1} of {total_files}: {file.name} ({file_size})..."
            )

            # Update progress bar
            progress_bar.progress((i + 1) / total_files)

            file_extension = os.path.splitext(file.name)[1]
            if file_extension not in [".pdf", ".docx"]:
                st.error(f"Unsupported file type: {file_extension}")
                failed_uploads.append(file.name)
                continue

            if SIMULATION_MODE:
                # Simulate upload time (1 second)
                time.sleep(1)
                # Mock file ID
                mock_file_id = f"mock_file_id_{i}"
                uploaded_file_ids.append(mock_file_id)
                file_id_to_name[mock_file_id] = file.name
            else:
                # Create temporary file
                temp_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=file_extension
                    ) as temp_file:
                        temp_file.write(file.getvalue())
                        temp_file_path = temp_file.name

                    with open(temp_file_path, "rb") as f:
                        uploaded_file = openai.files.create(
                            file=f, purpose="assistants"
                        )
                        uploaded_file_ids.append(uploaded_file.id)
                        file_id_to_name[uploaded_file.id] = file.name

                except Exception as e:
                    st.error(f"Failed to upload file {file.name}: {str(e)}")
                    failed_uploads.append(file.name)
                    continue
                finally:
                    # Clean up temporary file
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                        except Exception as e:
                            st.warning(
                                f"Failed to clean up temporary file {temp_file_path}: {str(e)}"
                            )

        # Clear the status text and progress bar
        status_text.empty()
        progress_bar.empty()

    # Display summary of failed uploads, if any
    if failed_uploads:
        st.warning(
            f"Successfully uploaded {len(uploaded_file_ids)} out of {total_files} file(s). "
            f"Failed to upload: {', '.join(failed_uploads)}"
        )
    else:
        st.success(f"Successfully uploaded all {total_files} file(s) to OpenAI.")

    # Create a new thread for analysis
    if not SIMULATION_MODE:
        thread = openai.beta.threads.create()
        thread_id = thread.id
    else:
        thread_id = "mock_thread_id"

    # Function to run a prompt and get a response
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
            response = load_mock_response(task_name)
            if progress_callback and total_tasks and current_task:
                progress_callback(current_task / total_tasks, f"Completed {task_name}")
            return response
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
                    st.spinner(
                        f"Processing {task_name}... (Status: {run_status.status})"
                    )
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled"]:
                    st.error(f"{task_name} failed with status: {run_status.status}")
                    if progress_callback and total_tasks and current_task:
                        progress_callback(
                            current_task / total_tasks, f"Failed {task_name}"
                        )
                    return "No response generated."
                time.sleep(0.5)  # Reduced polling interval
            spinner_placeholder.empty()
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            assistant_responses = [
                msg for msg in messages.data if msg.role == "assistant"
            ]
            if not assistant_responses:
                if progress_callback and total_tasks and current_task:
                    progress_callback(
                        current_task / total_tasks, f"No response for {task_name}"
                    )
                return "No response generated."
            response = "\n".join(
                content.text.value
                for msg in assistant_responses
                for content in msg.content
                if content.type == "text"
            )
            if progress_callback and total_tasks and current_task:
                progress_callback(current_task / total_tasks, f"Completed {task_name}")
            return response

    # Replace citations with original filenames
    def replace_citations(text):
        def replace_citation(match):
            citation = match.group(0)
            # Extract the file ID or temporary filename from the citation
            for file_id, original_name in file_id_to_name.items():
                # Check if the citation contains the file ID or the temporary filename
                if file_id in citation or any(
                    temp_name in citation
                    for temp_name in [f"tmp{file_id}.pdf", f'"{file_id}"']
                ):
                    return f"【{original_name}】"
            # If there's only one file, use its name as a fallback
            if len(file_id_to_name) == 1:
                return f"【{list(file_id_to_name.values())[0]}】"
            return citation

        # Replace citations in the format 【...】 and temporary filenames
        text = re.sub(r"【.*?】", replace_citation, text)
        # Replace any remaining temporary filenames (e.g., tmpp4z2s6xe.pdf)
        for file_id, original_name in file_id_to_name.items():
            text = re.sub(rf"tmp\w+\.pdf", original_name, text)
            text = re.sub(rf'"{file_id}"', original_name, text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove single asterisks
        return text

    # Analysis with enhanced feedback
    st.subheader("Analyzing Documents...")

    # Progress bar and status log
    progress_bar = st.progress(0)
    status_text = st.empty()
    progress_log = st.empty()

    def analyze_documents():
        total_tasks = (
            len(uploaded_file_ids) * 3 + 1
        )  # 3 tasks per file + 1 summary task
        current_task = 0
        progress_log_messages = []

        def update_progress(message):
            nonlocal current_task, progress_log_messages
            current_task += 1
            progress = current_task / total_tasks
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
            dates_response = run_prompt(
                [file_id], dates_prompt, f"Dates for {file_name}"
            )
            dates_response = replace_citations(dates_response)
            all_dates.append(dates_response)
            update_progress(f"Completed Dates for {file_name}")

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
            requirements_response = replace_citations(requirements_response)
            all_requirements.append(requirements_response)
            update_progress(f"Completed Requirements for {file_name}")

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
            folder_structure_response = replace_citations(folder_structure_response)
            all_folder_structures.append(folder_structure_response)
            update_progress(f"Completed Folder Structure for {file_name}")

        summary_prompt = """
        Provide a holistic summary of the tender based on all the provided documents. Focus on what the client is asking for, including:
        - The overall purpose of the tender.
        - The main deliverables or services required.
        - Any key objectives or priorities mentioned.
        - A brief overview of the scope and scale of the project.
        Synthesize the information from all files to create a cohesive summary. Cite the source files where relevant. Format the output as a concise paragraph (150-200 words).
        """
        summary_response = run_prompt(
            uploaded_file_ids, summary_prompt, "Tender Summary"
        )
        summary_response = replace_citations(summary_response)
        update_progress("Completed Tender Summary")

        return all_dates, all_requirements, all_folder_structures, summary_response

    # Run the analysis and get results
    all_dates, all_requirements, all_folder_structures, summary_response = (
        analyze_documents()
    )

    # Clear the progress indicators
    status_text.empty()
    progress_log.empty()

    # Display Results in Dedicated Sections
    st.subheader("📊 Tender Analysis Results")

    # Important Dates Section
    st.markdown("### 🕒 Important Dates and Milestones")
    with st.expander("View Dates and Milestones", expanded=True):
        for dates in all_dates:
            st.markdown(dates, unsafe_allow_html=False)
            st.markdown("<hr>", unsafe_allow_html=True)

    # Tender Summary Section
    st.markdown("### 📝 Tender Summary")
    with st.expander("View Tender Summary", expanded=True):
        st.markdown(summary_response, unsafe_allow_html=False)

    # Technical Requirements Section
    st.markdown("### 🔧 Technical Requirements")
    with st.expander("View Technical Requirements", expanded=True):
        for requirements in all_requirements:
            st.markdown(requirements, unsafe_allow_html=False)
            st.markdown("<hr>", unsafe_allow_html=True)

    # Folder Structure Section
    st.markdown("### 📁 Required Folder Structure")
    with st.expander("View Folder Structure", expanded=True):
        for folder_structure in all_folder_structures:
            st.markdown(folder_structure, unsafe_allow_html=False)
            st.markdown("<hr>", unsafe_allow_html=True)

    # Download Full Report
    full_report = (
        "Tender Analysis Report\n\n"
        "## Important Dates and Milestones\n" + "\n\n".join(all_dates) + "\n\n"
        "## Tender Summary\n" + summary_response + "\n\n"
        "## Technical Requirements\n" + "\n\n".join(all_requirements) + "\n\n"
        "## Required Folder Structure\n" + "\n\n".join(all_folder_structures)
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

                assistant_response = replace_citations(assistant_response)
                st.session_state.chat_history.append(
                    {"user": user_query, "assistant": assistant_response}
                )
                st.rerun()  # Refresh to show updated chat history
