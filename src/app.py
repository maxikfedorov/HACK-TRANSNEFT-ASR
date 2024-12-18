from datetime import datetime
import time
import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from typing import Dict, Union, List

from openai_model import transcribe_with_animation, save_transcription_to_json
from perplexity_model import process_transcription
from json_analyzer import (
    get_file_size,
    analyze_json_structure,
    estimate_network_load,
    evaluate_transmission
)

# Конфигурация приложения
APP_CONFIG = {
    'PORT': 5000,
    'UPLOAD_FOLDER': os.path.join('..', 'data'),
    'RESULTS_DIR': os.path.join('..', 'results'),
}

# Инициализация Flask приложения
app = Flask(__name__)
CORS(app)

# Создание необходимых директорий
os.makedirs(APP_CONFIG['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(APP_CONFIG['RESULTS_DIR'], exist_ok=True)

# Путь к файлу с результатами транскрипции
JSON_PATH = os.path.join(APP_CONFIG['RESULTS_DIR'], 'transcription.json')

@app.route('/results', methods=['GET'])
def get_results() -> tuple[Dict, int]:
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({'error': 'Файл не найден'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Ошибка чтения JSON'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['GET'])
def analyze_only() -> tuple[Dict, int]:
    try:
        file_size = get_file_size(JSON_PATH)
        with open(JSON_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        stats = analyze_json_structure(data)
        load_level, transfer_time = estimate_network_load(file_size)
        recommendations = evaluate_transmission(file_size, stats)
        
        analysis_result = {
            'file_size_mb': file_size,
            'structure_stats': stats,
            'network_load': load_level,
            'estimated_transfer_time': f'{transfer_time:.2f} сек',
            'recommendations': recommendations
        }
        
        return jsonify(analysis_result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-audio', methods=['POST'])
def upload_audio() -> tuple[Dict, int]:
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден в запросе'}), 400
    
    audio_file = request.files['file']
    if not audio_file.filename:
        return jsonify({'error': 'Имя файла пустое'}), 400
    
    try:
        file_path = os.path.join(APP_CONFIG['UPLOAD_FOLDER'], audio_file.filename)
        audio_file.save(file_path)
        return jsonify({'message': f'Файл успешно загружен: {audio_file.filename}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_latest_audio_file() -> Union[str, None]:
    files = [
        f for f in os.listdir(APP_CONFIG['UPLOAD_FOLDER'])
        if os.path.isfile(os.path.join(APP_CONFIG['UPLOAD_FOLDER'], f))
    ]
    if not files:
        return None
    
    return max(
        files,
        key=lambda x: os.path.getmtime(os.path.join(APP_CONFIG['UPLOAD_FOLDER'], x))
    )

@app.route('/transcribe-audio', methods=['POST'])
def transcribe_audio() -> tuple[Dict, int]:
    if not request.is_json:
        return jsonify({'error': 'Content-Type должен быть application/json'}), 415

    filename = request.json.get('filename')
    if filename:
        audio_path = os.path.join(APP_CONFIG['UPLOAD_FOLDER'], filename)
        if not os.path.exists(audio_path):
            return jsonify({'error': f'Файл {filename} не найден'}), 404
    else:
        latest_file = get_latest_audio_file()
        if not latest_file:
            return jsonify({'error': 'Нет доступных файлов для обработки'}), 404
        audio_path = os.path.join(APP_CONFIG['UPLOAD_FOLDER'], latest_file)

    try:
        transcription_result = transcribe_with_animation(audio_path)
        save_transcription_to_json(transcription_result, APP_CONFIG['RESULTS_DIR'], audio_path)

        with open(JSON_PATH, 'r', encoding='utf-8') as file:
            transcription_data = json.load(file)

        perplexity_result = process_transcription(JSON_PATH)
        
        # Преобразуем строку JSON в объект Python
        if perplexity_result:
            try:
                formalized_data = json.loads(perplexity_result)
                # Добавляем метаданные к formalized_data
                formalized_data.update({
                    "id": str(uuid.uuid4())[:8],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            except json.JSONDecodeError:
                formalized_data = {'error': 'Ошибка парсинга JSON'}
        else:
            formalized_data = {'error': 'Не удалось получить формализованный ответ'}

        # Записываем формализованный ответ в time_points.json
        time_points_path = os.path.join(APP_CONFIG['RESULTS_DIR'], 'time_points.json')
        
        if os.path.exists(time_points_path):
            with open(time_points_path, 'r', encoding='utf-8') as file:
                time_points_data = json.load(file)
        else:
            time_points_data = []

        # Добавляем новый элемент в список
        time_points_data.append(formalized_data)

        # Сохраняем обновленные данные
        with open(time_points_path, 'w', encoding='utf-8') as file:
            json.dump(time_points_data, file, ensure_ascii=False, indent=4)

        response_data = {
            'transcription': transcription_data,
            'formalized_data': formalized_data
        }

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(
        host='localhost',
        port=APP_CONFIG['PORT'],
        debug=True
    )
