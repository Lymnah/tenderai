import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI, ChatOpenAI
from langchain.document_loaders import PyPDFLoader
import openai
import os
import tempfile
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

st.title("Inox Tender - Analyse d'Appel d'Offres")
st.write("Déposez les documents pour analyse.")

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error(
        "⚠️ OpenAI API Key is missing! Please set `OPENAI_API_KEY` in your environment variables.")

# File uploader
uploaded_files = st.file_uploader(
    "Téléchargez vos documents", accept_multiple_files=True, type=['pdf', 'docx'])


def analyse_document(content):
    """Analyse document content using OpenAI"""
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    prompt = PromptTemplate(
        template="Analyse ce document et extrait les exigences obligatoires:\n{doc}",
        input_variables=["doc"]
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.invoke({"doc": content})


def extract_text_from_pdf(uploaded_file):
    """Extract text from a PDF file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        loader = PyPDFLoader(tmp_file.name)
        pages = loader.load_and_split()
        return " ".join([page.page_content for page in pages])


def extract_text_from_docx(uploaded_file):
    """Extract text from a DOCX file"""
    import docx2txt
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(uploaded_file.read())
        return docx2txt.process(tmp_file.name)


if uploaded_files:
    st.success(f"{len(uploaded_files)} fichiers téléchargés.")
    st.write("Analyse en cours... ⏳")

    full_text = ""
    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            full_text += extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            full_text += extract_text_from_docx(uploaded_file)

    # Analyze the extracted text
    results = analyse_document(full_text)

    # Mock values for missing variables (replace with real extractions)
    nom_projet = "Projet X"
    client = "Client ABC"
    date_limite = "01/06/2024"
    exigences_obligatoires = results
    criteres_evaluation = "Prix, Qualité, Délais"

    rapport = f"""
    # 🔍 Rapport d’Analyse

    ## 📂 Détails
    - **Nom du projet :** {nom_projet}
    - **Client :** {client}
    - **Date limite :** {date_limite}

    ## 📑 Exigences Obligatoires
    {exigences_obligatoires}

    ## ✅ Critères d’Évaluation
    {criteres_evaluation}

    ---
    Généré par **Inox Tender**
    """

    st.download_button("Télécharger le rapport", rapport,
                       file_name="rapport_tender.md")
