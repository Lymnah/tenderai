# prompts.py

ASSISTANT_INSTRUCTIONS = """You are a highly reliable assistant specialized in analyzing public tender documents. Your role is to extract and synthesize factual information with the highest possible precision.

Do not summarize, interpret creatively, or add new information. Only extract what is explicitly written in the documents. Use examples from the prompts to guide your output format.

For each task:
- Follow the prompt format strictly.
- If specific information is not found, return the required fallback message exactly (e.g., "NO_INFO_FOUND").
- Never invent information or assume context that isn’t provided in the text.
- Maintain consistent output formatting (markdown lists, tables, sections, etc.) as requested.

Your outputs are used in a legal and professional context. Prioritize completeness, clarity, and factual integrity over style or creativity.
"""

# Client information extraction prompts
## Single file client information extraction
CLIENT_INFO_PROMPT = """
Extract the client's name, role, and contact details from "{file_name}".
Look for sections like "Client", "Adjudicator", "Issuing Organization", or similar.
Extract:
- Name: The name of the client organization or individual.
- Role: The role or title of the client (e.g., "Project Manager", "Procurement Officer").
- Contact Details: Any contact information provided, such as address, email, phone number.
If any of these are not found, indicate "Not specified".
Format the output as:
- Name: [name]
- Role: [role]
- Contact Details: [contact details]
If no client information is found, return exactly: NO_INFO_FOUND
"""

## Synthesize client information from multiple files
SYNTHESIZE_CLIENT_INFO_PROMPT = """
You have extracted client information from multiple files related to a tender process. The information is provided below, each associated with a source file.

{client_info_data}

Your task is to synthesize this data into a single, cohesive client information section.

Follow these guidelines:
1. Combine the name, role, and contact details from all files.
2. If multiple files provide the same information, use the most detailed or complete version.
3. If there are conflicts, note them (e.g., "Name: Company A (file1), Company B (file2)").
4. If a piece of information is not found in any file, indicate "Not specified".
5. Present the final information as:
- Name: [name]
- Role: [role]
- Contact Details: [contact details]
If no client information is found across all files, return exactly: NO_INFO_FOUND
"""

# Summary prompts
## Prompt for summarizing a batch of files
SUMMARY_PROMPT = """
Summarize the tender based on the provided documents, focusing on:
- **Purpose**: Overall purpose of the tender
- **Main Deliverables**: Key deliverables or items to be provided
- **Scope and Scale**: Project scope and scale
- **Timeline and Submission**: Key dates (e.g., deadlines) and submission requirements
- **Evaluation Criteria**: How bids will be evaluated
- **Contractual Conditions**: Key terms and unique clauses
- **Additional Key Details**: Include other critical information such as risks, penalties, stakeholders, or budget constraints, if specified.
Cite sources as [file name] where applicable.
If no summary can be generated due to lack of relevant information, return exactly: NO_INFO_FOUND
"""

## Prompt for combining partial summaries into a final summary
FINAL_SUMMARY_PROMPT = """
Combine the following partial summaries into a cohesive overall summary that reads naturally and ensures no information is lost:
{partial_summaries}

Additionally, incorporate the following synthesized data to ensure all critical details are included:

Synthesized Dates:
{synthesized_dates}

Synthesized Requirements:
{synthesized_requirements}

Follow these guidelines:
1. **Preserve All Unique Information**: Include all unique details from each partial summary.
2. **Merge Similar Information Intelligently**: Combine overlapping details (e.g., dates) into a single entry, retaining the most specific information.
3. **Resolve Conflicts Transparently**: If details conflict (e.g., different dates), include both and note the discrepancy (e.g., "[Conflict: Source A says X, Source B says Y]").
4. **Maintain Structure**: Use the structure from the partial summaries (e.g., Purpose, Deliverables), covering all sections. If a section is missing from some summaries, note it as "Not specified in all sources."
5. **Incorporate Synthesized Data**:
   - Include key dates from the synthesized dates in the "Timeline and Submission" section.
   - Include key requirements (e.g., mandatory, compliance, submission documents) in the "Evaluation Criteria" and "Additional Key Details" sections.
6. **Cite Sources**: Combine citations where appropriate (e.g., [file1, file2]).
7. **Ensure Cohesion**: Write the summary in a natural, flowing style.
If no summary can be generated due to lack of relevant information, return exactly: NO_INFO_FOUND
"""

# Prompt for extracting dates from a single file
DATES_PROMPT = """
Extract all dates related to the tender process from "{file_name}", including deadlines, milestones, and key events. Tender-related dates often include:
- Publication dates (e.g., "Publication Date: 19.03.2021", "Date de publication: 19.03.2021")
- Deadlines for questions (e.g., "Délai pour le dépôt des questions: 21.04.2021", "Deadline for questions: 21 April 2021")
- Submission deadlines (e.g., "Délai pour le dépôt des offres: 30.04.2021 at 12h", "Submission deadline: 30/04/2021 12:00")
- Clarification meeting dates (e.g., "Séance de clarification: upon request", "Clarification meeting: TBD")
- Adjudication or award dates (e.g., "Date de la décision d’adjudication: May 2021", "Award date: May 2021")
- Contract signing dates (e.g., "Date envisagée pour la signature du contrat: June 2021", "Contract signing: Jun 2021")
Look for dates near keywords like "deadline", "milestone", "submission", "contract", "award", "publication", "délai", "date de", "signature", or in sections labeled as timelines or schedules.
Format each as: - [date and time], [time zone if specified], [event], Source: {file_name}
If no dates are found, return exactly: NO_INFO_FOUND
"""
# Prompt to synthesize dates from all files
SYNTHESIZE_DATES_PROMPT = """
You have extracted dates from multiple files related to a tender process. The dates are provided below, each associated with a source file.

{dates_data}

Your task is to synthesize this data into a single, clean table with the following columns:
- Date (in DD.MM.YYYY format)
- Event
- Source File

Follow these guidelines:
1. Parse the dates and events from the provided data.
2. Standardize the date format to DD.MM.YYYY.
3. If a date includes a time, include it in the date column (e.g., "30.04.2021 at 12h").
4. If the same date and event are mentioned in multiple files, list it once and cite all source files (e.g., "file1, file2").
5. If there are conflicting dates for the same event, note the conflict (e.g., "30.04.2021 (file1), 01.05.2021 (file2)").
6. Sort the table in reverse chronological order (most recent date first).
7. If no dates are found or all entries are "NO_INFO_FOUND", return exactly: NO_INFO_FOUND

Present the final table in markdown format.
"""

# Prompt for extracting requirements from a single file
REQUIREMENTS_PROMPT = """
Extract all requirements from the tender document and categorize them based on their nature. Focus on identifying:

- **Submission Documents**: List all documents required for the tender submission, including any specific formats (e.g., PDF, docx, signed) or signing requirements.
- Other requirements, which you should categorize as you see fit based on the document's content. Examples of categories might include:
  - Mandatory requirements (must be met to qualify)
  - Optional requirements (preferred but not essential)
  - Compliance requirements (legal, regulatory, or security standards)
  - Financial requirements (e.g., pricing, payment terms)
  - Sustainability or social requirements (e.g., environmental or ethical standards)
  - Performance or quality requirements
  - Certifications or standards
  - Any other relevant categories you identify

For each category, list the requirements in bullet points. If a category has no requirements, indicate "No information found for this category." Use your judgment to create categories that best fit the document's content, but ensure "Submission Documents" is always included as a category, even if empty.

If no requirements are found in the document, return exactly: NO_INFO_FOUND
"""

# Prompt for extracting folder structure from a single file
FOLDER_STRUCTURE_PROMPT = """
Extract the required or recommended folder structure for tender submission from "{file_name}", if it is specified or implied.
Present the structure as a hierarchical list (like a tree), indicating:
- Folder names
- Any subfolders
- Expected contents or documents within each folder
If no folder structure is mentioned or implied in the document, return exactly: NO_INFO_FOUND
"""

# Prompt to synthesize folder structures from all files
SYNTHESIZE_FOLDER_STRUCTURE_PROMPT = """
You have extracted folder structure information from multiple files related to a tender process, along with synthesized requirements. The data is provided below:

Folder Structures:
{folder_structure_data}

Synthesized Requirements:
{requirements_data}

Your task is to create a unified folder structure that encompasses all requirements from the provided data.

Follow these guidelines:
1. If any file specifies a folder structure (i.e., folder_structure_data is not empty and not "NO_INFO_FOUND"), create a unified structure:
   - If multiple files specify the same structure, present it once.
   - If there are differences, include all unique folders and subfolders, noting conflicts (e.g., "Folder X required in file1, optional in file2").
   - Respect the exact structure as specified in the tender documents.
2. If no folder structure is specified across all files (i.e., folder_structure_data is empty or "NO_INFO_FOUND"):
   - Use the "Submission Documents" from the synthesized requirements to suggest a simple structure.
   - Place all required documents in a single folder named "Submission Documents" unless a more specific structure is implied.
   - Include any submission format details (e.g., paper/electronic) as a note under the folder.
   - Indicate that this is a suggested structure (e.g., "**Suggested Structure**").
3. Present the final folder structure as a hierarchical list in markdown format.
4. If neither a folder structure nor submission documents are found, return exactly: NO_INFO_FOUND
"""


# Prompt to synthesize requirements from all files
SYNTHESIZE_REQUIREMENTS_PROMPT = """
You have extracted requirements from multiple files related to a tender process. The requirements are categorized and provided below, each associated with a source file.

{requirements_data}

Your task is to combine these requirements into a single, cohesive list, preserving the categories identified in the per-file extractions.

Follow these guidelines:
1. Ensure "Submission Documents" is always included as a category, even if empty, and merge all submission documents and related details (e.g., formats, instructions) from different files into a single list, citing all source files (e.g., "Document X [file1, file2]").
2. For other categories, identify all unique categories across the files and merge requirements under each:
   - If the same category appears in multiple files, combine the requirements, citing all source files.
   - If requirements within a category conflict, note the discrepancy (e.g., "Requirement X (file1), Requirement Y (file2)").
   - Preserve all sub-details (e.g., formats, instructions) within each category.
3. Include all categories identified in the per-file extractions, even if they are not predefined (e.g., "Optional Requirements", "Other Information").
4. If all categories are empty or all entries are "NO_INFO_FOUND", return exactly: NO_INFO_FOUND

Present the final list in markdown format with categories and requirements.
"""


def format_prompt(prompt_template, **kwargs):
    """Format a prompt template with the given keyword arguments."""
    return prompt_template.format(**kwargs)
