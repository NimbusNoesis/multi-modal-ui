# Phi-4 Multimodal Interface

This project provides a web interface and API for Microsoft's Phi-4 multimodal model, allowing users to interact with the model through a user-friendly Streamlit application.

## Features

- **Image Processing**

  - Upload images from your device
  - Process images from URLs
  - Customize model prompts for specific analysis needs

- **Audio Processing**
  - Upload audio files
  - Process audio from URLs
  - Record audio directly in the application
  - Automatic transcription and translation capabilities

## Architecture

The project consists of two main components:

1. **Flask API (`api/api.py`)**

   - Backend service that interfaces directly with the Phi-4 model
   - Handles image and audio processing requests
   - Manages model loading and inference

2. **Streamlit UI (`app.py`)**
   - User-friendly web interface
   - Handles file uploads and temporary storage
   - Communicates with the Flask API
   - Displays results in a clean format

## Requirements

- Python 3.8+
- PyTorch with CUDA support
- Transformers library
- Flask
- Streamlit
- Microsoft Phi-4 multimodal model

## Installation

1. Clone this repository:

   ```
   git clone git@github.com:NimbusNoesis/multi-modal-ui.git
   cd multi-modal-ui
   ```

2. Install CUDA 

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```


## Usage

### Starting the API

1. Run the Flask API:
   ```
   cd api
   python api.py
   ```
   The API will start on http://localhost:5000

### Starting the Streamlit App

1. Run the Streamlit application:
   ```
   streamlit run app.py
   ```
   The web interface will be available at http://localhost:8501

### Using the Interface

1. **Image Processing**:

   - Select "Image Processing" tab
   - Choose input method (upload or URL)
   - Optionally customize the prompt
   - Click "Process Image" to analyze

2. **Audio Processing**:
   - Select "Audio Processing" tab
   - Choose input method (upload, URL, or record)
   - Optionally customize the prompt
   - Click "Process Audio" to transcribe/translate

## API Endpoints

- `POST /process_image`: Process an image

  ```json
  {
    "image_url": "path/to/image.jpg",
    "prompt": "Optional custom prompt"
  }
  ```

- `POST /process_audio`: Process an audio file

  ```json
  {
    "audio_url": "path/to/audio.wav",
    "prompt": "Optional custom prompt"
  }
  ```

- `GET /health`: Check API status

## License

[Add license information]

## Acknowledgements

This project uses Microsoft's Phi-4 multimodal model. Please ensure you comply with Microsoft's usage policies when using this application.
