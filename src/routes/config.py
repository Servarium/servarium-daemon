from flask import Blueprint, jsonify
from src.services.metrics_collector import MetricsCollector
import datetime

config_bp = Blueprint("config", __name__)
collector = MetricsCollector()

@config_bp.route("/system_info", methods=["GET"])
def get_system_info():
    """Возвращает информацию о системе"""
    try:
        system_info = collector.collect_system_info()
        return jsonify({
            "success": True,
            "data": system_info,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


