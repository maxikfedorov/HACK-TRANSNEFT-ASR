import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PERPLEXITY_API_KEY")

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def process_transcription(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        transcription_data = json.load(f)
    
    transcription_text = transcription_data["text"]
    
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {
                "role": "user",
                "content": (
                    f"Extract the following information from this text: '{transcription_text}'. "
                    "Please provide a JSON object with the following keys: "
                    "'task' (the activity description), 'start_time' (in HH:MM format), "
                    "'end_time' (in HH:MM format), and 'duration' (in hours and minutes format, e.g., '2 hours 30 minutes'). "
                    "Ensure the JSON is correctly formatted."
                )
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    
    # Set headers for the API request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Send the request to Perplexity API
    response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse and return only the needed part of the response JSON
        response_data = response.json()
        if response_data and response_data.get("choices"):
            content = response_data["choices"][0]["message"]["content"]
            try:
                # Attempt to extract JSON object from the assistant's content
                start_index = content.find("{")
                end_index = content.rfind("}") + 1
                extracted_json_str = content[start_index:end_index]
                extracted_json = json.loads(extracted_json_str)
                return extracted_json
            except (ValueError, json.JSONDecodeError):
                print("Error parsing assistant's response content.")
                return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


if __name__ == "__main__":
    transcription_file_path = "../results/transcription.json"
    
    result = process_transcription(transcription_file_path)
    
    if result:
        print("Formatted Data:")
        print(json.dumps(result, indent=4, ensure_ascii=False))
