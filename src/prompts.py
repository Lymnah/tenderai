# prompts.py

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

# Prompt for extracting requirements from a single file
REQUIREMENTS_PROMPT = """
Extract all requirements from the tender document and categorize them as follows:
- **Mandatory Requirements**: Must be met to qualify.
- **Optional Requirements**: Additional or preferred but not essential.
- **Compliance Requirements**: Legal, regulatory, security, or compliance standards.
- **Financial Requirements**: Financial conditions (e.g., pricing, payment terms).
- **Sustainability and Social Requirements**: Environmental, sustainability, social, or ethical standards.
- **Performance and Quality Requirements**: Performance metrics or quality standards.
- **Certifications and Standards**: Required certifications or industry standards.
- **Other Requirements**: Any requirements not fitting the above categories.
List details under each category where applicable. If no requirements are found for any category, return exactly: NO_INFO_FOUND
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

# Prompt for summarizing a batch of files
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

# Prompt for combining partial summaries into a final summary
FINAL_SUMMARY_PROMPT = """
Combine the following partial summaries into a cohesive overall summary that reads naturally and ensures no information is lost:
{partial_summaries}
Follow these guidelines:
1. **Preserve All Unique Information**: Include all unique details from each partial summary.
2. **Merge Similar Information Intelligently**: Combine overlapping details (e.g., dates) into a single entry, retaining the most specific information.
3. **Resolve Conflicts Transparently**: If details conflict (e.g., different dates), include both and note the discrepancy (e.g., "[Conflict: Source A says X, Source B says Y]").
4. **Maintain Structure**: Use the structure from the partial summaries (e.g., Purpose, Deliverables), covering all sections. If a section is missing from some summaries, note it as "Not specified in all sources."
5. **Cite Sources**: Combine citations where appropriate (e.g., [file1, file2]).
6. **Ensure Cohesion**: Write the summary in a natural, flowing style.
If no summary can be generated due to lack of relevant information, return exactly: NO_INFO_FOUND
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
6. Sort the table chronologically by date.
7. If no dates are found or all entries are "NO_INFO_FOUND", return exactly: NO_INFO_FOUND

Present the final table in markdown format.
"""

# Prompt to synthesize requirements from all files
SYNTHESIZE_REQUIREMENTS_PROMPT = """
You have extracted requirements from multiple files related to a tender process. The requirements are categorized and provided below, each associated with a source file.

{requirements_data}

Your task is to combine these requirements into a single, cohesive list, categorized as follows:
- **Mandatory Requirements**
- **Optional Requirements**
- **Compliance Requirements**
- **Financial Requirements**
- **Sustainability and Social Requirements**
- **Performance and Quality Requirements**
- **Certifications and Standards**
- **Other Requirements**

Follow these guidelines:
1. Merge similar requirements from different files into a single entry, citing all source files (e.g., "Requirement X [file1, file2]").
2. If requirements conflict, note the discrepancy (e.g., "Requirement X (file1), Requirement Y (file2)").
3. Preserve the categorization from the original extracts.
4. If a category has no requirements across all files, omit it.
5. If all categories are empty or all entries are "NO_INFO_FOUND", return exactly: NO_INFO_FOUND

Present the final list in markdown format with categories and requirements.
"""

# Prompt to synthesize folder structures from all files
SYNTHESIZE_FOLDER_STRUCTURE_PROMPT = """
You have extracted folder structure information from multiple files related to a tender process. The structures are provided below, each associated with a source file.

{folder_structure_data}

Your task is to create a unified folder structure that encompasses all requirements from the provided data.

Follow these guidelines:
1. If multiple files specify the same folder structure, present it once.
2. If there are differences, create a structure that includes all unique folders and subfolders.
3. Note any conflicts or variations between files (e.g., "Folder X required in file1, optional in file2").
4. If no folder structure is specified across all files, return exactly: NO_INFO_FOUND

Present the final folder structure as a hierarchical list in markdown format.
"""


def format_prompt(prompt_template, **kwargs):
    """Format a prompt template with the given keyword arguments."""
    return prompt_template.format(**kwargs)
