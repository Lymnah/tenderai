# Tender AI

**Tender AI** is a Python application designed to streamline the analysis of tender documents using OpenAI's API. It extracts key information such as dates, requirements, folder structures, and client details from tender documents (PDF, DOCX) and presents them in a user-friendly Streamlit interface. This tool is ideal for professionals managing public or private tenders, helping to save time and improve accuracy in tender processing.

## Features

- **Document Analysis**: Extracts dates, requirements, folder structures, and client information from tender documents.
- **AI-Powered**: Leverages OpenAI's API for intelligent data extraction and synthesis.
- **User-Friendly Interface**: Built with Streamlit, featuring tabs, progress bars, and a clean UI.
- **Batch Processing**: Supports processing multiple documents in batches with multi-threading for efficiency.
- **Simulation Mode**: Allows testing without making actual API calls.
- **Logging**: Detailed logs for debugging and monitoring API interactions.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.8 or higher
- **Git**: For cloning the repository
- **OpenAI API Key**: Required for accessing OpenAI's API
- **Assistant ID**: The ID of your OpenAI assistant (configured in `config.py`)

## Installation

Follow these steps to set up and run Tender AI on your local machine.

### 1. Clone the Repository

Clone the repository from GitHub to your local machine:

```
git clone https://github.com/your-username/inox-tender-ai.git
cd inox-tender-ai
```

### 2. Set Up a Virtual Environment

It’s recommended to use a virtual environment to manage dependencies and avoid conflicts with other projects:

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Install all required Python packages listed in `requirements.txt`:

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The `requirements.txt` file includes all necessary dependencies, such as `streamlit`, `openai`, `pypdf`, `python-docx`, `tenacity`, and `python-dotenv`.

### 4. Configure Environment Variables

Create a `.env` file in the project root to store sensitive information like your OpenAI API key:

```plaintext
OPENAI_API_KEY=your-openai-api-key-here
```

### 5. Set Up the Assistant ID

Edit the `config.py` file to include your OpenAI assistant ID:

```python
ASSISTANT_ID = "your-assistant-id-here"
```

You can find your assistant ID in the OpenAI dashboard under the Assistants section.

## Usage

### Running the Application

Start the Streamlit application with the following command:

```
python -m streamlit run src/app.py
```

### Accessing the App

Once the app is running, open your web browser and navigate to:

```plaintext
http://localhost:8501
```

### Using the App

1. **Upload Documents**:

   - Go to the "Upload File" tab.
   - Upload your tender documents (PDF or DOCX format).
   - Click "Analyze Files" to start the analysis.

2. **View Results**:

   - Switch to the "Analysis" tab to see extracted information (dates, requirements, folder structures, client info).
   - The app will display a synthesized summary of the tender documents.

3. **Monitor Progress**:
   - Check the "Logs" tab for detailed logs of the analysis process, including API interactions and any errors.

## Project Structure

```plaintext
inox-tender-ai/
├── app.py                  # Main Streamlit application
├── tender_analyzer.py      # Core logic for tender analysis
├── config.py               # Configuration settings (API keys, assistant ID)
├── file_handler.py         # File upload and processing utilities
├── ui.py                   # UI components for Streamlit
├── utils.py                # General utility functions
├── prompts.py              # AI prompts for OpenAI API
├── requirements.txt        # List of Python dependencies
├── .gitignore              # Git ignore file
├── README.md               # Project documentation
└── resources/
    └── your_company_logo.png  # Logo for the app
```

## Troubleshooting

- **Streamlit Not Found**: Ensure you’ve activated your virtual environment and installed dependencies with `pip install -r requirements.txt`.
- **OpenAI API Errors**:
  - Verify that your API key is correctly set in the `.env` file.
  - Check that the `ASSISTANT_ID` in `config.py` matches your OpenAI assistant.
  - Ensure you have sufficient API credits and are within rate limits.
- **Document Processing Issues**:
  - Confirm that your documents are in PDF or DOCX format.
  - Check the logs in the "Logs" tab for detailed error messages.
- **Slow Performance**: The app processes documents in batches. For large documents, consider reducing the batch size in `tender_analyzer.py` (`BATCH_SIZE`).

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and commit them with a clear message:
   ```
   git commit -m "feat: add your feature description"
   ```
4. Push your changes to your fork:
   ```
   git push origin feature/your-feature-name
   ```
5. Open a pull request with a detailed description of your changes.

Please follow the conventional commit format for commit messages (e.g., `feat:`, `fix:`, `chore:`).

## License

This project is licensed under the [Apache License 2.0](LICENSE).

© 2025 [lymnah](https://github.com/lymnah) and [Inox Communication](https://github.com/InoxCommunication)  
You are free to use, modify, and distribute this software, with or without changes, under the terms of the license.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface.
- Powered by [OpenAI](https://openai.com/) for AI-driven document analysis.
- Inspired by the need to simplify tender document processing for professionals.
