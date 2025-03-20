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
st.title("📄 INOX Tender AI - Assistance aux Appels d'Offres")

st.sidebar.header("📂 Télécharger vos documents")
uploaded_files = st.sidebar.file_uploader(
    "Ajoutez vos documents (PDF, DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)


# Dictionary to map file IDs to original filenames
file_id_to_name = {}

if uploaded_files:
    st.sidebar.success(f"{len(uploaded_files)} fichiers ajoutés.")

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
            st.write(f"Uploaded file: {file.name} with ID: {uploaded_file.id}")

    # Create a new thread
    with st.spinner("Analyse en cours..."):
        thread = openai.beta.threads.create()
        thread_id = thread.id
        st.write(f"Created thread with ID: {thread_id}")

        # Attach files and send query
        query = """
        Extract the following details from the uploaded tender document:
        1. Submission deadline (date and time) and time zone (infer if not specified).
        2. Submission method (online, email, printed, including exact address and labeling instructions).
        3. Submission format (paper, electronic, specific templates, etc., with all requirements).
        4. Any required document structures or templates (list all annexes and specifications).
        Provide a detailed response with all relevant information, including additional notes (e.g., tender validity, evaluation criteria), and cite the source file explicitly.
        """
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=query,
            attachments=[
                {"file_id": file_id, "tools": [{"type": "file_search"}]}
                for file_id in uploaded_file_ids
            ],
        )
        st.write(
            f"Message sent with attachments: {json.dumps(message.to_dict(), indent=2)}"
        )

        # Start the assistant run
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID.strip(),
            tools=[{"type": "file_search"}],
        )
        st.write(f"Started run with ID: {run.id}")

        # Poll for completion
        with st.spinner("Waiting for analysis to complete..."):
            while True:
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )
                st.write(f"Run status: {run_status.status}")
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled"]:
                    st.error(f"Run failed with status: {run_status.status}")
                    st.write(
                        f"Run details: {json.dumps(run_status.to_dict(), indent=2)}"
                    )
                    st.stop()
                time.sleep(2)

        # Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        st.write(
            f"Raw messages: {json.dumps([msg.to_dict() for msg in messages.data], indent=2)}"
        )

        # Get assistant responses
        assistant_responses = [msg for msg in messages.data if msg.role == "assistant"]
        if not assistant_responses:
            response_text = "Aucune réponse générée."
        else:
            response_text = "\n".join(
                content.text.value
                for msg in assistant_responses
                for content in msg.content
                if content.type == "text"
            )
            st.write(f"Raw response text before citation replacement: {response_text}")

            # Replace citations with original filenames
            def replace_citations(match):
                citation = match.group(0)  # e.g., 【4:1†source】
                # If there's only one file, assume all citations refer to it
                if len(file_id_to_name) == 1:
                    return f"【{list(file_id_to_name.values())[0]}】"
                # Otherwise, try to match file_id if present in citation
                for file_id, original_name in file_id_to_name.items():
                    if file_id in citation:
                        return f"【{original_name}】"
                # Fallback: Replace "source" with the first file name if no match
                return (
                    f"【{list(file_id_to_name.values())[0]}】"
                    if "source" in citation
                    else citation
                )

            response_text = re.sub(r"【.*?】", replace_citations, response_text)

        # Display analysis
        st.subheader("📊 Résultats de l'analyse")
        st.write(response_text)

        # Download report option
        st.download_button(
            "📥 Télécharger le rapport", response_text, file_name="analyse_tender.txt"
        )

# Chat interface
st.subheader("💬 Interagir avec l'Assistant")
user_query = st.text_area("Posez une question sur les documents analysés:")
if st.button("Envoyer"):
    if not user_query.strip():
        st.warning("Veuillez entrer une question.")
    elif "thread_id" not in locals():
        st.warning("Veuillez d'abord analyser un document.")
    else:
        with st.spinner("Réponse en cours..."):
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
                "Aucune réponse générée.",
            )
            # Apply citation replacement to chat response
            assistant_response = re.sub(
                r"【.*?】", replace_citations, assistant_response
            )
            st.write("**Réponse:**", assistant_response)
