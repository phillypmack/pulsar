from flask import Blueprint, request, jsonify, g
from src.models.enhanced_work_graph import db, ActivityFeed, User, Task, Project
from src.routes.auth import auth_required
from datetime import datetime, timedelta
import json

activity_feed_bp = Blueprint('activity_feed', __name__)

@activity_feed_bp.route('/api/activity-feed', methods=['GET'])
@auth_required
def get_activity_feed():
    """Buscar feed de atividades com filtros."""
    try:
        # Parâmetros de filtro
        workspace_gid = request.args.get('workspace_gid')
        project_gid = request.args.get('project_gid')
        actor_gid = request.args.get('actor_gid')
        event_type = request.args.get('event_type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Filtro de data (últimos N dias)
        days = int(request.args.get('days', 30))
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Query base
        query = ActivityFeed.query.filter(ActivityFeed.created_at >= since_date)
        
        # Aplicar filtros
        if workspace_gid:
            query = query.filter_by(workspace_gid=workspace_gid)
        if project_gid:
            query = query.filter_by(project_gid=project_gid)
        if actor_gid:
            query = query.filter_by(actor_gid=actor_gid)
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        # Ordenar por data (mais recente primeiro)
        query = query.order_by(ActivityFeed.created_at.desc())
        
        # Paginação
        activities = query.offset(offset).limit(limit).all()
        
        # Enriquecer dados com informações relacionadas
        result = []
        for activity in activities:
            activity_data = activity.to_dict()
            
            # Adicionar dados do ator
            if activity.actor:
                activity_data['actor'] = {
                    'gid': activity.actor.gid,
                    'name': activity.actor.name,
                    'email': activity.actor.email
                }
            
            # Adicionar dados do alvo baseado no tipo
            if activity.target_type == 'task' and activity.target_gid:
                task = Task.query.get(activity.target_gid)
                if task:
                    activity_data['target'] = {
                        'gid': task.gid,
                        'name': task.name,
                        'completed': task.completed
                    }
            elif activity.target_type == 'project' and activity.target_gid:
                project = Project.query.get(activity.target_gid)
                if project:
                    activity_data['target'] = {
                        'gid': project.gid,
                        'name': project.name
                    }
            
            # Adicionar dados do projeto se disponível
            if activity.project_gid:
                project = Project.query.get(activity.project_gid)
                if project:
                    activity_data['project'] = {
                        'gid': project.gid,
                        'name': project.name
                    }
            
            result.append(activity_data)
        
        return jsonify({
            'activities': result,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': query.count()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activity_feed_bp.route('/api/activity-feed/summary', methods=['GET'])
@auth_required
def get_activity_summary():
    """Buscar resumo de atividades por tipo."""
    try:
        workspace_gid = request.args.get('workspace_gid')
        project_gid = request.args.get('project_gid')
        days = int(request.args.get('days', 7))
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Query base
        query = ActivityFeed.query.filter(ActivityFeed.created_at >= since_date)
        
        if workspace_gid:
            query = query.filter_by(workspace_gid=workspace_gid)
        if project_gid:
            query = query.filter_by(project_gid=project_gid)
        
        activities = query.all()
        
        # Agrupar por tipo de evento
        summary = {}
        for activity in activities:
            event_type = activity.event_type
            if event_type not in summary:
                summary[event_type] = {
                    'count': 0,
                    'recent_actors': set(),
                    'latest_timestamp': None
                }
            
            summary[event_type]['count'] += 1
            if activity.actor:
                summary[event_type]['recent_actors'].add(activity.actor.name)
            
            if not summary[event_type]['latest_timestamp'] or activity.created_at > summary[event_type]['latest_timestamp']:
                summary[event_type]['latest_timestamp'] = activity.created_at
        
        # Converter sets para listas para serialização JSON
        for event_type in summary:
            summary[event_type]['recent_actors'] = list(summary[event_type]['recent_actors'])
            if summary[event_type]['latest_timestamp']:
                summary[event_type]['latest_timestamp'] = summary[event_type]['latest_timestamp'].isoformat()
        
        return jsonify({
            'summary': summary,
            'period_days': days,
            'total_activities': len(activities)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activity_feed_bp.route('/api/activity-feed/user-activity', methods=['GET'])
@auth_required
def get_user_activity():
    """Buscar atividades de um usuário específico."""
    try:
        user_gid = request.args.get('user_gid', g.current_user.gid)
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        activities = ActivityFeed.query.filter(
            ActivityFeed.actor_gid == user_gid,
            ActivityFeed.created_at >= since_date
        ).order_by(ActivityFeed.created_at.desc()).limit(limit).all()
        
        # Agrupar por data
        activity_by_date = {}
        for activity in activities:
            date_key = activity.created_at.date().isoformat()
            if date_key not in activity_by_date:
                activity_by_date[date_key] = []
            
            activity_data = activity.to_dict()
            
            # Adicionar dados do alvo
            if activity.target_type == 'task' and activity.target_gid:
                task = Task.query.get(activity.target_gid)
                if task:
                    activity_data['target'] = {
                        'gid': task.gid,
                        'name': task.name
                    }
            
            activity_by_date[date_key].append(activity_data)
        
        return jsonify({
            'user_gid': user_gid,
            'activity_by_date': activity_by_date,
            'total_activities': len(activities),
            'period_days': days
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activity_feed_bp.route('/api/activity-feed/project-timeline', methods=['GET'])
@auth_required
def get_project_timeline():
    """Buscar timeline de atividades de um projeto."""
    try:
        project_gid = request.args.get('project_gid')
        if not project_gid:
            return jsonify({'error': 'project_gid is required'}), 400
        
        days = int(request.args.get('days', 90))
        since_date = datetime.utcnow() - timedelta(days=days)
        
        activities = ActivityFeed.query.filter(
            ActivityFeed.project_gid == project_gid,
            ActivityFeed.created_at >= since_date
        ).order_by(ActivityFeed.created_at.desc()).all()
        
        # Enriquecer dados para timeline
        timeline = []
        for activity in activities:
            activity_data = activity.to_dict()
            
            # Adicionar dados do ator
            if activity.actor:
                activity_data['actor'] = {
                    'gid': activity.actor.gid,
                    'name': activity.actor.name
                }
            
            # Adicionar dados do alvo
            if activity.target_type == 'task' and activity.target_gid:
                task = Task.query.get(activity.target_gid)
                if task:
                    activity_data['target'] = {
                        'gid': task.gid,
                        'name': task.name,
                        'completed': task.completed
                    }
            
            # Gerar descrição amigável
            activity_data['description'] = _generate_activity_description(activity)
            
            timeline.append(activity_data)
        
        return jsonify({
            'project_gid': project_gid,
            'timeline': timeline,
            'total_activities': len(timeline),
            'period_days': days
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _generate_activity_description(activity: ActivityFeed) -> str:
    """Gera descrição amigável para uma atividade."""
    actor_name = activity.actor.name if activity.actor else 'Alguém'
    
    if activity.event_type == 'task_created':
        return f"{actor_name} criou uma nova tarefa"
    elif activity.event_type == 'task_completed':
        return f"{actor_name} concluiu uma tarefa"
    elif activity.event_type == 'task_assigned':
        return f"{actor_name} atribuiu uma tarefa"
    elif activity.event_type == 'task_updated':
        return f"{actor_name} atualizou uma tarefa"
    elif activity.event_type == 'project_created':
        return f"{actor_name} criou um novo projeto"
    elif activity.event_type == 'project_updated':
        return f"{actor_name} atualizou o projeto"
    elif activity.event_type == 'dependency_added':
        return f"{actor_name} adicionou uma dependência"
    elif activity.event_type == 'dependency_removed':
        return f"{actor_name} removeu uma dependência"
    elif activity.event_type == 'custom_field_updated':
        return f"{actor_name} atualizou um campo personalizado"
    else:
        return f"{actor_name} realizou uma ação ({activity.event_type})"

@activity_feed_bp.route('/api/activity-feed/stats', methods=['GET'])
@auth_required
def get_activity_stats():
    """Buscar estatísticas de atividade."""
    try:
        workspace_gid = request.args.get('workspace_gid')
        project_gid = request.args.get('project_gid')
        days = int(request.args.get('days', 30))
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Query base
        query = ActivityFeed.query.filter(ActivityFeed.created_at >= since_date)
        
        if workspace_gid:
            query = query.filter_by(workspace_gid=workspace_gid)
        if project_gid:
            query = query.filter_by(project_gid=project_gid)
        
        activities = query.all()
        
        # Calcular estatísticas
        stats = {
            'total_activities': len(activities),
            'unique_actors': len(set(a.actor_gid for a in activities if a.actor_gid)),
            'activities_by_type': {},
            'activities_by_day': {},
            'most_active_users': {},
            'period_days': days
        }
        
        # Atividades por tipo
        for activity in activities:
            event_type = activity.event_type
            if event_type not in stats['activities_by_type']:
                stats['activities_by_type'][event_type] = 0
            stats['activities_by_type'][event_type] += 1
        
        # Atividades por dia
        for activity in activities:
            date_key = activity.created_at.date().isoformat()
            if date_key not in stats['activities_by_day']:
                stats['activities_by_day'][date_key] = 0
            stats['activities_by_day'][date_key] += 1
        
        # Usuários mais ativos
        for activity in activities:
            if activity.actor_gid:
                actor_name = activity.actor.name if activity.actor else f"User {activity.actor_gid}"
                if actor_name not in stats['most_active_users']:
                    stats['most_active_users'][actor_name] = 0
                stats['most_active_users'][actor_name] += 1
        
        # Ordenar usuários mais ativos
        stats['most_active_users'] = dict(
            sorted(stats['most_active_users'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

