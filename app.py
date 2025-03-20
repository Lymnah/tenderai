import streamlit as st
import openai
import os
import tempfile
import dotenv
import time
import json
import re

# Load environment variables
dotenv.load_dotenv()

# Load API Key
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
    .stTextArea textarea { border: 2px solid #007bff; border-radius: 5px; }
    .stButton button { background-color: #007bff; color: white; border-radius: 5px; }
    .stDownloadButton button { background-color: #28a745; color: white; border-radius: 5px; }
    .analysis-section { margin-bottom: 20px; }
    .chat-message { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .user-message { background-color: #e9ecef; }
    .assistant-message { background-color: #d1e7ff; }
</style>
""",
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.header("📂 Upload Documents")
    uploaded_files = st.file_uploader(
        "Add your documents (PDF, DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded.")

# Main Content
st.title("📄 INOX Tender AI - Assistance aux Appels d'Offres")

# Dictionary to map file IDs to original filenames
file_id_to_name = {}

if uploaded_files:
    # Upload files to OpenAI and store file ID mapping
    uploaded_file_ids = []
    for file in uploaded_files:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension not in [".pdf", ".docx"]:
            st.error(f"Unsupported file type: {file_extension}")
            continue

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            temp_file.write(file.getvalue())
            temp_file_path = temp_file.name

        with open(temp_file_path, "rb") as f:
            uploaded_file = openai.files.create(file=f, purpose="assistants")
            uploaded_file_ids.append(uploaded_file.id)
            file_id_to_name[uploaded_file.id] = file.name

    # Create a new thread
    with st.spinner("Analyzing documents..."):
        thread = openai.beta.threads.create()
        thread_id = thread.id

        # Attach files and send query
        query = """
        Extract the following details from the uploaded tender document:
        1. Submission deadline (date and time) and time zone (infer if not specified, e.g., CET/CEST for Swiss documents).
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

        # Poll for completion with a progress bar
        status_placeholder = st.empty()
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )
            status_placeholder.text(f"Processing: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled"]:
                st.error(f"Analysis failed with status: {run_status.status}")
                st.stop()
            time.sleep(2)
        status_placeholder.empty()

        # Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        assistant_responses = [msg for msg in messages.data if msg.role == "assistant"]
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

    # Display analysis with proper formatting
    st.subheader("📊 Analysis Results")
    with st.expander("Details from the Tender Document:", expanded=True):
        # Split response into sections based on numbered headings
        sections = re.split(r"(\d+\.\s+[^:]+:)", response_text)
        for i in range(len(sections)):
            section = sections[i].strip()
            if not section:
                continue
            if re.match(
                r"\d+\.\s+[^:]+:", section
            ):  # Section heading (e.g., "1. Submission Deadline:")
                st.markdown(f"**{section}**")
            else:
                # Apply bullets to items within the section, skipping empty lines
                lines = section.split("\n")
                for line in lines:
                    line = line.strip()
                    if line:  # Only process non-empty lines
                        if line.startswith("-"):
                            st.markdown(f"{line}")
                        else:
                            st.markdown(f"- {line}")
                    else:
                        st.markdown("")  # Add a blank line for spacing
        st.markdown(
            f"\n**Source:** {list(file_id_to_name.values())[0] if file_id_to_name else 'Unknown'}"
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
            with st.spinner("Generating response..."):
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
                    if run_status.status == "completed":
                        break
                    time.sleep(2)
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
                st.session_state.chat_history.append(
                    {"user": user_query, "assistant": assistant_response}
                )
                st.rerun()  # Refresh to show updated chat history
