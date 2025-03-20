import streamlit as st
import openai
import os
import tempfile
import dotenv
import time

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

# # Retrieve existing assistants
# assistants = openai.beta.assistants.list()
# if assistants.data:
#     print("Existing assistants:")
#     for assistant in assistants.data:
#         print(f"Name: {assistant.name}, ID: {assistant.id}")
# else:
#     print("No assistants found. You may need to create one.")

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

uploaded_file_ids = []
if uploaded_files:
    st.sidebar.success(f"{len(uploaded_files)} fichiers ajoutés.")

    # Upload files to OpenAI
    for file in uploaded_files:
        file_extension = os.path.splitext(file.name)[
            1
        ]  # Extracts the extension (e.g., .pdf, .docx)

        # Ensure the file extension is one of the supported types
        if file_extension.lower() not in [
            ".pdf",
            ".docx",
            ".txt",
            ".csv",
            ".json",
            ".html",
            ".md",
        ]:
            st.error(f"❌ Type de fichier non supporté : {file_extension}")
            continue

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            temp_file.write(file.getvalue())
            temp_file_path = temp_file.name  # Now retains the correct extension

        uploaded_file = openai.files.create(
            file=open(temp_file_path, "rb"), purpose="assistants"
        )
        uploaded_file_ids.append(uploaded_file.id)

    # Create a new thread
    with st.spinner("Analyse en cours..."):
        thread = openai.beta.threads.create()
        thread_id = thread.id

        # Attach files to the thread via messages
        for file_id in uploaded_file_ids:
            openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content="Voici un document à analyser.",
                attachments=[
                    {"file_id": file_id, "tools": [{"type": "file_search"}]},
                ],
            )

        print(thread.tool_resources.file_search)

        # Start the assistant run
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID.strip(),
            tools=[{"type": "file_search"}],
        )

        st.success("L'analyse a commencé. Veuillez patienter...")

        # Poll for completion with delay
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("L'analyse a échoué. Veuillez réessayer.")
                st.stop()
            else:
                print(f"Unexpected run status: {run_status.status}")
            time.sleep(2)  # Prevent excessive API calls

        # Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        response_text = next(
            (msg.content.text for msg in messages.data if hasattr(msg.content, "text")),
            "Aucune réponse générée.",
        )

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
    else:
        with st.spinner("Réponse en cours..."):
            message_response = openai.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=user_query
            )
            assistant_response = (
                message_response.data[0].content.text
                if message_response.data
                else "Aucune réponse générée."
            )
            st.write("**Réponse:**", assistant_response)
