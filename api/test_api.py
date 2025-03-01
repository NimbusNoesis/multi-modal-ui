import requests
import json
import time
import os
import shutil


class Phi4APITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        # Test URLs
        self.remote_image_url = "https://www.ilankelman.org/stopsigns/australia.jpg"
        # Use a different audio URL that's publicly accessible
        self.remote_audio_url = "https://upload.wikimedia.org/wikipedia/commons/b/b0/Barbara_Sahakian_BBC_Radio4_The_Life_Scientific_29_May_2012_b01j5j24.flac"

        # Create test directory
        self.test_dir = "test_files"
        os.makedirs(self.test_dir, exist_ok=True)

        # Set local file paths
        self.local_image_path = os.path.join(self.test_dir, "test_image.jpg")
        self.local_audio_path = os.path.join(self.test_dir, "test_audio.flac")

        # Download test files
        self.create_test_files()

    def create_test_files(self):
        print("Downloading test files...")

        # Download test image
        response = requests.get(self.remote_image_url)
        if response.status_code == 200:
            with open(self.local_image_path, "wb") as f:
                f.write(response.content)
            print(f"Created test image: {self.local_image_path}")

        # Download test audio
        response = requests.get(self.remote_audio_url)
        if response.status_code == 200:
            with open(self.local_audio_path, "wb") as f:
                f.write(response.content)
            print(f"Created test audio: {self.local_audio_path}")

    def test_health(self):
        print("\n=== Testing Health Check ===")
        response = requests.get(f"{self.base_url}/health")
        self._print_response(response)

    def test_image_processing(self):
        print("\n=== Testing Image Processing Endpoint ===")

        # Test 1: Remote URL
        print("\nTest 1: Remote image URL")
        response = requests.post(
            f"{self.base_url}/process_image", json={"image_url": self.remote_image_url}
        )
        self._print_response(response)

        # Test 2: Local file
        print("\nTest 2: Local image file")
        response = requests.post(
            f"{self.base_url}/process_image", json={"image_url": self.local_image_path}
        )
        self._print_response(response)

    def test_audio_processing(self):
        print("\n=== Testing Audio Processing Endpoint ===")

        # Test 1: Remote URL
        print("\nTest 1: Remote audio URL")
        response = requests.post(
            f"{self.base_url}/process_audio", json={"audio_url": self.remote_audio_url}
        )
        self._print_response(response)

        # Test 2: Local file
        print("\nTest 2: Local audio file")
        response = requests.post(
            f"{self.base_url}/process_audio", json={"audio_url": self.local_audio_path}
        )
        self._print_response(response)

    def _print_response(self, response):
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            print(f"Raw Response: {response.text}")
        print("-" * 50)

    def cleanup(self):
        print("\nCleaning up test files...")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"Removed test directory: {self.test_dir}")

    def run_all_tests(self):
        print("Starting API Tests...")
        try:
            self.test_health()
            time.sleep(1)
            self.test_image_processing()
            time.sleep(1)
            self.test_audio_processing()
            print("\nAll tests completed!")
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to the API at {self.base_url}")
            print("Make sure the API server is running and the URL is correct.")
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = Phi4APITester()
    tester.run_all_tests()
