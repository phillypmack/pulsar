from flask import Blueprint, request, jsonify, g
from src.models.enhanced_work_graph import db, Task, Project, User, CustomField, CustomFieldValue, task_dependencies
from src.routes.auth import auth_required
from src.tasks.automation_tasks import process_automation_rules
from src.websocket.events import broadcast_task_change
from datetime import datetime, date
import json

enhanced_tasks_bp = Blueprint('enhanced_tasks', __name__)

@enhanced_tasks_bp.route('/api/tasks', methods=['GET'])
@auth_required
def get_tasks():
    """Buscar tarefas com filtros avançados."""
    try:
        # Parâmetros de filtro
        workspace_gid = request.args.get('workspace_gid')
        project_gid = request.args.get('project_gid')
        assignee_gid = request.args.get('assignee_gid')
        completed = request.args.get('completed')
        has_dependencies = request.args.get('has_dependencies')
        section_gid = request.args.get('section_gid')
        
        # Query base
        query = Task.query
        
        # Aplicar filtros
        if workspace_gid:
            query = query.filter_by(workspace_gid=workspace_gid)
        if project_gid:
            query = query.join(Task.projects).filter(Project.gid == project_gid)
        if assignee_gid:
            query = query.filter_by(assignee_gid=assignee_gid)
        if completed is not None:
            completed_bool = completed.lower() == 'true'
            query = query.filter_by(completed=completed_bool)
        if section_gid:
            query = query.filter_by(section_gid=section_gid)
        if has_dependencies == 'true':
            query = query.join(task_dependencies, Task.gid == task_dependencies.c.dependent_task_gid)
        
        tasks = query.all()
        
        # Incluir dados de campos personalizados se solicitado
        include_custom_fields = request.args.get('include_custom_fields', 'false').lower() == 'true'
        
        result = []
        for task in tasks:
            task_data = task.to_dict()
            
            if include_custom_fields:
                custom_field_values = []
                for cfv in task.custom_field_values:
                    cf_data = cfv.to_dict()
                    cf_data['custom_field'] = cfv.custom_field.to_dict()
                    custom_field_values.append(cf_data)
                task_data['custom_field_values'] = custom_field_values
            
            result.append(task_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_tasks_bp.route('/api/tasks', methods=['POST'])
@auth_required
def create_task():
    """Criar nova tarefa com suporte a dependências e campos personalizados."""
    try:
        data = request.get_json()
        
        # Validações básicas
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if not data.get('workspace_gid'):
            return jsonify({'error': 'Workspace GID is required'}), 400
        
        # Criar tarefa
        task = Task(
            name=data['name'],
            notes=data.get('notes'),
            assignee_gid=data.get('assignee_gid'),
            workspace_gid=data['workspace_gid'],
            section_gid=data.get('section_gid'),
            resource_subtype=data.get('resource_subtype', 'default_task'),
            parent_gid=data.get('parent_gid')
        )
        
        # Processar datas
        if data.get('due_on'):
            task.due_on = datetime.strptime(data['due_on'], '%Y-%m-%d').date()
        if data.get('start_on'):
            task.start_on = datetime.strptime(data['start_on'], '%Y-%m-%d').date()
        
        db.session.add(task)
        db.session.flush()  # Para obter o GID da tarefa
        
        # Adicionar a projetos se especificado
        project_gids = data.get('project_gids', [])
        for project_gid in project_gids:
            project = Project.query.get(project_gid)
            if project:
                task.projects.append(project)
        
        # Processar dependências
        dependency_gids = data.get('dependency_gids', [])
        for dep_gid in dependency_gids:
            dependency_task = Task.query.get(dep_gid)
            if dependency_task:
                task.dependencies.append(dependency_task)
        
        # Processar campos personalizados
        custom_field_values = data.get('custom_field_values', [])
        for cfv_data in custom_field_values:
            custom_field = CustomField.query.get(cfv_data.get('custom_field_gid'))
            if custom_field:
                cfv = CustomFieldValue(
                    custom_field_gid=custom_field.gid,
                    task_gid=task.gid
                )
                
                # Definir valor baseado no tipo do campo
                if custom_field.type == 'text':
                    cfv.text_value = cfv_data.get('text_value')
                elif custom_field.type == 'number':
                    cfv.number_value = cfv_data.get('number_value')
                elif custom_field.type == 'enum':
                    cfv.enum_value = cfv_data.get('enum_value')
                elif custom_field.type == 'multi_enum':
                    cfv.multi_enum_values = json.dumps(cfv_data.get('multi_enum_values', []))
                elif custom_field.type == 'date':
                    if cfv_data.get('date_value'):
                        cfv.date_value = datetime.strptime(cfv_data['date_value'], '%Y-%m-%d').date()
                
                db.session.add(cfv)
        
        db.session.commit()
        
        # Disparar automação assíncrona
        process_automation_rules.delay(
            'task_created',
            task.gid,
            'task',
            g.current_user.gid,
            task.workspace_gid,
            project_gids[0] if project_gids else None,
            {'task_name': task.name}
        )
        
        # Broadcast para WebSocket
        broadcast_task_change(task.gid, 'created', task.to_dict(), g.current_user.gid)
        
        return jsonify(task.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enhanced_tasks_bp.route('/api/tasks/<task_gid>', methods=['PUT'])
@auth_required
def update_task(task_gid):
    """Atualizar tarefa com suporte a dependências e campos personalizados."""
    try:
        task = Task.query.get(task_gid)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        old_data = task.to_dict()
        
        # Atualizar campos básicos
        if 'name' in data:
            task.name = data['name']
        if 'notes' in data:
            task.notes = data['notes']
        if 'assignee_gid' in data:
            old_assignee = task.assignee_gid
            task.assignee_gid = data['assignee_gid']
            
            # Se atribuição mudou, disparar notificação
            if old_assignee != task.assignee_gid and task.assignee_gid:
                from src.tasks.notification_tasks import send_task_notification
                send_task_notification.delay(
                    task.gid,
                    'task_assigned',
                    task.assignee_gid,
                    {'previous_assignee': old_assignee}
                )
        
        if 'completed' in data:
            was_completed = task.completed
            task.completed = data['completed']
            
            if not was_completed and task.completed:
                task.completed_at = datetime.utcnow()
                
                # Disparar automação para conclusão
                process_automation_rules.delay(
                    'task_completed',
                    task.gid,
                    'task',
                    g.current_user.gid,
                    task.workspace_gid,
                    task.projects[0].gid if task.projects else None,
                    {'task_name': task.name}
                )
                
                # Notificar dependentes que a dependência foi concluída
                for dependent in task.dependents:
                    if dependent.assignee_gid:
                        from src.tasks.notification_tasks import send_task_notification
                        send_task_notification.delay(
                            dependent.gid,
                            'dependency_completed',
                            dependent.assignee_gid,
                            {'completed_dependency': task.name}
                        )
            
            elif was_completed and not task.completed:
                task.completed_at = None
        
        if 'section_gid' in data:
            task.section_gid = data['section_gid']
        
        # Processar datas
        if 'due_on' in data:
            if data['due_on']:
                task.due_on = datetime.strptime(data['due_on'], '%Y-%m-%d').date()
            else:
                task.due_on = None
        
        if 'start_on' in data:
            if data['start_on']:
                task.start_on = datetime.strptime(data['start_on'], '%Y-%m-%d').date()
            else:
                task.start_on = None
        
        # Atualizar dependências
        if 'dependency_gids' in data:
            # Remover dependências existentes
            task.dependencies.clear()
            
            # Adicionar novas dependências
            for dep_gid in data['dependency_gids']:
                dependency_task = Task.query.get(dep_gid)
                if dependency_task:
                    # Verificar se não cria ciclo
                    if not _creates_dependency_cycle(task.gid, dep_gid):
                        task.dependencies.append(dependency_task)
        
        # Atualizar campos personalizados
        if 'custom_field_values' in data:
            # Remover valores existentes
            for cfv in task.custom_field_values:
                db.session.delete(cfv)
            
            # Adicionar novos valores
            for cfv_data in data['custom_field_values']:
                custom_field = CustomField.query.get(cfv_data.get('custom_field_gid'))
                if custom_field:
                    cfv = CustomFieldValue(
                        custom_field_gid=custom_field.gid,
                        task_gid=task.gid
                    )
                    
                    # Definir valor baseado no tipo
                    if custom_field.type == 'text':
                        cfv.text_value = cfv_data.get('text_value')
                    elif custom_field.type == 'number':
                        cfv.number_value = cfv_data.get('number_value')
                    elif custom_field.type == 'enum':
                        cfv.enum_value = cfv_data.get('enum_value')
                    elif custom_field.type == 'multi_enum':
                        cfv.multi_enum_values = json.dumps(cfv_data.get('multi_enum_values', []))
                    elif custom_field.type == 'date':
                        if cfv_data.get('date_value'):
                            cfv.date_value = datetime.strptime(cfv_data['date_value'], '%Y-%m-%d').date()
                    
                    db.session.add(cfv)
        
        task.modified_at = datetime.utcnow()
        db.session.commit()
        
        # Determinar tipo de mudança para automação
        change_type = 'task_updated'
        if old_data.get('completed') != task.completed:
            change_type = 'task_completed' if task.completed else 'task_reopened'
        elif old_data.get('assignee_gid') != task.assignee_gid:
            change_type = 'task_assigned'
        
        # Disparar automação
        process_automation_rules.delay(
            change_type,
            task.gid,
            'task',
            g.current_user.gid,
            task.workspace_gid,
            task.projects[0].gid if task.projects else None,
            {'old_data': old_data, 'new_data': task.to_dict()}
        )
        
        # Broadcast para WebSocket
        broadcast_task_change(task.gid, 'updated', task.to_dict(), g.current_user.gid)
        
        return jsonify(task.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enhanced_tasks_bp.route('/api/tasks/<task_gid>/dependencies', methods=['POST'])
@auth_required
def add_task_dependency(task_gid):
    """Adicionar dependência a uma tarefa."""
    try:
        task = Task.query.get(task_gid)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        dependency_gid = data.get('dependency_gid')
        
        if not dependency_gid:
            return jsonify({'error': 'dependency_gid is required'}), 400
        
        dependency_task = Task.query.get(dependency_gid)
        if not dependency_task:
            return jsonify({'error': 'Dependency task not found'}), 404
        
        # Verificar se não cria ciclo
        if _creates_dependency_cycle(task_gid, dependency_gid):
            return jsonify({'error': 'Adding this dependency would create a cycle'}), 400
        
        # Verificar se dependência já existe
        if dependency_task in task.dependencies:
            return jsonify({'error': 'Dependency already exists'}), 400
        
        task.dependencies.append(dependency_task)
        task.modified_at = datetime.utcnow()
        db.session.commit()
        
        # Broadcast para WebSocket
        broadcast_task_change(task.gid, 'dependency_added', {
            'dependency_gid': dependency_gid,
            'dependency_name': dependency_task.name
        }, g.current_user.gid)
        
        return jsonify({
            'message': 'Dependency added successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enhanced_tasks_bp.route('/api/tasks/<task_gid>/dependencies/<dependency_gid>', methods=['DELETE'])
@auth_required
def remove_task_dependency(task_gid, dependency_gid):
    """Remover dependência de uma tarefa."""
    try:
        task = Task.query.get(task_gid)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        dependency_task = Task.query.get(dependency_gid)
        if not dependency_task:
            return jsonify({'error': 'Dependency task not found'}), 404
        
        if dependency_task not in task.dependencies:
            return jsonify({'error': 'Dependency does not exist'}), 400
        
        task.dependencies.remove(dependency_task)
        task.modified_at = datetime.utcnow()
        db.session.commit()
        
        # Broadcast para WebSocket
        broadcast_task_change(task.gid, 'dependency_removed', {
            'dependency_gid': dependency_gid,
            'dependency_name': dependency_task.name
        }, g.current_user.gid)
        
        return jsonify({
            'message': 'Dependency removed successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enhanced_tasks_bp.route('/api/tasks/<task_gid>/subtasks', methods=['GET'])
@auth_required
def get_task_subtasks(task_gid):
    """Buscar subtarefas de uma tarefa."""
    try:
        task = Task.query.get(task_gid)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        subtasks = Task.query.filter_by(parent_gid=task_gid).all()
        return jsonify([subtask.to_dict() for subtask in subtasks]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_tasks_bp.route('/api/tasks/<task_gid>/blocked-tasks', methods=['GET'])
@auth_required
def get_blocked_tasks(task_gid):
    """Buscar tarefas que dependem desta tarefa (tarefas bloqueadas por esta)."""
    try:
        task = Task.query.get(task_gid)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        blocked_tasks = []
        for dependent in task.dependents:
            # Verificar se a tarefa dependente está realmente bloqueada
            is_blocked = not task.completed
            blocked_tasks.append({
                **dependent.to_dict(),
                'is_blocked': is_blocked,
                'blocking_task': {
                    'gid': task.gid,
                    'name': task.name,
                    'completed': task.completed
                }
            })
        
        return jsonify(blocked_tasks), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _creates_dependency_cycle(task_gid, dependency_gid, visited=None):
    """Verifica se adicionar uma dependência criaria um ciclo."""
    if visited is None:
        visited = set()
    
    if dependency_gid == task_gid:
        return True
    
    if dependency_gid in visited:
        return False
    
    visited.add(dependency_gid)
    
    # Buscar dependências da tarefa que seria adicionada como dependência
    dependency_task = Task.query.get(dependency_gid)
    if not dependency_task:
        return False
    
    for dep in dependency_task.dependencies:
        if _creates_dependency_cycle(task_gid, dep.gid, visited.copy()):
            return True
    
    return False

