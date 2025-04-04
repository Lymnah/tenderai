# config.py
import os
import streamlit as st
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Check if API key and assistant ID are required (not in simulation mode)
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

# Custom CSS for styling, adapted from Obsidian "Things" theme
# Define common values as variables for clarity and reusability
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Inter, Ubuntu, sans-serif"  # Obsidian --font-text-theme
LINE_HEIGHT = "1.6"  # Obsidian --line-height
BORDER_RADIUS = "8px"  # Consistent border radius (Obsidian --radius-m)
PADDING_STANDARD = "20px"  # Standard padding (retained from original)
SHADOW_S = "0px 1px 2px rgba(0, 0, 0, 0.121), 0px 3.4px 6.7px rgba(0, 0, 0, 0.179), 0px 15px 30px rgba(0, 0, 0, 0.3)"  # Obsidian --shadow-s
BACKGROUND_BASE_30 = "#35393e"  # Obsidian --color-base-30
BACKGROUND_BASE_10 = "#282c34"  # Obsidian --color-base-10

CUSTOM_CSS = f"""
<style>
    /* Custom CSS for Streamlit App, adapted from Obsidian "Things" Theme (Dark Mode) */

    /* CSS Variables for Theme Consistency */
    :root {{
        /* Colors from Obsidian Things Theme (Dark Mode) */
        --primary-color: #fb464c;    /* Red theme for buttons (Obsidian --color-red) */
        --primary-hover: #d13c41;    /* Darker red for hover */
        --secondary-color: #027aff;  /* Blue for assistant messages (Obsidian --color-blue) */
        --background-dark: #1c2127;  /* Main background (Obsidian --color-base-00) */
        --background-secondary: {BACKGROUND_BASE_10}; /* Secondary background (Obsidian --color-base-10) */
        --text-color: hsl(212, 15%, 90%); /* Text color (approximated --text-normal for dark mode) */
        --text-muted: hsl(212, 15%, 78%); /* Muted text (Obsidian --text-muted) */
        --sidebar-bg: #181c20;      /* Sidebar background (Obsidian --color-base-20) */
        --success-bg: rgba(68, 207, 110, 0.2); /* Success message background (Obsidian --color-green with opacity) */
        --success-text: #ffffff;    /* Success message text (Obsidian --tag-font-color-d) */
        --border-radius: {BORDER_RADIUS};
        --padding-standard: {PADDING_STANDARD};
        --shadow-s: {SHADOW_S};
        /* Obsidian heading colors */
        --h1-color: hsl(212, 15%, 78%); /* --text-normal in dark mode */
        --h2-color: #ff82b2; /* --color-pink */
        --h3-color: #027aff; /* --color-blue */
        --h4-color: #e0de71; /* --color-yellow */
    }}

    /* General Styling */
    body {{
        font-family: {FONT_FAMILY};
        background-color: var(--background-dark);
        color: var(--text-color);
    }}

    .stMainBlockContainer {{
        padding-top: 40px;
        max-width: 40rem; /* Obsidian --line-width */
        margin: 0 auto;
    }}

    .stMarkdown {{
        font-size: 16px;
        line-height: {LINE_HEIGHT};
        color: var(--text-color);
    }}

    /* Headings */
    h1, h2, h3, h4, h5, h6 {{
        font-family: {FONT_FAMILY};
        line-height: {LINE_HEIGHT};
    }}

    .stMain .stVerticalBlock h2 {{
        font-size: 2.2rem; /* Larger and clear */
        color: var(--h1-color);
        font-weight: 700; /* Stronger weight for prominence */
        text-transform: uppercase; /* ALL CAPS for emphasis */
        margin-bottom: 0.75rem;
        /* margin: 0.5em 0 1em; */
    }}

    .stMain .stVerticalBlock h3 {{
        font-size: 2rem; /* Clearly smaller than h1 */
        color: var(--h1-color);
        font-weight: 600;
        margin-bottom: 1rem;
        /* padding-left: 1.2em; */
        /* font-size: 1.2rem; */ /* Obsidian --h3-size */
        /* font-weight: 600; */ /* Obsidian default for h3 */
    }}

    .stMain .stVerticalBlock h4 {{
        font-size: 1.6rem; /* Clearly smaller than h2 */
        color: var(--h2-color);
        font-weight: 600;
        padding-bottom: 2px;
        margin-bottom: 0.4rem;
    }}

    .stMain .stVerticalBlock h5 {{
        font-size: 1.2rem; /* Obsidian --h3-size */
        color: var(--h3-color); /* Obsidian --h3-color (blue) */
        font-weight: 600; /* Obsidian --h3-weight */
    }}

    .stMain .stVerticalBlock h6 {{
        font-size: 1.1rem; /* Obsidian --h4-size */
        color: var(--h4-color); /* Obsidian --h4-color (yellow) */
        font-weight: 500; /* Obsidian --h4-weight */
        text-transform: uppercase; /* Obsidian --h4-transform */
    }}

    /* Main Block Layout */
    .stMain .block-container {{
        max-width: 900px !important; /* Increase the width of the main block */
    }}

    /* Sidebar Styling */
    [data-testid="stSidebarContent"] {{
        background-color: var(--background-secondary);
        padding: 20px 30px;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-s);
    }}

    .sidebar-logo-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 30px;
        margin-top: 0px;
    }}

    .sidebar-logo {{
        max-height: 125px;
        border-radius: 4px; /* Obsidian image border-radius */
    }}

    /* Change font color of text inside st.code blocks in the sidebar */
    [data-testid="stSidebarContent"] [data-testid="stCode"] code {{
        color: var(--text-color) !important; /* Use the theme's text color for general text */
    }}

    /* Specifically target numbers to ensure they are also changed */
    [data-testid="stSidebarContent"] [data-testid="stCode"] code .token.number {{
        color: var(--text-color) !important; /* Use the theme's text color for numbers */
    }}

    /* Horizontal Rules */
    .stSidebar .stVerticalBlock hr {{
        background: {BACKGROUND_BASE_30} !important; /* Obsidian --color-base-30 */
        margin: -3rem 0 2rem !important;
        height: 1px !important;
    }}

    .stVerticalBlock hr {{
        background: {BACKGROUND_BASE_30} !important; /* Obsidian --color-base-30 */
        margin: -1.5rem 0 2rem !important;
        height: 1px !important;
    }}

    /* Buttons */
    .stButton button,
    .stDownloadButton button {{
        background-color: var(--primary-color);
        color: #ffffff;
        border-radius: var(--border-radius);
        padding: 10px 20px;
        font-size: 16px;
        transition: background-color 0.3s ease;
        border: none;
        box-shadow: var(--shadow-s);
    }}

    .stButton button:hover,
    .stDownloadButton button:hover {{
        background-color: var(--primary-hover);
    }}

    .stVerticalBlock .stDownloadButton {{
        margin: 3em 0;
        text-align: center;
    }}

    /* Text Area */
    .stTextArea textarea {{
        border: 2px solid var(--secondary-color);
        border-radius: var(--border-radius);
        background-color: var(--background-secondary);
        color: var(--text-color);
        font-family: {FONT_FAMILY};
    }}

    /* Chat Messages */
    .chat-message {{
        padding: 15px;
        border-radius: var(--border-radius);
        margin-bottom: 15px;
        box-shadow: var(--shadow-s);
    }}

    .user-message {{
        background-color: {BACKGROUND_BASE_30}; /* Obsidian --color-base-30 */
        color: var(--text-color);
    }}

    .assistant-message {{
        background-color: var(--secondary-color);
        color: #ffffff;
    }}

    /* Expanders */
    .st-expander {{
        margin-bottom: 20px;
        background-color: var(--background-secondary);
        border-radius: var(--border-radius);
        padding: var(--padding-standard);
        box-shadow: var(--shadow-s);
    }}

    .stVerticalBlock .stExpander {{
        margin-bottom: 2em;
    }}

    .stVerticalBlock .stExpander details {{
        background: var(--background-dark); /* Obsidian --color-base-10 */
        border: none;
    }}

    /* File Uploader */
    .stFileUploader {{
        background-color: var(--background-secondary);
        border: 2px dashed var(--primary-color);
        border-radius: var(--border-radius);
        padding: var(--padding-standard);
    }}

    /* Style the inner dropzone area behind the text and icon */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: var(--background-secondary);
    }}

    .stSuccess {{
        background-color: var(--success-bg);
        color: var(--success-text);
        border-radius: var(--border-radius);
        padding: 10px;
    }}

    /* Tables */
    .stMain .stVerticalBlock table {{
        max-width: 100%;
        width: 100%;
        table-layout: auto;
        border-collapse: collapse;
        background-color: var(--background-secondary);
    }}

    .stMain .stVerticalBlock table th,
    .stMain .stVerticalBlock table td {{
        word-break: break-word;
        hyphens: auto;
        padding: 8px;
        text-align: left;
        color: var(--text-color);
    }}

    .stMain .stVerticalBlock table th:nth-child(1),
    .stMain .stVerticalBlock table td:nth-child(1) {{
        width: 15%; /* Date column */
    }}

    .stMain .stVerticalBlock table th:nth-child(2),
    .stMain .stVerticalBlock table td:nth-child(2) {{
        width: 50%; /* Event column */
    }}

    .stMain .stVerticalBlock table th:nth-child(3),
    .stMain .stVerticalBlock table td:nth-child(3) {{
        width: 35%; /* Source File column */
    }}

    /* Forms */
    .st-emotion-cache-qcpnpn {{
        border: none;
        background: {BACKGROUND_BASE_10}; /* Obsidian --color-base-10 */
    }}

    .stVerticalBlock .stForm .stElementContainer:last-child {{
        align-self: flex-end;
    }}

    /* Mobile Responsiveness */
    @media (max-width: 768px) {{
        .sidebar-logo-container {{
            flex-direction: column;
        }}
        .stFileUploader {{
            padding: 10px;
        }}
    }}

    /* Remove padding from list items */
    .st-emotion-cache-seewz2 li {{
        padding: 0px;
    }}
    .st-emotion-cache-1clstc5 {{
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }}
    .stMain .stVerticalBlock h4 {{
        color: #fb464c;
        margin-bottom: 1rem;
        margin-top: 1.5em;
    }}
    .st-emotion-cache-seewz2 a {{
        color: rgb(251, 70, 76);
    }}
    .stTextArea textarea {{
        border: 2px rgb(251, 70, 76);
    }}
    [data-testid="stSidebarContent"] {{
        padding: 0;
    }}
</style>
"""
