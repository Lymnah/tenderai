import streamlit as st
from config import CUSTOM_CSS, ASSISTANT_ID, TENDERAI_VERSION
from file_handler import upload_files
from tender_analyzer import (
    analyze_tender,
    synthesize_results,
    BATCH_SIZE,
    MAX_CONCURRENT_REQUESTS,
)
from ui import render_main_content
from utils import load_image_as_base64
import openai
import logging

# Set page config
st.set_page_config(page_title="INOX Tender AI", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Display the logo at the top, replacing the title
your_company_logo = load_image_as_base64("resources/tenderAI_white.png")
if your_company_logo:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; padding: 50px 20px; margin-bottom: 20px">
            <img src="{your_company_logo}" style="max-width: 400px; height: auto;" alt="Your Company Logo">
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.warning("Logo could not be loaded. Check the file path.")

# Retrieve assistant details from OpenAI API
try:
    if ASSISTANT_ID:
        assistant = openai.beta.assistants.retrieve(ASSISTANT_ID)
        assistant_model = assistant.model
        assistant_temperature = (
            assistant.temperature
            if assistant.temperature is not None
            else "Not specified"
        )
        assistant_top_p = (
            assistant.top_p if assistant.top_p is not None else "Not specified"
        )
    else:
        raise ValueError("ASSISTANT_ID cannot be None")
except Exception as e:
    st.error(f"Failed to retrieve assistant details: {str(e)}")
    assistant_model = "Unknown"
    assistant_temperature = "Unknown"
    assistant_top_p = "Unknown"

# Sidebar with logo and assistant settings
with st.sidebar:
    your_company_logo = load_image_as_base64("resources/your_company_logo.png")
    if your_company_logo:
        st.markdown(
            f"""
            <div class="sidebar-logo-container">
                <img src="{your_company_logo}" class="sidebar-logo" alt="Your Company Logo">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Logo could not be loaded. Check the file path.")

    # Add Simulation Mode toggle
    st.header("Simulation Mode", divider="red")
    if "simulation_mode" not in st.session_state:
        st.session_state.simulation_mode = False
    st.session_state.simulation_mode = st.checkbox(
        "Enable Simulation Mode", value=st.session_state.simulation_mode
    )

    st.header("Assistant Settings", divider="red")

    st.markdown("<div class='setting-label'>Version</div>", unsafe_allow_html=True)
    st.code(TENDERAI_VERSION, language="text")

    st.markdown("<div class='setting-label'>Model</div>", unsafe_allow_html=True)
    st.code(assistant_model, language="text")

    st.markdown("<div class='setting-label'>Temperature</div>", unsafe_allow_html=True)
    st.code(assistant_temperature)

    st.markdown("<div class='setting-label'>Top P</div>", unsafe_allow_html=True)
    st.code(assistant_top_p)


# Initialize session state
if "start_analysis" not in st.session_state:
    st.session_state.start_analysis = False
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "uploaded_file_ids" not in st.session_state:
    st.session_state.uploaded_file_ids = []
if "file_id_to_name" not in st.session_state:
    st.session_state.file_id_to_name = {}
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {
        "all_dates": [],
        "all_requirements": [],
        "all_folder_structures": [],
        "all_client_infos": [],
        "summary_response": "",
        "progress_log_messages": [],
        "synthesized_dates": "",
        "synthesized_requirements": "",
        "synthesized_folder_structure": "",
        "synthesized_client_info": "",
    }
if "thread_id" not in st.session_state:
    st.session_state.thread_id = (
        openai.beta.threads.create().id
        if not st.session_state.simulation_mode
        else "mock_thread_id"
    )
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "new_files_to_process" not in st.session_state:
    st.session_state.new_files_to_process = []
if "analysis_completed" not in st.session_state:
    st.session_state.analysis_completed = False

# Create tabs with static labels
tab1, tab2, tab3 = st.tabs(["Upload File", "Analysis", "Logs"])

# Tab 1: Upload File
with tab1:
    if st.session_state.is_analyzing:
        st.info("Analysis in progress. Please wait...", icon="ℹ️")
    else:
        # Show notification if analysis is complete
        if st.session_state.analysis_completed:
            st.success("Analysis complete! Check the results in the Analysis tab.")

    st.header("📂 Upload Documents")
    uploaded_files_input = st.file_uploader(
        "Add your documents (PDF, DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        analyze_button = st.button("Analyze Files", use_container_width=True)
    with col2:
        clear_button = st.button("Clear All Files", use_container_width=True)

# Handle file uploads
if uploaded_files_input:
    existing_file_names = {f.name for f in st.session_state.uploaded_files}
    new_files = [
        file for file in uploaded_files_input if file.name not in existing_file_names
    ]
    duplicate_files = [
        file.name for file in uploaded_files_input if file.name in existing_file_names
    ]
    if new_files:
        st.session_state.uploaded_files.extend(new_files)
        st.success(f"{len(new_files)} new file(s) uploaded.")
    if duplicate_files:
        st.warning(f"Duplicate files ignored: {', '.join(duplicate_files)}")
    st.session_state.uploader_key += 1

# Handle clear
if clear_button:
    st.session_state.uploaded_files = []
    st.session_state.uploaded_file_ids = []
    st.session_state.file_id_to_name = {}
    st.session_state.analysis_results = {
        "all_dates": [],
        "all_requirements": [],
        "all_folder_structures": [],
        "all_client_infos": [],
        "summary_response": "",
        "progress_log_messages": [],
        "synthesized_dates": "",
        "synthesized_requirements": "",
        "synthesized_folder_structure": "",
        "synthesized_client_info": "",
    }
    st.session_state.thread_id = (
        openai.beta.threads.create().id
        if not st.session_state.simulation_mode
        else "mock_thread_id"
    )
    st.session_state.is_analyzing = False
    st.session_state.start_analysis = False
    st.session_state.new_files_to_process = []
    st.session_state.uploader_key += 1
    st.session_state.analysis_completed = False
    st.rerun()

# Tab 2: Analysis
with tab2:
    st.markdown('<a name="analysis-tab"></a>', unsafe_allow_html=True)
    if st.session_state.is_analyzing:
        with st.spinner("Analyzing..."):
            st.subheader("Processing...")
            progress_bar = st.empty()
            status_text = st.empty()
            files_text = st.empty()

            if st.session_state.start_analysis:
                st.session_state.start_analysis = False
                new_files_to_process = st.session_state.new_files_to_process
                if new_files_to_process:
                    new_file_ids, new_file_id_to_name = upload_files(
                        new_files_to_process,
                        simulation_mode=st.session_state.simulation_mode,
                    )
                    st.session_state.uploaded_file_ids.extend(new_file_ids)
                    st.session_state.file_id_to_name.update(new_file_id_to_name)

                    total_files = len(new_file_ids)
                    (
                        new_dates,
                        new_requirements,
                        new_folder_structures,
                        new_client_infos,
                        new_summary_response,
                        new_progress_log_messages,
                    ) = analyze_tender(
                        new_file_ids,
                        new_file_id_to_name,
                        progress_bar,
                        status_text,
                        files_text,
                        st.session_state.uploaded_files,
                        total_files,
                        simulation_mode=st.session_state.simulation_mode,
                    )

                    st.session_state.analysis_results["all_dates"].extend(new_dates)
                    st.session_state.analysis_results["all_requirements"].extend(
                        new_requirements
                    )
                    st.session_state.analysis_results["all_folder_structures"].extend(
                        new_folder_structures
                    )
                    st.session_state.analysis_results["all_client_infos"].extend(
                        new_client_infos
                    )
                    st.session_state.analysis_results["summary_response"] = (
                        new_summary_response
                    )
                    st.session_state.analysis_results["progress_log_messages"].extend(
                        new_progress_log_messages
                    )

                    logger = logging.getLogger("synthesis")
                    synthesized_results = synthesize_results(
                        st.session_state.analysis_results["all_dates"],
                        st.session_state.analysis_results["all_requirements"],
                        st.session_state.analysis_results["all_folder_structures"],
                        st.session_state.analysis_results["all_client_infos"],
                        st.session_state.uploaded_file_ids,
                        st.session_state.file_id_to_name,
                        logger,
                        simulation_mode=st.session_state.simulation_mode,
                    )
                    st.session_state.analysis_results.update(synthesized_results)

                st.session_state.is_analyzing = False
                st.session_state.new_files_to_process = []
                st.session_state.analysis_completed = True
                st.rerun()
    else:
        if any(
            st.session_state.analysis_results[key]
            for key in ["all_dates", "all_requirements", "all_folder_structures"]
        ):
            render_main_content(
                st.session_state.uploaded_files,
                st.session_state.uploaded_file_ids,
                st.session_state.file_id_to_name,
                st.session_state.thread_id,
                st.session_state.analysis_results,
            )
        else:
            st.info("No analysis results yet. Upload files and click 'Analyze Files'.")

# Tab 3: Logs
with tab3:
    st.header("📜 Progress Log", divider=True)
    st.markdown(
        "<div class='progress-log'>"
        + "<br>".join(st.session_state.analysis_results["progress_log_messages"])
        + "</div>",
        unsafe_allow_html=True,
    )

# Trigger analysis
if (
    analyze_button
    and st.session_state.uploaded_files
    and not st.session_state.is_analyzing
):
    st.session_state.new_files_to_process = [
        file
        for file in st.session_state.uploaded_files
        if file.name
        not in {
            st.session_state.file_id_to_name.get(fid, "")
            for fid in st.session_state.uploaded_file_ids
        }
    ]
    st.session_state.start_analysis = True
    st.session_state.is_analyzing = True
    st.rerun()
