import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def validate_and_fix_json(json_str):
    try:
        # Попытка найти JSON в тексте
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = json_str[start:end]
        
        # Парсинг JSON
        data = json.loads(json_str)
        
        # Проверка структуры
        if not isinstance(data, dict) or 'tasks' not in data:
            # Если структура неверная, исправляем
            if isinstance(data, list):
                data = {'tasks': data}
            else:
                raise ValueError("Неверная структура JSON")
        
        # Проверка каждой задачи
        for task in data['tasks']:
            required_keys = ['task', 'start_time', 'end_time', 'duration']
            if not all(key in task for key in required_keys):
                raise ValueError(f"Отсутствуют обязательные поля: {required_keys}")
            
            # Проверка формата времени
            for time_key in ['start_time', 'end_time']:
                if not isinstance(task[time_key], str) or not len(task[time_key]) == 5:
                    task[time_key] = "00:00"  # Значение по умолчанию
        
        return data
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return None
    except ValueError as e:
        print(f"Ошибка валидации: {e}")
        return None

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
                    "Please provide a JSON object with a single key 'tasks', where the value is an array of objects. "
                    "Each object in the array should have the following keys: "
                    "'task' (the activity description in Russian), 'start_time' (in HH:MM format), "
                    "'end_time' (in HH:MM format), and 'duration' (in hours and minutes format, e.g., '2 hours 30 minutes'). "
                    "Do not include any explanations, comments, or additional text. Return only the JSON object."
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

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        if response_data and response_data.get("choices"):
            content = response_data["choices"][0]["message"]["content"]
            # Валидация и исправление JSON
            validated_data = validate_and_fix_json(content)
            if validated_data:
                return json.dumps(validated_data, ensure_ascii=False, indent=2)
    
    return None

if __name__ == "__main__":
    transcription_file_path = "../results/transcription.json"
    result = process_transcription(transcription_file_path)
    
    if result:
        print("Отформатированный JSON:")
        print(result)
