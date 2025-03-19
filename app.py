import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import openai
import os
import tempfile
import dotenv
import docx2txt

# Load environment variables
dotenv.load_dotenv()

# Load API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error(
        "⚠️ OpenAI API Key is missing! Please set `OPENAI_API_KEY` in your environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# Streamlit UI
st.set_page_config(page_title="INOX Tender AI", layout="wide")
st.title("📄 INOX Tender AI - Assistance aux Appels d'Offres")

st.sidebar.header("📂 Télécharger vos documents")
uploaded_files = st.sidebar.file_uploader("Ajoutez vos documents (PDF, DOCX)", type=[
                                          "pdf", "docx"], accept_multiple_files=True)

# OpenAI Assistants API
if uploaded_files:
    st.sidebar.success(f"{len(uploaded_files)} fichiers ajoutés.")

    # Create Assistant Thread
    with st.spinner("Analyse en cours..."):
        thread = openai.beta.threads.create()
        thread_id = thread.id

        # Upload each file to OpenAI Assistants API
        for file in uploaded_files:
            response = openai.beta.threads.files.create(
                thread_id=thread_id,
                file=file
            )

        # Run Assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id="your_assistant_id_here"
        )

        # Poll for Completion
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("L'analyse a échoué. Veuillez réessayer.")
                st.stop()

        # Retrieve Messages
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        response_text = messages.data[0].content.text if messages.data else "Aucune réponse générée."

        # Display Analysis
        st.subheader("📊 Résultats de l'analyse")
        st.write(response_text)

        # Download Report Option
        st.download_button("📥 Télécharger le rapport",
                           response_text, file_name="analyse_tender.txt")

# Chat Interface
st.subheader("💬 Interagir avec l'Assistant")
user_query = st.text_area("Posez une question sur les documents analysés:")
if st.button("Envoyer"):
    if not user_query.strip():
        st.warning("Veuillez entrer une question.")
    else:
        with st.spinner("Réponse en cours..."):
            response = openai.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_query
            )
            assistant_response = response.data[0].content.text if response.data else "Aucune réponse générée."
            st.write("**Réponse:**", assistant_response)
