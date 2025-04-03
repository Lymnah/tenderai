# config.py
import os
import streamlit as st
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Load API Key and Assistant ID using os.getenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Check if API key and assistant ID are required (not in simulation mode)
# Simulation mode is managed in app.py via st.session_state.simulation_mode
if "simulation_mode" in st.session_state and st.session_state.simulation_mode:
    OPENAI_API_KEY = None
    ASSISTANT_ID = None
else:
    if not OPENAI_API_KEY:
        st.error(
            "⚠️ OpenAI API Key is missing! Please set `OPENAI_API_KEY` in your environment variables."
        )
        st.stop()
    if not ASSISTANT_ID:
        st.error(
            "⚠️ Assistant ID is missing! Set `OPENAI_ASSISTANT_ID` in your environment variables."
        )
        st.stop()

# Custom CSS for styling
CUSTOM_CSS = """
<style>
    /* Custom CSS for Streamlit App */

    /* Define CSS Variables for Theme Consistency */
    :root {
        --primary-color: #bd4043;    /* Red theme for buttons */
        --primary-hover: #9e3639;    /* Darker red for hover */
        --secondary-color: #007bff;  /* Blue for assistant messages, etc. */
        --background-dark: #2a2a2a; /* Dark background */
        --text-color: #d3d3d3;      /* Light text */
        --sidebar-bg: #1a1a1a;      /* Sidebar background */
        --success-bg: #1a3c34;      /* Success message background */
        --success-text: #a3d9b1;    /* Success message text */
        --border-radius: 5px;       /* Consistent border radius */
        --padding-standard: 20px;   /* Standard padding */
    }

    /* General Styling */
    body {
        font-family: 'Arial', sans-serif;
    }
    .stMainBlockContainer {
        padding-top: 40px;
    }
    .stMarkdown {
        font-size: 16px;
        line-height: 1.5;
        color: var(--text-color);
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    h1 { font-size: 36px; }
    h2 { font-size: 28px; }
    h3 { font-size: 22px; }

    /* Button Styling */
    .stButton button,
    .stDownloadButton button {
        background-color: var(--primary-color);
        color: #ffffff;
        border-radius: var(--border-radius);
        padding: 10px 20px;
        font-size: 16px;
        transition: background-color 0.3s ease;
        border: none;
    }
    .stButton button:hover,
    .stDownloadButton button:hover {
        background-color: var(--primary-hover);
    }

    /* Text Area Styling */
    .stTextArea textarea {
        border: 2px solid var(--secondary-color);
        border-radius: var(--border-radius);
        background-color: var(--background-dark);
        color: var(--text-color);
    }

    /* Chat Message Styling */
    .chat-message {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .user-message {
        background-color: #3a3a3a;
        color: var(--text-color);
    }
    .assistant-message {
        background-color: var(--secondary-color);
        color: #ffffff;
    }

    /* Expander Styling */
    .st-expander {
        margin-bottom: 20px;
        background-color: var(--background-dark);
        border-radius: 8px;
        padding: var(--padding-standard);
    }

    /* Sidebar Styling */
    .sidebar .sidebar-content {
        background-color: var(--sidebar-bg);
        padding: 20px 30px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    }
    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 30px;
        margin-top: 0px;
    }
    .sidebar-logo {
        max-height: 125px;
    }

    /* File Uploader Styling */
    .stFileUploader {
        background-color: var(--background-dark);
        border: 2px dashed var(--primary-color);
        border-radius: 8px;
        padding: var(--padding-standard);
    }
    .stSuccess {
        background-color: var(--success-bg);
        color: var(--success-text);
        border-radius: var(--border-radius);
        padding: 10px;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .sidebar-logo-container {
            flex-direction: column;
        }
        .stFileUploader {
            padding: 10px;
        }
    }

    /* Main Block Custom Styles */
    .stMain .stVerticalBlock h2 {
        margin: 0.5em 0 1em;
    }
    .stVerticalBlock hr {
        background: #333 !important;
        margin: -3rem 0 2rem !important;
        height: 1px !important;
    }
    .stVerticalBlock h3 {
        padding-left: 1.2em;
        font-size: 1.65rem;
        font-weight: 100;
    }
    .stVerticalBlock .stExpander {
        margin-bottom: 2em;
    }
    .stVerticalBlock .stExpander details {
        background: rgb(34, 41, 46);
        border: none;
    }
    .stVerticalBlock .stDownloadButton {
        margin: 3em 0;
        text-align: center;
    }

    /* Table Styling to Prevent Overflow */
    .stMain .stVerticalBlock table {
        max-width: 100%;
        width: 100%;
        table-layout: auto;
        border-collapse: collapse;
    }
    .stMain .stVerticalBlock table th,
    .stMain .stVerticalBlock table td {
        word-break: break-word;
        hyphens: auto;
        padding: 8px;
        text-align: left;
    }
    .stMain .stVerticalBlock table th:nth-child(1),
    .stMain .stVerticalBlock table td:nth-child(1) {
        width: 15%; /* Date column */
    }
    .stMain .stVerticalBlock table th:nth-child(2),
    .stMain .stVerticalBlock table td:nth-child(2) {
        width: 50%; /* Event column */
    }
    .stMain .stVerticalBlock table th:nth-child(3),
    .stMain .stVerticalBlock table td:nth-child(3) {
        width: 35%; /* Source File column */
    }

    /* Form Styling */
    .st-emotion-cache-qcpnpn {
        border: none;
        background: #22292e;
    }
    .stVerticalBlock .stForm .stElementContainer:last-child {
        align-self: flex-end;
    }
</style>
"""
