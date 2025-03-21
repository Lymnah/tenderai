# utils.py
import base64
import re
import streamlit as st


def load_image_as_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        st.error(
            f"Image file {image_path} not found. Please ensure it is in the resources/ directory."
        )
        return None


def load_mock_response(prompt_type):
    try:
        with open("resources/mock_response.txt", "r", encoding="utf-8") as f:
            base_response = f.read()
        # Simulate different responses based on prompt type
        if "dates" in prompt_type.lower():
            return f"Mock Dates Response for {prompt_type}:\n- Date: 2025-04-15 14:00, Time Zone: CET, Event: Submission Deadline, Source: mock_file.pdf"
        elif "requirements" in prompt_type.lower():
            return f"Mock Requirements Response for {prompt_type}:\n**Mandatory Requirements**\n- Must have ISO 9001 certification [mock_file.pdf]\n**Optional Requirements**\n- None [mock_file.pdf]\n**Legal Requirements**\n- Compliance with GDPR [mock_file.pdf]\n**Financial Requirements**\n- Minimum budget of 500k EUR [mock_file.pdf]\n**Security Requirements**\n- Must have cybersecurity certification [mock_file.pdf]\n**Certifications**\n- ISO 9001 [mock_file.pdf]"
        elif "folder structure" in prompt_type.lower():
            return f"Mock Folder Structure Response for {prompt_type}:\n- Main Submission Folder\n  - Technical Docs: Technical Proposal, Specs Sheet [mock_file.pdf]\n  - Financial Docs: Budget Plan [mock_file.pdf]"
        elif "summary" in prompt_type.lower():
            return f"Mock Tender Summary Response for {prompt_type}:\nThe client is seeking a comprehensive solution for a construction project, requiring technical expertise, financial stability, and compliance with legal standards. Key deliverables include a detailed technical proposal and a financial plan. The project aims to build a new facility by 2026, with a focus on sustainability. [mock_file.pdf]"
        return base_response
    except FileNotFoundError:
        st.error("Mock response file 'resources/mock_response.txt' not found.")
        return "No response generated."


def replace_citations(text, file_id_to_name):
    def replace_citation(match):
        citation = match.group(0)
        # Extract the file ID or temporary filename from the citation
        for file_id, original_name in file_id_to_name.items():
            if file_id in citation:
                return f"【{original_name}】"
        # If there's only one file, use its name as a fallback
        if len(file_id_to_name) == 1:
            return f"【{list(file_id_to_name.values())[0]}】"
        return citation

    # Replace citations in the format 【...】
    text = re.sub(r"【.*?】", replace_citation, text)
    # Replace temporary filenames (e.g., tmplgazt62r.docx) with original filenames
    for file_id, original_name in file_id_to_name.items():
        temp_filename_pattern = rf"tmp\w+\.(?:pdf|docx)"
        text = re.sub(temp_filename_pattern, original_name, text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove single asterisks
    return text
