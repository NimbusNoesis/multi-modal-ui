import streamlit as st
import requests
import tempfile
import os
import io
import base64
from PIL import Image
import soundfile as sf
from audio_recorder_streamlit import audio_recorder
import shutil
from urllib.parse import urlparse
import uuid


class Phi4Interface:
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        # Create temp directory if it doesn't exist in session state
        if "temp_dir" not in st.session_state:
            st.session_state["temp_dir"] = tempfile.mkdtemp(prefix="streamlit_phi4_")
        self.temp_dir = st.session_state["temp_dir"]

        # Ensure the directory exists
        os.makedirs(self.temp_dir, exist_ok=True)

    def save_uploaded_file(self, uploaded_file):
        """Save an uploaded file to temp directory with proper extension"""
        if uploaded_file is None:
            return None

        try:
            # Generate unique filename
            file_ext = os.path.splitext(uploaded_file.name)[1]
            temp_filename = f"{str(uuid.uuid4())}{file_ext}"
            temp_path = os.path.join(self.temp_dir, temp_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            # Save the file
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            return temp_path
        except Exception as e:
            st.error(f"Error saving uploaded file: {str(e)}")
            return None

    def save_url_file(self, url):
        """Download and save a file from URL to temp directory"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch file: HTTP {response.status_code}")

            # Try to get extension from URL or content-type
            content_type = response.headers.get("content-type", "")
            if "image" in content_type:
                ext = ".jpg" if "jpeg" in content_type else ".png"
            elif "audio" in content_type:
                ext = ".wav"
            else:
                # Try to get extension from URL
                ext = os.path.splitext(urlparse(url).path)[1]
                if not ext:
                    ext = ".tmp"

            # Generate unique filename
            temp_filename = f"{str(uuid.uuid4())}{ext}"
            temp_path = os.path.join(self.temp_dir, temp_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            # Save file
            with open(temp_path, "wb") as f:
                f.write(response.content)

            return temp_path
        except Exception as e:
            st.error(f"Error downloading file: {str(e)}")
            return None

    def save_audio_recording(self, audio_bytes):
        """Save recorded audio to temp directory"""
        if audio_bytes is None:
            return None

        try:
            temp_filename = f"{str(uuid.uuid4())}.wav"
            temp_path = os.path.join(self.temp_dir, temp_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            # Save the file
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            return temp_path
        except Exception as e:
            st.error(f"Error saving audio recording: {str(e)}")
            return None

    def process_image(self, image_path, custom_prompt=None):
        """Process image through API"""
        try:
            response = requests.post(
                f"{self.api_url}/process_image",
                json={"image_url": image_path, "prompt": custom_prompt},
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def process_audio(self, audio_path, custom_prompt=None):
        """Process audio through API"""
        try:
            response = requests.post(
                f"{self.api_url}/process_audio",
                json={"audio_url": audio_path, "prompt": custom_prompt},
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


class StreamlitApp:
    def __init__(self):
        st.set_page_config(
            page_title="Phi-4 Multimodal Interface",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Initialize interface
        if "phi4" not in st.session_state:
            st.session_state["phi4"] = Phi4Interface()
        self.phi4 = st.session_state["phi4"]

        # Set up sidebar
        self.setup_sidebar()

    def setup_sidebar(self):
        """Setup the sidebar with additional information and controls"""
        st.sidebar.title("About")
        st.sidebar.info(
            """
            This application uses Microsoft's Phi-4 multimodal model to:
            - Analyze images
            - Process audio (transcription & translation)

            The model supports both local and remote files.
            """
        )

        st.sidebar.title("Settings")
        # Add any additional settings here

        st.sidebar.title("Status")
        if st.sidebar.button("Check API Status"):
            try:
                response = requests.get(f"{self.phi4.api_url}/health")
                if response.status_code == 200:
                    st.sidebar.success("API is running")
                else:
                    st.sidebar.error("API is not responding correctly")
            except Exception:
                st.sidebar.error("Could not connect to API")

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if "temp_dir" in st.session_state:
                temp_dir = st.session_state["temp_dir"]
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    del st.session_state["temp_dir"]
        except Exception as e:
            st.error(f"Error cleaning up temporary files: {str(e)}")

    def run(self):
        st.title("Phi-4 Multimodal Interface")

        # Create tabs for different functionalities
        tab1, tab2 = st.tabs(["Image Processing", "Audio Processing"])

        with tab1:
            self.image_interface()

        with tab2:
            self.audio_interface()

    def image_interface(self):
        st.header("Image Processing")

        # Input method selection
        input_method = st.radio("Select input method:", ["Upload Image", "Image URL"])

        file_path = None

        if input_method == "Upload Image":
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=["jpg", "jpeg", "png"],
                help="Supported formats: JPG, JPEG, PNG",
            )
            if uploaded_file:
                file_path = self.phi4.save_uploaded_file(uploaded_file)
                if file_path:
                    st.image(file_path, caption="Uploaded Image", use_column_width=True)
        else:
            image_url = st.text_input(
                "Enter image URL:", help="Enter the URL of an image to process"
            )
            if image_url:
                file_path = self.phi4.save_url_file(image_url)
                if file_path:
                    st.image(file_path, caption="Image from URL", use_column_width=True)

        with st.expander("Advanced Options", expanded=False):
            custom_prompt = st.text_area(
                "Custom prompt:",
                "What is shown in this image?",
                help="Customize how the model should analyze the image",
            )

        col1, col2 = st.columns([1, 4])
        with col1:
            process_button = st.button("Process Image", type="primary")

        if process_button and file_path:
            with st.spinner("Processing image..."):
                result = self.phi4.process_image(file_path, custom_prompt)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Processing complete!")
                    with st.container():
                        st.markdown("### Results")
                        st.markdown(result["response"])
        elif process_button and not file_path:
            st.warning("Please provide an image first!")

    def audio_interface(self):
        st.header("Audio Processing")

        # Input method selection
        input_method = st.radio(
            "Select input method:", ["Upload Audio", "Audio URL", "Record Audio"]
        )

        file_path = None

        if input_method == "Upload Audio":
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=["wav", "mp3", "flac"],
                help="Supported formats: WAV, MP3, FLAC",
            )
            if uploaded_file:
                file_path = self.phi4.save_uploaded_file(uploaded_file)
                if file_path:
                    st.audio(file_path)
        elif input_method == "Audio URL":
            audio_url = st.text_input(
                "Enter audio URL:", help="Enter the URL of an audio file to process"
            )
            if audio_url:
                file_path = self.phi4.save_url_file(audio_url)
                if file_path:
                    st.audio(file_path)
        else:
            st.info("Click the microphone button below to start recording")
            audio_bytes = audio_recorder()
            if audio_bytes:
                file_path = self.phi4.save_audio_recording(audio_bytes)
                if file_path:
                    st.audio(file_path)

        with st.expander("Advanced Options", expanded=False):
            custom_prompt = st.text_area(
                "Custom prompt:",
                "Transcribe the audio to text, and then translate the audio to French. Use <sep> as a separator between the original transcript and the translation.",
                help="Customize how the model should process the audio",
            )

        col1, col2 = st.columns([1, 4])
        with col1:
            process_button = st.button("Process Audio", type="primary")

        if process_button and file_path:
            with st.spinner("Processing audio..."):
                result = self.phi4.process_audio(file_path, custom_prompt)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Processing complete!")
                    with st.container():
                        st.markdown("### Results")

                        # Split response if it contains separator
                        if "<sep>" in result["response"]:
                            transcript, translation = result["response"].split("<sep>")
                            st.markdown("#### Original Transcript")
                            st.markdown(transcript.strip())
                            st.markdown("#### French Translation")
                            st.markdown(translation.strip())
                        else:
                            st.markdown(result["response"])
        elif process_button and not file_path:
            st.warning("Please provide an audio file first!")


if __name__ == "__main__":
    app = StreamlitApp()
    try:
        app.run()
    finally:
        app.cleanup()
