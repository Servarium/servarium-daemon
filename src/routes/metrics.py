from flask import Blueprint, jsonify, request
from src.services.metrics_collector import MetricsCollector
import json
import datetime

metrics_bp = Blueprint('metrics', __name__)
collector = MetricsCollector()

@metrics_bp.route('/components', methods=['GET'])
def get_available_components():
    """Возвращает список доступных компонентов для мониторинга"""
    try:
        components = collector.get_available_components()
        return jsonify({
            'success': True,
            'components': components,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/cpu', methods=['GET'])
def get_cpu_metrics():
    """Возвращает метрики CPU"""
    try:
        metrics = collector.collect_cpu_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/memory', methods=['GET'])
def get_memory_metrics():
    """Возвращает метрики памяти"""
    try:
        metrics = collector.collect_memory_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/disk', methods=['GET'])
def get_disk_metrics():
    """Возвращает метрики дисков"""
    try:
        metrics = collector.collect_disk_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/network', methods=['GET'])
def get_network_metrics():
    """Возвращает сетевые метрики"""
    try:
        metrics = collector.collect_network_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/processes', methods=['GET'])
def get_processes_metrics():
    """Возвращает метрики процессов"""
    try:
        metrics = collector.collect_processes_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/uptime', methods=['GET'])
def get_uptime_metrics():
    """Возвращает метрики времени работы"""
    try:
        metrics = collector.collect_uptime_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/docker', methods=['GET'])
def get_docker_metrics():
    """Возвращает метрики Docker контейнеров"""
    try:
        metrics = collector.collect_docker_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/all', methods=['GET'])
def get_all_metrics():
    """Возвращает все доступные метрики"""
    try:
        metrics = collector.collect_all_metrics()
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/key/generate', methods=['POST'])
def generate_unique_key():
    """Генерирует уникальный ключ для агента"""
    try:
        unique_key = collector.generate_unique_key()
        return jsonify({
            'success': True,
            'unique_key': unique_key,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@metrics_bp.route('/status', methods=['GET'])
def get_agent_status():
    """Возвращает статус агента"""
    try:
        return jsonify({
            'success': True,
            'status': 'online',
            'available_components': collector.get_available_components(),
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

