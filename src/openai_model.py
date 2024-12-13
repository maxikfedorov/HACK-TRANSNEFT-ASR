import threading
import itertools
import time
import warnings
import whisper
import os
import json

# Отключение предупреждений
warnings.filterwarnings("ignore")

# Глобальные переменные
AUDIO_PATH = "../data"
AUDIO_FILE = os.path.join(AUDIO_PATH, '2.mp3')
LANGUAGE = "ru"
MODEL_NAME = "large"  # tiny, base, small, medium, large
RESULTS_DIR = "../results"

def loading_animation(stop_animation, message="Обработка"):
    for frame in itertools.cycle(["\\", "|", "/"]):
        if stop_animation.is_set():
            break
        print(f"\r{message}... {frame}", end="")
        time.sleep(0.1)
    print("\r" + " " * 50 + "\r", end="")
    print("\r", end="")

def transcribe_with_animation(audio_file, language="ru"):
    model_info = {
        'filename': audio_file,
        'model_name': f'Whisper {MODEL_NAME}',
        'company': 'OpenAI',
        'architecture': 'Transformer кодировщик-декодер'
    }
    
    print("Используемая модель:")
    for key, value in model_info.items():
        if isinstance(value, list):
            value = ", ".join(value)
        print(f"{key.capitalize()}: {value}")

    stop_animation = threading.Event()
    animation_thread = threading.Thread(
        target=loading_animation, args=(stop_animation, "Транскрибирование"))
    animation_thread.daemon = True
    animation_thread.start()

    try:
        model = whisper.load_model(MODEL_NAME)
        result = model.transcribe(audio_file, language=language, 
                                  task="transcribe", 
                                  fp16=False)         

        result['model_info'] = model_info
        
    finally:
        stop_animation.set()
        print("\r" + " " * 50 + "\r", end="")
        print("Готово!")

    return result

def save_transcription_to_json(result, output_dir, audio_file, filename="transcription.json"):
    result['audio_file_name'] = os.path.basename(audio_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)
    print(f"Результат транскрипции сохранен в файл: {output_path}")

def main():
    transcription_result = transcribe_with_animation(AUDIO_FILE, LANGUAGE)
    
    save_transcription_to_json(transcription_result, RESULTS_DIR, AUDIO_FILE)
    
    print(f"\nРезультат транскрипции:\n{transcription_result['text']}\n")

if __name__ == "__main__":
    main()
