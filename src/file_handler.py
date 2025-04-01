import streamlit as st
import openai
import os
import tempfile
import time


def upload_files(uploaded_files, simulation_mode):
    uploaded_file_ids = []
    failed_uploads = []
    total_files = len(uploaded_files)
    file_id_to_name = {}

    # Use a single spinner for the entire upload process
    with st.spinner(""):
        # Placeholder for dynamic status text
        status_text = st.empty()
        # Progress bar for visual feedback
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            # Update status text
            file_size = (
                f"{file.size / 1024:.1f}KB"
                if file.size < 1024 * 1024
                else f"{file.size / (1024 * 1024):.1f}MB"
            )
            status_text.text(
                f"Uploading file {i+1} of {total_files}: {file.name} ({file_size})..."
            )

            # Update progress bar
            progress_bar.progress((i + 1) / total_files)

            file_extension = os.path.splitext(file.name)[1]
            if file_extension not in [".pdf", ".docx"]:
                st.error(f"Unsupported file type: {file_extension}")
                failed_uploads.append(file.name)
                continue

            if simulation_mode:
                # Mock file ID
                mock_file_id = f"mock_file_id_{i}"
                uploaded_file_ids.append(mock_file_id)
                file_id_to_name[mock_file_id] = file.name
            else:
                # Create temporary file
                temp_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=file_extension
                    ) as temp_file:
                        temp_file.write(file.getvalue())
                        temp_file_path = temp_file.name

                    with open(temp_file_path, "rb") as f:
                        uploaded_file = openai.files.create(
                            file=f, purpose="assistants"
                        )
                        uploaded_file_ids.append(uploaded_file.id)
                        file_id_to_name[uploaded_file.id] = file.name

                except Exception as e:
                    st.error(f"Failed to upload file {file.name}: {str(e)}")
                    failed_uploads.append(file.name)
                    continue
                finally:
                    # Clean up temporary file
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                        except Exception as e:
                            st.warning(
                                f"Failed to clean up temporary file {temp_file_path}: {str(e)}"
                            )

        # Clear the status text and progress bar
        status_text.empty()
        progress_bar.empty()

    # Display summary of failed uploads, if any
    if failed_uploads:
        st.warning(
            f"Successfully uploaded {len(uploaded_file_ids)} out of {total_files} file(s). "
            f"Failed to upload: {', '.join(failed_uploads)}"
        )

    return uploaded_file_ids, file_id_to_name
