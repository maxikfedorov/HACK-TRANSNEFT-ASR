import os

def get_file_size(file_path):
    """Получение размера файла в МБ"""
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except OSError:
        return 0

def analyze_json_structure(data):
    """Анализ структуры JSON"""
    stats = {
        'total_elements': len(str(data)),
        'nesting_level': 0,
        'keys_count': 0
    }
    
    def count_nesting(obj, level=0):
        if isinstance(obj, dict):
            stats['keys_count'] += len(obj)
            return max([count_nesting(v, level + 1) for v in obj.values()] + [level])
        elif isinstance(obj, list):
            return max([count_nesting(item, level + 1) for item in obj] + [level])
        return level
    
    stats['nesting_level'] = count_nesting(data)
    return stats

def estimate_network_load(file_size_mb):
    """Оценка нагрузки на сеть"""
    transfer_time = file_size_mb
    
    if file_size_mb > 10:
        return "Высокая нагрузка", transfer_time
    elif file_size_mb > 5:
        return "Средняя нагрузка", transfer_time
    else:
        return "Низкая нагрузка", transfer_time

def evaluate_transmission(file_size_mb, stats):
    """Оценка целесообразности передачи"""
    recommendations = []
    
    if file_size_mb > 10:
        recommendations.append("Рекомендуется разбить данные на части")
    if stats['nesting_level'] > 5:
        recommendations.append("Высокий уровень вложенности может затруднить обработку")
    if stats['keys_count'] > 100:
        recommendations.append("Большое количество ключей, рекомендуется оптимизация структуры")
    
    return recommendations if recommendations else ["Передача данных оптимальна"]
