
from flask import Flask, request, jsonify
import time
import google.generativeai as genai
from UpdateData import fetch_data_from_mongo  # Import the function to fetch data from MongoDB
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)

api_key = os.getenv('GEMINI_API_KEY')

# Check if API key is present
if not api_key:
    raise EnvironmentError("API Key not found. Set GEMINI_API_KEY in environment variables.")

# Configure the Google Generative AI SDK with the API key
genai.configure(api_key=api_key)


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file


def wait_for_files_active(files):
    """Waits for the given files to be active."""
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")


# Create the model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Instantiate the Generative Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

# Fetch updated data from MongoDB and save it as a CSV
fetch_data_from_mongo()  # Run the function to fetch the latest data

# Upload a file (ensure that the file path is correct)
files = [
    upload_to_gemini("synthetic_colleges_updated.csv", mime_type="text/csv"),
]

# Wait for files to become active after processing
wait_for_files_active(files)

chat_session = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                files[0],
                "which college is in Anand and its fee is under 140000 and provides scholarship",
            ],
        },
        {
            "role": "model",
            "parts": [
                "The college you are looking for is **Charotar University of Science and Tech** in Anand. ...",
            ],
        },
    ]
)


@app.route('/message', methods=['POST'])
def handle_message():
    data = request.json
    user_input = data.get('message')

    if user_input:
        response = chat_session.send_message(user_input)
        response_text = response.text

        # Clean the response text and preserve newlines for formatting
        cleaned_response = (
            response_text
            .replace("*", "")  # Remove asterisks
            .replace("\n\n", "\n")  # Fix double newlines
            .replace("\n", "\n")  # Preserve newlines as intended
            .strip()  # Remove leading and trailing whitespace
        )

        # Adding additional newline formatting if needed
        formatted_response = cleaned_response.replace(". ", ".\n")

        return jsonify({'response': formatted_response})

    return jsonify({'error': 'No message provided'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10001, debug=True)
