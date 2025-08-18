from src.celery_app import celery
from src.models.enhanced_work_graph import db, User, Task, Project
import logging
import json

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def send_task_notification(self, task_gid, notification_type, recipient_gid, data=None):
    """
    Envia notificação sobre uma tarefa.
    
    Args:
        task_gid: ID da tarefa
        notification_type: Tipo da notificação (assigned, completed, due_soon, etc.)
        recipient_gid: ID do usuário que receberá a notificação
        data: Dados adicionais da notificação
    """
    try:
        task = Task.query.get(task_gid)
        recipient = User.query.get(recipient_gid)
        
        if not task or not recipient:
            logger.error(f"Tarefa {task_gid} ou usuário {recipient_gid} não encontrado")
            return {'status': 'error', 'message': 'Task or user not found'}
        
        # Preparar dados da notificação
        notification_data = {
            'task_name': task.name,
            'task_gid': task.gid,
            'recipient_email': recipient.email,
            'recipient_name': recipient.name,
            'notification_type': notification_type,
            'data': data or {}
        }
        
        # Enviar notificação baseada no tipo
        if notification_type == 'task_assigned':
            _send_assignment_notification(notification_data)
        elif notification_type == 'task_completed':
            _send_completion_notification(notification_data)
        elif notification_type == 'task_due_soon':
            _send_due_date_notification(notification_data)
        elif notification_type == 'task_overdue':
            _send_overdue_notification(notification_data)
        elif notification_type == 'dependency_completed':
            _send_dependency_notification(notification_data)
        
        logger.info(f"Notificação {notification_type} enviada para {recipient.email}")
        return {'status': 'success', 'notification_type': notification_type}
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {str(e)}")
        self.retry(countdown=60, max_retries=3)

def _send_assignment_notification(data):
    """Envia notificação de atribuição de tarefa."""
    # Por enquanto, apenas log. Em produção, integraria com serviço de email
    logger.info(f"NOTIFICAÇÃO: {data['recipient_name']} foi atribuído à tarefa '{data['task_name']}'")
    
    # Aqui seria integrado com serviço de email real
    # send_email(
    #     to=data['recipient_email'],
    #     subject=f"Nova tarefa atribuída: {data['task_name']}",
    #     template='task_assigned',
    #     data=data
    # )

def _send_completion_notification(data):
    """Envia notificação de conclusão de tarefa."""
    logger.info(f"NOTIFICAÇÃO: Tarefa '{data['task_name']}' foi concluída")

def _send_due_date_notification(data):
    """Envia notificação de prazo próximo."""
    logger.info(f"NOTIFICAÇÃO: Tarefa '{data['task_name']}' tem prazo próximo")

def _send_overdue_notification(data):
    """Envia notificação de tarefa atrasada."""
    logger.info(f"NOTIFICAÇÃO: Tarefa '{data['task_name']}' está atrasada")

def _send_dependency_notification(data):
    """Envia notificação quando uma dependência é concluída."""
    logger.info(f"NOTIFICAÇÃO: Dependência concluída para tarefa '{data['task_name']}'")

@celery.task
def send_daily_digest(user_gid):
    """Envia resumo diário das tarefas para um usuário."""
    try:
        user = User.query.get(user_gid)
        if not user:
            return {'status': 'error', 'message': 'User not found'}
        
        # Buscar tarefas pendentes do usuário
        pending_tasks = Task.query.filter_by(
            assignee_gid=user_gid,
            completed=False
        ).all()
        
        # Buscar tarefas com prazo próximo (próximos 3 dias)
        from datetime import datetime, timedelta
        upcoming_deadline = datetime.utcnow().date() + timedelta(days=3)
        due_soon_tasks = [task for task in pending_tasks if task.due_on and task.due_on <= upcoming_deadline]
        
        # Buscar tarefas atrasadas
        today = datetime.utcnow().date()
        overdue_tasks = [task for task in pending_tasks if task.due_on and task.due_on < today]
        
        digest_data = {
            'user_name': user.name,
            'user_email': user.email,
            'pending_count': len(pending_tasks),
            'due_soon_count': len(due_soon_tasks),
            'overdue_count': len(overdue_tasks),
            'due_soon_tasks': [{'name': task.name, 'due_on': task.due_on.isoformat()} for task in due_soon_tasks[:5]],
            'overdue_tasks': [{'name': task.name, 'due_on': task.due_on.isoformat()} for task in overdue_tasks[:5]]
        }
        
        logger.info(f"RESUMO DIÁRIO para {user.name}: {len(pending_tasks)} pendentes, {len(due_soon_tasks)} com prazo próximo, {len(overdue_tasks)} atrasadas")
        
        # Em produção, enviaria email com o resumo
        # send_email(
        #     to=user.email,
        #     subject="Seu resumo diário de tarefas",
        #     template='daily_digest',
        #     data=digest_data
        # )
        
        return {'status': 'success', 'digest_data': digest_data}
        
    except Exception as e:
        logger.error(f"Erro ao enviar resumo diário: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def check_due_dates():
    """Verifica tarefas com prazo próximo ou atrasadas e envia notificações."""
    try:
        from datetime import datetime, timedelta
        
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        
        # Buscar tarefas com prazo amanhã
        due_tomorrow = Task.query.filter_by(
            due_on=tomorrow,
            completed=False
        ).all()
        
        # Buscar tarefas atrasadas
        overdue = Task.query.filter(
            Task.due_on < today,
            Task.completed == False
        ).all()
        
        notifications_sent = 0
        
        # Enviar notificações para tarefas com prazo amanhã
        for task in due_tomorrow:
            if task.assignee_gid:
                send_task_notification.delay(
                    task.gid,
                    'task_due_soon',
                    task.assignee_gid,
                    {'due_date': task.due_on.isoformat()}
                )
                notifications_sent += 1
        
        # Enviar notificações para tarefas atrasadas
        for task in overdue:
            if task.assignee_gid:
                send_task_notification.delay(
                    task.gid,
                    'task_overdue',
                    task.assignee_gid,
                    {'due_date': task.due_on.isoformat(), 'days_overdue': (today - task.due_on).days}
                )
                notifications_sent += 1
        
        logger.info(f"Verificação de prazos concluída. {notifications_sent} notificações enviadas.")
        
        return {
            'status': 'success',
            'due_tomorrow': len(due_tomorrow),
            'overdue': len(overdue),
            'notifications_sent': notifications_sent
        }
        
    except Exception as e:
        logger.error(f"Erro na verificação de prazos: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def send_project_summary(project_gid, recipient_gid):
    """Envia resumo de um projeto para um usuário."""
    try:
        project = Project.query.get(project_gid)
        recipient = User.query.get(recipient_gid)
        
        if not project or not recipient:
            return {'status': 'error', 'message': 'Project or user not found'}
        
        # Calcular estatísticas do projeto
        total_tasks = len(project.tasks)
        completed_tasks = len([task for task in project.tasks if task.completed])
        pending_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Buscar tarefas atrasadas no projeto
        from datetime import datetime
        today = datetime.utcnow().date()
        overdue_tasks = [task for task in project.tasks if task.due_on and task.due_on < today and not task.completed]
        
        summary_data = {
            'project_name': project.name,
            'project_gid': project.gid,
            'recipient_name': recipient.name,
            'recipient_email': recipient.email,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': round(completion_rate, 1),
            'overdue_tasks': len(overdue_tasks)
        }
        
        logger.info(f"RESUMO DO PROJETO '{project.name}' para {recipient.name}: {completion_rate}% concluído")
        
        return {'status': 'success', 'summary_data': summary_data}
        
    except Exception as e:
        logger.error(f"Erro ao enviar resumo do projeto: {str(e)}")
        return {'status': 'error', 'message': str(e)}

