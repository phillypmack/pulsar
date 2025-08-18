from src.celery_app import celery
from src.models.enhanced_work_graph import db, Task, AutomationRule, ActivityFeed, Section
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def process_automation_rules(self, event_type, target_gid, target_type, actor_gid, workspace_gid, project_gid=None, data=None):
    """
    Processa regras de automação baseadas em eventos do sistema.
    
    Args:
        event_type: Tipo do evento (task_completed, task_created, field_changed, etc.)
        target_gid: ID do objeto afetado
        target_type: Tipo do objeto (task, project, etc.)
        actor_gid: ID do usuário que causou o evento
        workspace_gid: ID do workspace
        project_gid: ID do projeto (opcional)
        data: Dados adicionais do evento
    """
    try:
        # Buscar regras ativas para o projeto
        if project_gid:
            rules = AutomationRule.query.filter_by(
                project_gid=project_gid,
                trigger_type=event_type,
                active=True
            ).all()
        else:
            # Se não há projeto específico, buscar regras globais do workspace
            rules = []
        
        for rule in rules:
            try:
                # Verificar condições da regra
                if _check_rule_conditions(rule, target_gid, target_type, data):
                    # Executar ação da regra
                    _execute_rule_action(rule, target_gid, target_type, actor_gid, data)
                    
                    logger.info(f"Regra {rule.gid} executada com sucesso para {target_type} {target_gid}")
            except Exception as e:
                logger.error(f"Erro ao executar regra {rule.gid}: {str(e)}")
                continue
        
        # Registrar atividade no feed
        _create_activity_record(event_type, target_gid, target_type, actor_gid, workspace_gid, project_gid, data)
        
        return {'status': 'success', 'rules_processed': len(rules)}
        
    except Exception as e:
        logger.error(f"Erro no processamento de regras de automação: {str(e)}")
        self.retry(countdown=60, max_retries=3)

def _check_rule_conditions(rule, target_gid, target_type, data):
    """Verifica se as condições da regra são atendidas."""
    try:
        conditions = json.loads(rule.trigger_conditions) if rule.trigger_conditions else {}
        
        if not conditions:
            return True  # Sem condições específicas, sempre executa
        
        # Buscar o objeto alvo
        if target_type == 'task':
            target_obj = Task.query.get(target_gid)
            if not target_obj:
                return False
            
            # Verificar condições específicas para tarefas
            if 'assignee_gid' in conditions:
                if target_obj.assignee_gid != conditions['assignee_gid']:
                    return False
            
            if 'section_gid' in conditions:
                if target_obj.section_gid != conditions['section_gid']:
                    return False
            
            if 'custom_field' in conditions:
                field_condition = conditions['custom_field']
                # Verificar valor de campo personalizado
                # Implementação seria expandida conforme necessário
                pass
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar condições da regra {rule.gid}: {str(e)}")
        return False

def _execute_rule_action(rule, target_gid, target_type, actor_gid, data):
    """Executa a ação definida na regra."""
    try:
        action_params = json.loads(rule.action_parameters) if rule.action_parameters else {}
        
        if rule.action_type == 'move_to_section':
            _move_task_to_section(target_gid, action_params.get('section_gid'))
        
        elif rule.action_type == 'assign_task':
            _assign_task(target_gid, action_params.get('assignee_gid'))
        
        elif rule.action_type == 'mark_complete':
            _mark_task_complete(target_gid)
        
        elif rule.action_type == 'add_to_project':
            _add_task_to_project(target_gid, action_params.get('project_gid'))
        
        elif rule.action_type == 'set_due_date':
            _set_task_due_date(target_gid, action_params.get('due_date'))
        
        # Adicionar mais tipos de ação conforme necessário
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Erro ao executar ação da regra {rule.gid}: {str(e)}")
        db.session.rollback()
        raise

def _move_task_to_section(task_gid, section_gid):
    """Move uma tarefa para uma seção específica."""
    task = Task.query.get(task_gid)
    if task and section_gid:
        section = Section.query.get(section_gid)
        if section:
            task.section_gid = section_gid
            task.modified_at = datetime.utcnow()

def _assign_task(task_gid, assignee_gid):
    """Atribui uma tarefa a um usuário."""
    task = Task.query.get(task_gid)
    if task:
        task.assignee_gid = assignee_gid
        task.modified_at = datetime.utcnow()

def _mark_task_complete(task_gid):
    """Marca uma tarefa como concluída."""
    task = Task.query.get(task_gid)
    if task:
        task.completed = True
        task.completed_at = datetime.utcnow()
        task.modified_at = datetime.utcnow()

def _add_task_to_project(task_gid, project_gid):
    """Adiciona uma tarefa a um projeto."""
    from src.models.enhanced_work_graph import Project
    task = Task.query.get(task_gid)
    project = Project.query.get(project_gid)
    if task and project and project not in task.projects:
        task.projects.append(project)
        task.modified_at = datetime.utcnow()

def _set_task_due_date(task_gid, due_date_str):
    """Define a data de vencimento de uma tarefa."""
    from datetime import datetime
    task = Task.query.get(task_gid)
    if task and due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            task.due_on = due_date
            task.modified_at = datetime.utcnow()
        except ValueError:
            logger.error(f"Formato de data inválido: {due_date_str}")

def _create_activity_record(event_type, target_gid, target_type, actor_gid, workspace_gid, project_gid, data):
    """Cria um registro de atividade no feed."""
    try:
        activity = ActivityFeed(
            event_type=event_type,
            actor_gid=actor_gid,
            target_gid=target_gid,
            target_type=target_type,
            project_gid=project_gid,
            workspace_gid=workspace_gid,
            data=json.dumps(data) if data else None
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Erro ao criar registro de atividade: {str(e)}")
        db.session.rollback()

@celery.task
def cleanup_old_activities(days_old=30):
    """Remove atividades antigas do feed para manter performance."""
    try:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_activities = ActivityFeed.query.filter(
            ActivityFeed.created_at < cutoff_date
        ).all()
        
        count = len(old_activities)
        for activity in old_activities:
            db.session.delete(activity)
        
        db.session.commit()
        logger.info(f"Removidas {count} atividades antigas")
        
        return {'status': 'success', 'removed_count': count}
        
    except Exception as e:
        logger.error(f"Erro na limpeza de atividades antigas: {str(e)}")
        return {'status': 'error', 'message': str(e)}

