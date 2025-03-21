# app.py
import streamlit as st
import openai
from config import CUSTOM_CSS, SIMULATION_MODE
import PyPDF2
from io import BytesIO
from file_handler import upload_files
from ui import render_main_content
from utils import load_image_as_base64

# Set page config as the first Streamlit command
st.set_page_config(page_title="INOX Tender AI", layout="wide")

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Render the sidebar directly in app.py
with st.sidebar:
    your_company_logo = load_image_as_base64("resources/your_company_logo.png")
    client_company_logo = load_image_as_base64("resources/client_company_logo.png")

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

# Main logic
if uploaded_files:
    # Upload files and get file IDs
    uploaded_file_ids, file_id_to_name = upload_files(uploaded_files)

    # Create a new thread for analysis
    if not SIMULATION_MODE:
        thread_id = openai.beta.threads.create().id
    else:
        thread_id = "mock_thread_id"

    # Render the main content
    render_main_content(uploaded_files, uploaded_file_ids, file_id_to_name, thread_id)
