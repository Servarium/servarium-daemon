from flask import Blueprint, jsonify, request
import json
import datetime
import uuid

tickets_bp = Blueprint('tickets', __name__)

# Временное хранилище тикетов (в реальном приложении использовать базу данных)
tickets_storage = []

@tickets_bp.route('/create', methods=['POST'])
def create_ticket():
    """Создает новый тикет"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Валидация обязательных полей
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Создаем тикет
        ticket = {
            'id': str(uuid.uuid4()),
            'title': data['title'],
            'description': data['description'],
            'priority': data.get('priority', 'medium'),  # low, medium, high, critical
            'category': data.get('category', 'general'),  # system, network, docker, general
            'status': 'open',  # open, in_progress, resolved, closed
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat(),
            'agent_info': {
                'hostname': data.get('hostname'),
                'ip_address': data.get('ip_address'),
                'os_info': data.get('os_info')
            },
            'attachments': data.get('attachments', []),
            'tags': data.get('tags', [])
        }
        
        tickets_storage.append(ticket)
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'message': 'Ticket created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@tickets_bp.route('/list', methods=['GET'])
def list_tickets():
    """Возвращает список всех тикетов"""
    try:
        # Параметры фильтрации
        status = request.args.get('status')
        priority = request.args.get('priority')
        category = request.args.get('category')
        limit = request.args.get('limit', type=int)
        
        filtered_tickets = tickets_storage.copy()
        
        # Применяем фильтры
        if status:
            filtered_tickets = [t for t in filtered_tickets if t['status'] == status]
        if priority:
            filtered_tickets = [t for t in filtered_tickets if t['priority'] == priority]
        if category:
            filtered_tickets = [t for t in filtered_tickets if t['category'] == category]
        
        # Сортируем по дате создания (новые первыми)
        filtered_tickets.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Ограничиваем количество
        if limit:
            filtered_tickets = filtered_tickets[:limit]
        
        return jsonify({
            'success': True,
            'tickets': filtered_tickets,
            'total_count': len(tickets_storage),
            'filtered_count': len(filtered_tickets)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@tickets_bp.route('/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Возвращает конкретный тикет по ID"""
    try:
        ticket = next((t for t in tickets_storage if t['id'] == ticket_id), None)
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket not found'
            }), 404
        
        return jsonify({
            'success': True,
            'ticket': ticket
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@tickets_bp.route('/<ticket_id>/update', methods=['PUT'])
def update_ticket(ticket_id):
    """Обновляет тикет"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        ticket = next((t for t in tickets_storage if t['id'] == ticket_id), None)
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket not found'
            }), 404
        
        # Обновляем поля
        updatable_fields = ['title', 'description', 'priority', 'category', 'status', 'tags']
        for field in updatable_fields:
            if field in data:
                ticket[field] = data[field]
        
        ticket['updated_at'] = datetime.datetime.utcnow().isoformat()
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'message': 'Ticket updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@tickets_bp.route('/<ticket_id>/close', methods=['POST'])
def close_ticket(ticket_id):
    """Закрывает тикет"""
    try:
        ticket = next((t for t in tickets_storage if t['id'] == ticket_id), None)
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket not found'
            }), 404
        
        ticket['status'] = 'closed'
        ticket['updated_at'] = datetime.datetime.utcnow().isoformat()
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'message': 'Ticket closed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@tickets_bp.route('/stats', methods=['GET'])
def get_ticket_stats():
    """Возвращает статистику по тикетам"""
    try:
        stats = {
            'total': len(tickets_storage),
            'by_status': {},
            'by_priority': {},
            'by_category': {}
        }
        
        for ticket in tickets_storage:
            # Статистика по статусам
            status = ticket['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Статистика по приоритетам
            priority = ticket['priority']
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Статистика по категориям
            category = ticket['category']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

