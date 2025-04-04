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
        with open("resources/mock_response.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Step 1: Split into top-level sections based on # headings
        top_level_sections = {}
        current_top_section = None
        current_top_content = []
        for line in content.splitlines():
            if line.startswith("# "):
                if current_top_section:
                    top_level_sections[current_top_section] = "\n".join(
                        current_top_content
                    ).strip()
                current_top_section = line[2:].strip()
                current_top_content = []
            else:
                current_top_content.append(line)
        if current_top_section:
            top_level_sections[current_top_section] = "\n".join(
                current_top_content
            ).strip()

        # Step 2: Split top-level sections into subsections based on ## headings
        sections = {}
        for top_section, top_content in top_level_sections.items():
            current_subsection = top_section  # Default to top-level section title
            current_subcontent = []
            for line in top_content.splitlines():
                if line.startswith("## "):
                    if current_subsection and current_subcontent:
                        sections[current_subsection] = "\n".join(
                            current_subcontent
                        ).strip()
                    current_subsection = line[3:].strip()
                    current_subcontent = []
                else:
                    current_subcontent.append(line)
            if current_subsection and current_subcontent:
                sections[current_subsection] = "\n".join(current_subcontent).strip()

        # Step 3: Map prompt_type to the appropriate section
        prompt_type_lower = prompt_type.lower()
        if "client info" in prompt_type_lower:
            return sections.get("👤 Client Information", "No client information found.")
        elif "summary" in prompt_type_lower:
            return sections.get("📝 Tender Summary", "No summary found.")
        elif "dates" in prompt_type_lower or "timeline" in prompt_type_lower:
            return sections.get(
                "📅 All Important Dates and Milestones", "No dates found."
            )
        elif "requirements" in prompt_type_lower:
            return sections.get(
                "🔧 All Technical Requirements", "No requirements found."
            )
        elif "folder structure" in prompt_type_lower:
            return sections.get(
                "📁 Consolidated Required Folder Structure",
                "No folder structure found.",
            )
        elif "additional key details" in prompt_type_lower:
            tender_summary = sections.get("📝 Tender Summary", "")
            if not tender_summary:
                return "No additional details found."
            # Extract "Additional Key Details" from "📝 Tender Summary"
            lines = tender_summary.splitlines()
            additional_details = []
            in_additional_details = False
            for line in lines:
                if line.startswith("#### Additional Key Details"):
                    in_additional_details = True
                elif line.startswith("#### ") and in_additional_details:
                    in_additional_details = False
                elif in_additional_details and line.strip():
                    additional_details.append(line)
            return (
                "\n".join(additional_details).strip()
                if additional_details
                else "No additional details found."
            )
        else:
            return "No response generated for prompt type: " + prompt_type

    except FileNotFoundError:
        print("Mock response file 'resources/mock_response.md' not found.")
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
