
import time
from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)

# Store the API key in a local variable
api_key = os.getenv('GEMINI_API_KEY')

# Check if API key is present
if not api_key:
    raise EnvironmentError("API Key not found. Set GEMINI_API_KEY in environment variables.")

# Configure the Google Generative AI SDK with the API key
genai.configure(api_key=api_key)



def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini and returns the file object."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file


def wait_for_files_active(files):
    """Waits for the uploaded files to be processed and become active."""
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")


def calculate_rank(twelfth_percentage, gujcet_percentage):
    """Calculates the predicted rank based on the formula provided."""
    board_component = 0.5 * twelfth_percentage
    gujcet_component = 0.5 * gujcet_percentage
    total_percentile = board_component + gujcet_component
    rank = ((100 - total_percentile) / 100) * 50000
    return round(rank)


def clean_colleges_text(colleges_text):
    """Cleans up the colleges text by formatting it for better readability."""
    # Replace asterisks and leading/trailing spaces
    cleaned_text = colleges_text.replace("*", "").replace("**", "").strip()

    # Add new lines after each college suggestion
    formatted_text = cleaned_text.replace(", ", ",\n")  # Add newline after each comma
    formatted_text = formatted_text.replace("),", "),\n")  # Add newline after closing parenthesis

    # Split into lines and reformat to ensure better clarity
    lines = formatted_text.splitlines()
    formatted_lines = []

    for line in lines:
        line = line.strip()  # Remove leading/trailing spaces
        if line:  # Add non-empty lines
            formatted_lines.append(line)

    return "\n".join(formatted_lines)


def suggest_colleges(rank, pdf_file):
    """Uses the uploaded PDF and rank to suggest possible colleges."""
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    pdf_file,
                    f"Use the following information to suggest colleges based on a predicted rank of {rank}.\nThe document contains information about cutoff ranks and available courses in various colleges."
                ],
            },
        ]
    )
    response = chat_session.send_message("Which colleges can I get into with this rank?")
    cleaned_response = clean_colleges_text(response.text)  # Clean and format the response
    return cleaned_response


@app.route('/api/suggest_colleges', methods=['POST'])
def suggest_colleges_route():
    data = request.json
    twelfth_percentage = data.get('twelfth_percentage')
    gujcet_percentage = data.get('gujcet_percentage')

    if twelfth_percentage is None or gujcet_percentage is None:
        return jsonify({"error": "Please provide both 12th Board percentage and GUJCET percentile."}), 400

    predicted_rank = calculate_rank(twelfth_percentage, gujcet_percentage)

    # Upload the PDF file (make sure the PDF is present in the same directory)
    pdf_file = upload_to_gemini("2024_compressed.csv", mime_type="text/csv")

    # Wait for the PDF to be processed
    wait_for_files_active([pdf_file])

    # Suggest colleges based on the calculated rank
    college_suggestions = suggest_colleges(predicted_rank, pdf_file)

    return jsonify({
        "predicted_rank": predicted_rank,
        "colleges": college_suggestions
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5022, debug=True)
