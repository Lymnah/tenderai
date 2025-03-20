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
    True  # Set to True to use mock responses, False to use real OpenAI API
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
def load_mock_response():
    try:
        with open("mock_response.txt", "r", encoding="utf-8") as f:
            return f.read()
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
                # Simulate upload time (2 seconds)
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

    # Create a new thread with analysis spinner
    with st.spinner("Analyzing documents..."):
        if SIMULATION_MODE:
            # Simulate analysis time (3 seconds)
            time.sleep(1)
            thread_id = "mock_thread_id"
            response_text = load_mock_response()
        else:
            thread = openai.beta.threads.create()
            thread_id = thread.id

            # Attach files and send query
            query = """
            Extract the following details from the uploaded tender document:
            1. Submission deadline (date and time) and time zone.
            2. Submission method (online, email, or printed, including exact address and labeling instructions).
            3. Submission format (paper, electronic, specific templates, etc., with all requirements).
            4. Any required document structures or templates (list all annexes and specifications).
            Provide a detailed response with all relevant information, including additional notes (e.g., tender validity, evaluation criteria), and cite the source file explicitly.
            """
            openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=query,
                attachments=[
                    {"file_id": file_id, "tools": [{"type": "file_search"}]}
                    for file_id in uploaded_file_ids
                ],
            )

            # Start the assistant run
            run = openai.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=ASSISTANT_ID.strip(),
                tools=[{"type": "file_search"}],
            )

            # Poll for completion with a single spinner
            spinner_placeholder = st.empty()
            while True:
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )
                with spinner_placeholder.container():
                    st.spinner(f"Analyzing documents... (Status: {run_status.status})")
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled"]:
                    st.error(f"Analysis failed with status: {run_status.status}")
                    st.stop()
                time.sleep(1)
            spinner_placeholder.empty()

            # Retrieve messages
            messages = openai.beta.threads.messages.list(thread_id=thread_id)
            assistant_responses = [
                msg for msg in messages.data if msg.role == "assistant"
            ]
            if not assistant_responses:
                response_text = "No response generated."
            else:
                response_text = "\n".join(
                    content.text.value
                    for msg in assistant_responses
                    for content in msg.content
                    if content.type == "text"
                )

        # Replace citations with original filenames
        def replace_citations(match):
            citation = match.group(0)
            if len(file_id_to_name) == 1:
                return f"【{list(file_id_to_name.values())[0]}】"
            for file_id, original_name in file_id_to_name.items():
                if file_id in citation:
                    return f"【{original_name}】"
            return (
                f"【{list(file_id_to_name.values())[0]}】"
                if file_id_to_name
                else citation
            )

        response_text = re.sub(r"【.*?】", replace_citations, response_text)
        response_text = re.sub(r'"tmp\w+\.pdf"', "", response_text)

        # Remove single asterisks used for italicization
        response_text = re.sub(r"\*(.*?)\*", r"\1", response_text)

    # Display analysis with proper formatting
    st.subheader("📊 Résultats des Analyses")
    with st.expander("Détail:", expanded=True):
        # Split response into sections based on numbered headings
        sections = re.split(r"(\d+\.\s+[^:]+:)", response_text)
        for i in range(len(sections)):
            section = sections[i].strip()
            if not section:
                continue
            if re.match(
                r"\d+\.\s+[^:]+:", section
            ):  # Section heading (e.g., "1. Submission Deadline:")
                if i > 0:  # Add a divider before each section except the first
                    st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='section-heading'>{section}</div>",
                    unsafe_allow_html=True,
                )
            else:
                # Render the section content as-is, preserving the assistant's Markdown formatting
                st.markdown(section, unsafe_allow_html=False)

        # Remove redundant "Citations:" section if it exists
        response_lines = response_text.split("\n")
        if any("Citations:" in line for line in response_lines):
            response_text = "\n".join(
                line for line in response_lines if "Citations:" not in line
            )

        st.markdown(
            f"\n**Source:** {list(file_id_to_name.values())[0] if file_id_to_name else 'Unknown'}",
            unsafe_allow_html=False,
        )

    # Download button
    st.download_button(
        "📥 Download Report",
        response_text,
        file_name="tender_analysis.txt",
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
                        time.sleep(1)
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

                assistant_response = re.sub(
                    r"【.*?】", replace_citations, assistant_response
                )
                assistant_response = re.sub(r'"tmp\w+\.pdf"', "", assistant_response)
                # Remove asterisks from chat response as well
                assistant_response = re.sub(r"\*(.*?)\*", r"\1", assistant_response)
                st.session_state.chat_history.append(
                    {"user": user_query, "assistant": assistant_response}
                )
                st.rerun()  # Refresh to show updated chat history
