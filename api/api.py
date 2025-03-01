from flask import Flask, request, jsonify
import requests
import torch
import os
import io
from PIL import Image
import soundfile as sf
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
from urllib.parse import urlparse
import pathlib

app = Flask(__name__)


class Phi4Model:
    def __init__(self):
        self.model_path = "microsoft/Phi-4-multimodal-instruct"
        self.processor = AutoProcessor.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="cuda",
            torch_dtype="auto",
            trust_remote_code=True,
            attn_implementation="flash_attention_2",
        ).cuda()
        self.generation_config = GenerationConfig.from_pretrained(self.model_path)
        self.user_prompt = "<|user|>"
        self.assistant_prompt = "<|assistant|>"
        self.prompt_suffix = "<|end|>"

    def load_file(self, url):
        """Handle both local and remote files"""
        parsed_url = urlparse(url)

        # Handle local file
        if parsed_url.scheme in ["", "file"]:
            if parsed_url.scheme == "file":
                # Remove 'file://' and any leading slashes
                path = parsed_url.path.lstrip("/")
            else:
                path = url

            # Convert to absolute path
            abs_path = os.path.abspath(path)

            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Local file not found: {abs_path}")

            return open(abs_path, "rb")

        # Handle remote file
        else:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers)
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch remote file: HTTP {response.status_code} - {response.reason}"
                )
            return io.BytesIO(response.content)

    def process_image(self, image_url, custom_prompt=None):
        try:
            prompt = f"{self.user_prompt}<|image_1|>{custom_prompt or 'What is shown in this image?'}{self.prompt_suffix}{self.assistant_prompt}"

            # Load and open image
            file_obj = self.load_file(image_url)
            image = Image.open(file_obj)

            # Process with the model
            inputs = self.processor(text=prompt, images=image, return_tensors="pt").to(
                "cuda:0"
            )

            generate_ids = self.model.generate(
                **inputs,
                max_new_tokens=1000,
                generation_config=self.generation_config,
            )
            generate_ids = generate_ids[:, inputs["input_ids"].shape[1] :]
            response = self.processor.batch_decode(
                generate_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            # Clean up
            file_obj.close()

            return response
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    def process_audio(self, audio_url, custom_prompt=None):
        try:
            default_prompt = "Transcribe the audio to text, and then translate the audio to French. Use <sep> as a separator between the original transcript and the translation."
            prompt = f"{self.user_prompt}<|audio_1|>{custom_prompt or default_prompt}{self.prompt_suffix}{self.assistant_prompt}"

            # Load audio file
            file_obj = self.load_file(audio_url)

            # Read audio file
            audio, samplerate = sf.read(file_obj)

            # Process with the model
            inputs = self.processor(
                text=prompt, audios=[(audio, samplerate)], return_tensors="pt"
            ).to("cuda:0")

            generate_ids = self.model.generate(
                **inputs,
                max_new_tokens=1000,
                generation_config=self.generation_config,
            )
            generate_ids = generate_ids[:, inputs["input_ids"].shape[1] :]
            response = self.processor.batch_decode(
                generate_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            # Clean up
            file_obj.close()

            return response
        except Exception as e:
            raise Exception(f"Error processing audio: {str(e)}")


# Initialize the model
model = Phi4Model()


@app.route("/process_image", methods=["POST"])
def process_image():
    try:
        data = request.get_json()
        if not data or "image_url" not in data:
            return jsonify({"error": "image_url is required"}), 400

        custom_prompt = data.get("prompt")
        response = model.process_image(data["image_url"], custom_prompt)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        data = request.get_json()
        if not data or "audio_url" not in data:
            return jsonify({"error": "audio_url is required"}), 400

        custom_prompt = data.get("prompt")
        response = model.process_audio(data["audio_url"], custom_prompt)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "API is running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
