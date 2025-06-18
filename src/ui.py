# ui.py
import streamlit as st
from io import BytesIO
import PyPDF2
from config import ASSISTANT_ID
import time
from utils import replace_citations
from tender_analyzer import analyze_tender
import openai
import re


def render_per_file_section(data_list, file_ids, file_id_to_name, section_title):
    """Helper function to render per-file analysis sections."""
    consolidated_content = ""
    for i, file_id in enumerate(file_ids):
        file_name = file_id_to_name[file_id]
        content = data_list[i] if i < len(data_list) else ""
        if content.strip() and content.strip() != "NO_INFO_FOUND":
            content = replace_citations(
                content, file_id_to_name, intended_file_name=file_name
            )
            consolidated_content += (
                f"{section_title} from {file_name}:\n{content}\n\n---\n\n"
            )
    return consolidated_content


def render_main_content(
    uploaded_files, uploaded_file_ids, file_id_to_name, thread_id, analysis_results
):
    # Extract analysis results
    synthesized_dates = analysis_results.get("synthesized_dates", "")
    synthesized_requirements = analysis_results.get("synthesized_requirements", "")
    synthesized_folder_structure = analysis_results.get(
        "synthesized_folder_structure", ""
    )
    synthesized_client_info = analysis_results.get("synthesized_client_info", "")
    summary_response = analysis_results["summary_response"]
    all_dates = analysis_results["all_dates"]
    all_requirements = analysis_results["all_requirements"]
    all_folder_structures = analysis_results["all_folder_structures"]
    progress_log_messages = analysis_results["progress_log_messages"]

    # Consolidated Analysis Section
    st.header("Tender Analysis", divider="grey")

    # Client Information
    st.subheader("👤 Client Information")
    with st.expander("View Client Information", expanded=True):
        if (
            synthesized_client_info.strip()
            and synthesized_client_info.strip() != "NO_INFO_FOUND"
        ):
            st.markdown(synthesized_client_info, unsafe_allow_html=False)
        else:
            st.markdown("No client information found.")

    # Tender Summary
    st.subheader("📝 Tender Summary")
    with st.expander("View Tender Summary", expanded=True):
        if summary_response.strip() and summary_response.strip() != "NO_INFO_FOUND":
            summary_response = replace_citations(summary_response, file_id_to_name)
            st.markdown(summary_response, unsafe_allow_html=False)
        else:
            st.markdown("No summary generated from the provided files.")

    # Consolidated Dates
    st.subheader("📅 All Important Dates and Milestones")
    with st.expander("View dates", expanded=True):
        if synthesized_dates.strip() and synthesized_dates.strip() != "NO_INFO_FOUND":
            st.markdown(synthesized_dates, unsafe_allow_html=False)
        else:
            st.markdown("No important dates found across all files.")

    # Consolidated Requirements
    st.subheader("🔧 All Technical Requirements")
    with st.expander("View requirements", expanded=True):
        if (
            synthesized_requirements.strip()
            and synthesized_requirements.strip() != "NO_INFO_FOUND"
        ):
            st.markdown(synthesized_requirements, unsafe_allow_html=False)
        else:
            st.markdown("No technical requirements found across all files.")

    # Consolidated Folder Structure
    st.subheader("📁 Arboresence structure")
    with st.expander("View Arboresence structure", expanded=True):
        if (
            synthesized_folder_structure.strip()
            and synthesized_folder_structure.strip() != "NO_INFO_FOUND"
        ):
            st.markdown(synthesized_folder_structure, unsafe_allow_html=False)
        else:
            st.markdown("No folder structure information found across all files.")

    # Per File Analysis Section only if not in simulation mode
    if not st.session_state.simulation_mode:
        # Per-File Analysis Section
        st.header("📄 Per-File Analysis", divider=True)

        # Per-File Dates
        st.subheader("📅 Important Dates and Milestones per File")
        with st.expander("View Dates per File", expanded=False):
            consolidated_dates = render_per_file_section(
                all_dates, uploaded_file_ids, file_id_to_name, "Dates"
            )
            if consolidated_dates:
                st.markdown(consolidated_dates, unsafe_allow_html=False)
            else:
                st.markdown("No important dates extracted from the provided files.")

        # Per-File Requirements
        st.subheader("🔧 Technical Requirements per File")
        with st.expander("View Requirements per File", expanded=False):
            consolidated_requirements = render_per_file_section(
                all_requirements, uploaded_file_ids, file_id_to_name, "Requirements"
            )
            if consolidated_requirements:
                st.markdown(consolidated_requirements, unsafe_allow_html=False)
            else:
                st.markdown("No technical requirements extracted from the provided files.")

        # Per-File Folder Structure
        st.subheader("📁 Required Folder Structure per File")
        with st.expander("View Folder Structure per File", expanded=False):
            consolidated_folder_structure = render_per_file_section(
                all_folder_structures,
                uploaded_file_ids,
                file_id_to_name,
                "Folder Structure",
            )
            if consolidated_folder_structure:
                st.markdown(consolidated_folder_structure, unsafe_allow_html=False)
            else:
                st.markdown("No folder structure extracted from the provided files.")

    # Update Download Report with Correct Order
    full_report = "Tender Analysis Report\n\n"
    # Consolidated Tender Analysis Sections
    if (
        synthesized_client_info.strip()
        and synthesized_client_info.strip() != "NO_INFO_FOUND"
    ):
        full_report += "## Client Information\n" + synthesized_client_info + "\n\n"
    if summary_response.strip() and summary_response.strip() != "NO_INFO_FOUND":
        full_report += "## Tender Summary\n" + summary_response + "\n\n"
    if synthesized_dates.strip() and synthesized_dates.strip() != "NO_INFO_FOUND":
        full_report += (
            "## All Important Dates and Milestones\n" + synthesized_dates + "\n\n"
        )
    if (
        synthesized_requirements.strip()
        and synthesized_requirements.strip() != "NO_INFO_FOUND"
    ):
        full_report += (
            "## All Technical Requirements\n" + synthesized_requirements + "\n\n"
        )
    if (
        synthesized_folder_structure.strip()
        and synthesized_folder_structure.strip() != "NO_INFO_FOUND"
    ):
        full_report += (
            "## Arborescence Structure\n"
            + synthesized_folder_structure
            + "\n\n"
        )

    # Per File Analysis Section only if not in simulation mode
    if not st.session_state.simulation_mode:
        # Per-File Analysis Sections
        if consolidated_dates:
            full_report += (
                "## Important Dates and Milestones per File\n" + consolidated_dates + "\n\n"
            )
        if consolidated_requirements:
            full_report += (
                "## Technical Requirements per File\n" + consolidated_requirements + "\n\n"
            )
        if consolidated_folder_structure:
            full_report += (
                "## Required Folder Structure per File\n"
                + consolidated_folder_structure
                + "\n\n"
            )
            
    st.download_button(
        "Download Full Report",
        full_report,
        file_name="tender_analysis_report.md",
        mime="text/plain",
    )
