# ui.py
import streamlit as st
from io import BytesIO
import PyPDF2
from config import ASSISTANT_ID, SIMULATION_MODE
import time
from utils import replace_citations
from tender_analyzer import analyze_tender
import openai


def render_main_content(uploaded_files, uploaded_file_ids, file_id_to_name, thread_id):
    st.title("INOX Tender AI - Assistance aux Appels d'Offres")

    if uploaded_files:
        # Analysis with enhanced feedback
        st.subheader("Analyzing Documents...")

        # Progress bar and status log
        progress_bar = st.progress(0)
        status_text = st.empty()
        progress_log = st.empty()

        all_dates, all_requirements, all_folder_structures, summary_response = (
            analyze_tender(
                uploaded_file_ids,
                file_id_to_name,
                progress_bar,
                status_text,
                progress_log,
            )
        )

        # Clear the progress indicators
        status_text.empty()
        progress_log.empty()

        # Display Results in Dedicated Sections
        st.subheader("📊 Tender Analysis Results")

        # Important Dates Section
        st.markdown("### 🕒 Important Dates and Milestones")
        with st.expander("View Dates and Milestones", expanded=True):
            for dates in all_dates:
                st.markdown(dates, unsafe_allow_html=False)
                st.markdown("<hr>", unsafe_allow_html=True)

        # Tender Summary Section
        st.markdown("### 📝 Tender Summary")
        with st.expander("View Tender Summary", expanded=True):
            st.markdown(summary_response, unsafe_allow_html=False)

        # Technical Requirements Section
        st.markdown("### 🔧 Technical Requirements")
        with st.expander("View Technical Requirements", expanded=True):
            for requirements in all_requirements:
                st.markdown(requirements, unsafe_allow_html=False)
                st.markdown("<hr>", unsafe_allow_html=True)

        # Folder Structure Section
        st.markdown("### 📁 Required Folder Structure")
        with st.expander("View Folder Structure", expanded=True):
            for folder_structure in all_folder_structures:
                st.markdown(folder_structure, unsafe_allow_html=False)
                st.markdown("<hr>", unsafe_allow_html=True)

        # Download Full Report
        full_report = (
            "Tender Analysis Report\n\n"
            "## Important Dates and Milestones\n" + "\n\n".join(all_dates) + "\n\n"
            "## Tender Summary\n" + summary_response + "\n\n"
            "## Technical Requirements\n" + "\n\n".join(all_requirements) + "\n\n"
            "## Required Folder Structure\n" + "\n\n".join(all_folder_structures)
        )
        st.download_button(
            "📥 Download Full Report",
            full_report,
            file_name="tender_analysis_report.txt",
            mime="text/plain",
        )

        # Chat Interface
        st.subheader("💬 Chat with Assistant")
        if "thread_id" not in locals():
            st.info("Please upload and analyze a document first.")
        else:
            # Initialize chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # Display chat history
            for chat in st.session_state.chat_history:
                st.markdown(
                    f"<div class='chat-message user-message'><strong>You:</strong> {chat['user']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='chat-message assistant-message'><strong>Assistant:</strong> {chat['assistant']}</div>",
                    unsafe_allow_html=True,
                )

            # Chat input form
            with st.form(key="chat_form"):
                user_query = st.text_area(
                    "Ask a question about the analyzed documents:", height=100
                )
                submit_button = st.form_submit_button("Send")

                if submit_button and user_query.strip():
                    # Streamline loading indicator for chat as well
                    spinner_placeholder = st.empty()
                    if SIMULATION_MODE:
                        # Simulate chat response time (1 seconds)
                        with spinner_placeholder.container():
                            st.spinner("Generating response... (Status: mock)")
                        time.sleep(1)
                        assistant_response = (
                            "This is a mock chat response to your query: " + user_query
                        )
                    else:
                        openai.beta.threads.messages.create(
                            thread_id=thread_id, role="user", content=user_query
                        )
                        run = openai.beta.threads.runs.create(
                            thread_id=thread_id,
                            assistant_id=ASSISTANT_ID.strip(),
                        )
                        while True:
                            run_status = openai.beta.threads.runs.retrieve(
                                thread_id=thread_id, run_id=run.id
                            )
                            with spinner_placeholder.container():
                                st.spinner(
                                    f"Generating response... (Status: {run_status.status})"
                                )
                            if run_status.status == "completed":
                                break
                            time.sleep(0.5)  # Reduced polling interval
                        spinner_placeholder.empty()

                        messages = openai.beta.threads.messages.list(
                            thread_id=thread_id
                        )
                        assistant_response = next(
                            (
                                msg.content[0].text.value
                                for msg in messages.data
                                if msg.role == "assistant"
                            ),
                            "No response generated.",
                        )

                    assistant_response = replace_citations(
                        assistant_response, file_id_to_name
                    )
                    st.session_state.chat_history.append(
                        {"user": user_query, "assistant": assistant_response}
                    )
                    st.rerun()  # Refresh to show updated chat history
