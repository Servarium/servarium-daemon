from flask import Blueprint, jsonify, request
import subprocess
import json
import datetime
import uuid
import os
from src.utils.docker_utils import docker_action
from src.utils.process_utils import terminate_process

commands_bp = Blueprint("commands", __name__)

# Белый список разрешенных команд
ALLOWED_COMMANDS = {
    "system_info": ["uname", "-a"],
    "disk_usage": ["df", "-h"],
    "memory_info": ["free", "-h"],
    "process_list": ["ps", "aux"],
    "network_info": ["ip", "addr", "show"],
    "docker_ps": ["docker", "ps", "-a"],
    "docker_images": ["docker", "images"],
    "docker_stats": ["docker", "stats", "--no-stream"],
    "uptime": ["uptime"],
    "whoami": ["whoami"],
    "date": ["date"],
    "hostname": ["hostname"],
    "docker_logs": ["docker", "logs"],
}

# История выполненных команд
command_history = []

def log_command(command_name, command_args, result, success, execution_time):
    """Логирует выполненную команду"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "command_name": command_name,
        "command_args": command_args,
        "result": result,
        "success": success,
        "execution_time": execution_time,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    command_history.append(log_entry)
    
    # Ограничиваем историю последними 100 командами
    if len(command_history) > 100:
        command_history.pop(0)
    
    return log_entry

@commands_bp.route("/allowed", methods=["GET"])
def get_allowed_commands():
    """Возвращает список разрешенных команд"""
    try:
        commands_info = {}
        for cmd_name, cmd_args in ALLOWED_COMMANDS.items():
            commands_info[cmd_name] = {
                "command": " ".join(cmd_args),
                "description": get_command_description(cmd_name),
                "requires_params": cmd_name in ["docker_logs"]
            }
        # Добавляем Docker и Process actions как отдельные команды
        commands_info["docker_start"] = {"command": "docker start <container_name>", "description": "Запуск Docker контейнера", "requires_params": True}
        commands_info["docker_stop"] = {"command": "docker stop <container_name>", "description": "Остановка Docker контейнера", "requires_params": True}
        commands_info["docker_restart"] = {"command": "docker restart <container_name>", "description": "Перезапуск Docker контейнера", "requires_params": True}
        commands_info["terminate_process"] = {"command": "kill <pid>", "description": "Завершение процесса по PID", "requires_params": True}

        return jsonify({
            "success": True,
            "allowed_commands": commands_info,
            "total_count": len(commands_info)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_command_description(cmd_name):
    """Возвращает описание команды"""
    descriptions = {
        "system_info": "Информация о системе",
        "disk_usage": "Использование дискового пространства",
        "memory_info": "Информация о памяти",
        "process_list": "Список процессов",
        "network_info": "Информация о сетевых интерфейсах",
        "docker_ps": "Список Docker контейнеров",
        "docker_images": "Список Docker образов",
        "docker_stats": "Статистика Docker контейнеров",
        "uptime": "Время работы системы",
        "whoami": "Текущий пользователь",
        "date": "Текущая дата и время",
        "hostname": "Имя хоста",
        "docker_logs": "Логи Docker контейнера",
    }
    return descriptions.get(cmd_name, "Описание недоступно")

@commands_bp.route("/execute", methods=["POST"])
def execute_command():
    """Выполняет разрешенную команду"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        command_name = data.get("command_name")
        if not command_name:
            return jsonify({
                "success": False,
                "error": "command_name is required"
            }), 400
        
        start_time = datetime.datetime.utcnow()
        command_result = {}
        success = False
        base_command = []

        if command_name in ["docker_start", "docker_stop", "docker_restart"]:
            container_name = data.get("container_name")
            if not container_name:
                return jsonify({"success": False, "error": f"container_name is required for {command_name}"}), 400
            action_result = docker_action(container_name, command_name.replace("docker_", ""))
            command_result = {"stdout": action_result.get("message", ""), "stderr": action_result.get("error", ""), "return_code": 0 if action_result["status"] == "success" else 1}
            success = action_result["status"] == "success"
            base_command = ["docker", command_name.replace("docker_", ""), container_name]
        elif command_name == "terminate_process":
            pid = data.get("pid")
            if not pid:
                return jsonify({"success": False, "error": "pid is required for terminate_process"}), 400
            action_result = terminate_process(pid)
            command_result = {"stdout": action_result.get("message", ""), "stderr": action_result.get("error", ""), "return_code": 0 if action_result["status"] == "success" else 1}
            success = action_result["status"] == "success"
            base_command = ["kill", str(pid)]
        elif command_name in ALLOWED_COMMANDS:
            base_command = ALLOWED_COMMANDS[command_name].copy()
            if command_name == "docker_logs":
                container_id = data.get("container_id")
                if not container_id:
                    return jsonify({"success": False, "error": "container_id is required for docker_logs"}), 400
                base_command.append(container_id)
                lines = data.get("lines", 100)
                base_command.extend(["--tail", str(lines)])

            try:
                result = subprocess.run(
                    base_command,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                command_result = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "success": result.returncode == 0
                }
                success = result.returncode == 0
            except subprocess.TimeoutExpired:
                command_result = {
                    "stdout": "",
                    "stderr": "Command timed out after 30 seconds",
                    "return_code": -1,
                    "success": False
                }
                success = False
            except Exception as e:
                command_result = {
                    "stdout": "",
                    "stderr": str(e),
                    "return_code": -1,
                    "success": False
                }
                success = False
        else:
            return jsonify({"success": False, "error": f"Command \"{command_name}\" is not allowed"}), 403

        end_time = datetime.datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        log_entry = log_command(
            command_name,
            base_command,
            command_result,
            success,
            execution_time
        )
        
        return jsonify({
            "success": True,
            "command_name": command_name,
            "command": " ".join(map(str, base_command)),
            "result": command_result,
            "execution_time": execution_time,
            "log_id": log_entry["id"]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@commands_bp.route("/history", methods=["GET"])
def get_command_history():
    """Возвращает историю выполненных команд"""
    try:
        limit = request.args.get("limit", 50, type=int)
        command_filter = request.args.get("command")
        success_filter = request.args.get("success")
        
        filtered_history = command_history.copy()
        
        # Применяем фильтры
        if command_filter:
            filtered_history = [h for h in filtered_history if h["command_name"] == command_filter]
        
        if success_filter is not None:
            success_bool = success_filter.lower() == "true"
            filtered_history = [h for h in filtered_history if h["success"] == success_bool]
        
        # Сортируем по времени (новые первыми)
        filtered_history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Ограничиваем количество
        if limit:
            filtered_history = filtered_history[:limit]
        
        return jsonify({
            "success": True,
            "history": filtered_history,
            "total_count": len(command_history),
            "filtered_count": len(filtered_history)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@commands_bp.route("/history/<log_id>", methods=["GET"])
def get_command_log(log_id):
    """Возвращает конкретную запись из истории команд"""
    try:
        log_entry = next((h for h in command_history if h["id"] == log_id), None)
        
        if not log_entry:
            return jsonify({
                "success": False,
                "error": "Log entry not found"
            }), 404
        
        return jsonify({
            "success": True,
            "log_entry": log_entry
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


