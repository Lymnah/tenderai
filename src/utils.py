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
            content = f.read()

        # Split the content into sections based on headers
        sections = {}
        current_section = None
        current_content = []
        for line in content.splitlines():
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        # Map prompt_type to the appropriate section
        prompt_type_lower = prompt_type.lower()
        if "client info" in prompt_type_lower:
            return sections.get("Client Information", "No client information found.")
        elif "summary" in prompt_type_lower:
            # Combine relevant sections for the summary
            summary_sections = [
                sections.get("Tender Summary", ""),
                sections.get("Timeline and Submission", ""),
                sections.get("Evaluation Criteria", ""),
                sections.get("Contractual Conditions", ""),
            ]
            return "\n\n".join(section for section in summary_sections if section)
        elif "dates" in prompt_type_lower or "timeline" in prompt_type_lower:
            return sections.get("All Important Dates and Milestones", "No dates found.")
        elif "requirements" in prompt_type_lower:
            return sections.get("Technical Requirements", "No requirements found.")
        elif "folder structure" in prompt_type_lower:
            return sections.get(
                "Consolidated Required Folder Structure", "No folder structure found."
            )
        elif "additional key details" in prompt_type_lower:
            return sections.get(
                "Additional Key Details", "No additional details found."
            )
        else:
            return "No response generated for prompt type: " + prompt_type

    except FileNotFoundError:
        st.error("Mock response file 'resources/mock_response.txt' not found.")
        return "No response generated."


def replace_citations(text, file_id_to_name, intended_file_name=None):
    if not file_id_to_name:
        return text  # Avoid processing if file_id_to_name is empty

    def replace_citation(match):
        citation = match.group(0)
        for file_id, original_name in file_id_to_name.items():
            if file_id in citation:
                return f"【{original_name}】"
        if len(file_id_to_name) == 1:
            return f"【{list(file_id_to_name.values())[0]}】"
        return citation

    # Replace citations in the format 【...】
    text = re.sub(r"【.*?】", replace_citation, text)

    # Replace temporary filenames with more specificity
    for file_id, original_name in file_id_to_name.items():
        temp_filename_pattern = rf"tmp\w+\.(?:pdf|docx)"
        if re.search(temp_filename_pattern, text):
            text = re.sub(temp_filename_pattern, original_name, text)

    # Optionally preserve asterisks or use a safer pattern
    text = re.sub(r"\*(\w+)\*", r"\1", text)

    # Correct file name references with word boundaries
    if intended_file_name:
        for file_id, file_name in file_id_to_name.items():
            if file_name != intended_file_name:
                pattern = rf"\b{re.escape(file_name)}\b"
                text = re.sub(pattern, intended_file_name, text)

    return text
