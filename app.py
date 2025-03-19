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


def extract_text_from_pdf(uploaded_file):
    """Extract text from a PDF file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        loader = PyPDFLoader(tmp_file.name)
        pages = loader.load_and_split()
        return " ".join([page.page_content for page in pages])


def extract_text_from_docx(uploaded_file):
    """Extract text from a DOCX file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(uploaded_file.read())
        return docx2txt.process(tmp_file.name)


def create_retriever(docs):
    """Create FAISS vector store retriever for document search"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=200)
    chunks = text_splitter.split_text(docs)

    vectorstore = FAISS.from_texts(chunks, OpenAIEmbeddings())
    return vectorstore.as_retriever()


def extract_metadata(text):
    """Extracts project name, client, and deadline using GPT-4"""
    prompt = PromptTemplate(
        template="Analyse ce texte et identifie:\n- Le nom du projet\n- Le client\n- La date limite de soumission\nTexte:\n{text}",
        input_variables=["text"]
    )
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    chain = RetrievalQA.from_chain_type(llm=llm, retriever=create_retriever(
        text), chain_type="stuff", return_source_documents=False)

    response = chain.invoke(
        {"query": "Identifie les informations clés du projet"})
    return response


def analyse_document(content):
    """Analyze document content using RAG-based retrieval"""
    retriever = create_retriever(content)
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    chain = RetrievalQA.from_chain_type(
        llm=llm, retriever=retriever, chain_type="stuff", return_source_documents=False)
    response = chain.invoke(
        {"query": "Quelles sont les exigences obligatoires de cet appel d'offres?"})
    return response


if uploaded_files:
    st.success(f"{len(uploaded_files)} fichiers téléchargés.")
    st.write("Analyse en cours... ⏳")

    full_text = ""
    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            full_text += extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            full_text += extract_text_from_docx(uploaded_file)

    metadata = extract_metadata(full_text)
    exigences_obligatoires = analyse_document(full_text)

    rapport = f"""
    # 🔍 Rapport d’Analyse

    ## 📂 Détails
    - **Nom du projet :** {metadata.get("nom_projet", "Inconnu")}
    - **Client :** {metadata.get("client", "Inconnu")}
    - **Date limite :** {metadata.get("date_limite", "Non spécifiée")}

    ## 📑 Exigences Obligatoires
    {exigences_obligatoires}

    ---
    Généré par **Inox Tender**
    """

    st.download_button("Télécharger le rapport", rapport,
                       file_name="rapport_tender.md")
