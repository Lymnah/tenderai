# config.py
import os
import dotenv
import streamlit as st

# Load environment variables
dotenv.load_dotenv()

# Global variable to toggle simulation mode
SIMULATION_MODE = (
    False  # Set to True to use mock responses, False to use real OpenAI API
)

# Load API Key and Assistant ID (only required if not in simulation mode)
if not SIMULATION_MODE:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        st.error(
            "⚠️ OpenAI API Key is missing! Please set `OPENAI_API_KEY` in your environment variables."
        )
        st.stop()

    ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
    if not ASSISTANT_ID:
        st.error(
            "⚠️ Assistant ID is missing! Set `OPENAI_ASSISTANT_ID` in your environment variables."
        )
        st.stop()
else:
    OPENAI_API_KEY = None
    ASSISTANT_ID = None

# Custom CSS for styling
CUSTOM_CSS = """
<style>
    .stTextArea textarea { 
        border: 2px solid #007bff; 
        border-radius: 5px; 
        background-color: #2a2a2a; 
        color: #d3d3d3; 
    }
    .stButton button { 
        background-color: #007bff; 
        color: white; 
        border-radius: 5px; 
        padding: 10px 20px; 
        font-size: 16px; 
        transition: background-color 0.3s ease; 
    }
    .stButton button:hover { 
        background-color: #0056b3; 
    }
    .stDownloadButton button { 
        background-color: #28a745; 
        color: white; 
        border-radius: 5px; 
        padding: 10px 20px; 
        font-size: 16px; 
        transition: background-color 0.3s ease; 
    }
    .stDownloadButton button:hover { 
        background-color: #218838; 
    }
    .analysis-section { 
        margin-bottom: 20px; 
    }
    .chat-message { 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); 
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
        padding: 15px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3); 
    }
    .st-expander div { 
        padding: 10px; 
    }
    .stMarkdown { 
        margin-bottom: 15px; 
        font-size: 16px; 
        color: #d3d3d3; 
        line-height: 1.6; 
    }
    h1 { 
        font-size: 32px; 
        color: #ffffff; 
        text-align: center; 
        margin-bottom: 20px; 
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5); 
    }
    h2 { 
        font-size: 24px; 
        color: #ffffff; 
        margin-top: 30px; 
    }
    h3 { 
        font-size: 20px; 
        color: #ffffff; 
    }
    hr { 
        border: 1px solid #444; 
        margin: 20px 0; 
    }
    .section-heading { 
        font-size: 20px; 
        margin-bottom: 10px; 
        color: #007bff; 
        font-weight: bold; 
    }
    .spinner-text { 
        font-size: 16px; 
        color: #d3d3d3; 
    }
    .stSpinner {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    .stSpinner > div {
        font-size: 16px;
        color: #d3d3d3;
        margin-top: 10px;
    }
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
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        margin-top: 0px;
    }
    .sidebar-logo {
        max-height: 50px; /* Slightly smaller for sidebar */
    }
    /* File uploader styling */
    .stFileUploader {
        background-color: #2a2a2a;
        border: 2px dashed #007bff;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    .stFileUploader div {
        color: #d3d3d3;
    }
    /* Success and error messages */
    .stSuccess {
        background-color: #1a3c34;
        color: #a3d9b1;
        border-radius: 5px;
        padding: 10px;
    }
    .stError {
        background-color: #4a1a1a;
        color: #ff9999;
        border-radius: 5px;
        padding: 10px;
    }
    .stWarning {
        background-color: #4a3c1a;
        color: #ffcc99;
        border-radius: 5px;
        padding: 10px;
    }
    /* Progress log styling */
    .progress-log {
        background-color: #2a2a2a;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
        max-height: 200px;
        overflow-y: auto;
        color: #d3d3d3;
    }
</style>
"""
