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
    /* General styling */
    body {
        font-family: 'Arial', sans-serif;
    }
    .stMainBlockContainer {
        padding-top: 40px;
    }
    .stTextArea textarea { 
        border: 2px solid #007bff; 
        border-radius: 5px; 
        background-color: #2a2a2a; 
        color: #d3d3d3; 
    }
    /* Updated button styling with red theme */
    .stButton button { 
        background-color: #bd4043; 
        color: #ffffff; 
        border-radius: 5px; 
        padding: 10px 20px; 
        font-size: 16px; 
        transition: background-color 0.3s ease; 
        border: none;
    }
    .stButton button:hover { 
        background-color: #9e3639; 
    }
    .stDownloadButton button { 
        background-color: #bd4043; 
        color: #ffffff; 
        border-radius: 5px; 
        padding: 10px 20px; 
        font-size: 16px; 
        transition: background-color 0.3s ease; 
        border: none;
    }
    .stDownloadButton button:hover { 
        background-color: #9e3639; 
    }
    .analysis-section { 
        margin-bottom: 30px; 
    }
    .chat-message { 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
    }
    .user-message { 
        background-color: #3a3a3a; 
        color: #d3d3d3; 
    }
    .assistant-message { 
        background-color: #007bff; 
        color: white; 
    }
    .st-expander { 
        margin-bottom: 20px; 
        background-color: #2a2a2a; 
        border-radius: 8px; 
        padding: 20px; 
    }
    .stMarkdown { 
        font-size: 16px; 
        line-height: 1.5; 
        color: #d3d3d3; 
    }
    h1 { font-size: 36px; color: #ffffff; }
    h2 { font-size: 28px; color: #ffffff; }
    h3 { font-size: 22px; color: #ffffff; }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
        padding: 20px 30px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    }

    /* Sidebar logo container */
    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        margin-top: 0px;
    }
    .sidebar-logo {
        max-height: 125px; /* Slightly smaller for sidebar */
    }

    /* File uploader styling */
    .stFileUploader {
        background-color: #2a2a2a;
        border: 2px dashed #bd4043;
        border-radius: 8px;
        padding: 20px;
    }
    .stSuccess {
        background-color: #1a3c34;
        color: #a3d9b1;
        border-radius: 5px;
        padding: 10px;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .sidebar-logo-container { flex-direction: column; }
        .stFileUploader { padding: 10px; }
    }
</style>
"""
