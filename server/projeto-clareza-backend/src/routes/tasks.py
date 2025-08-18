from flask import Blueprint, request, jsonify
from src.models.work_graph import db, Task, User, Workspace, Project, ProjectTask
import uuid
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    """Criar uma nova tarefa"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'name' not in data or 'workspace_gid' not in data:
            return jsonify({'error': 'Nome e workspace_gid são obrigatórios'}), 400
        
        # Verificar se workspace existe
        workspace = Workspace.query.get(data['workspace_gid'])
        if not workspace:
            return jsonify({'error': 'Workspace não encontrado'}), 404
        
        # Verificar se assignee existe (se fornecido)
        if 'assignee_gid' in data and data['assignee_gid']:
            assignee = User.query.get(data['assignee_gid'])
            if not assignee:
                return jsonify({'error': 'Usuário responsável não encontrado'}), 404
        
        # Verificar se parent task existe (se fornecido)
        if 'parent_gid' in data and data['parent_gid']:
            parent_task = Task.query.get(data['parent_gid'])
            if not parent_task:
                return jsonify({'error': 'Tarefa pai não encontrada'}), 404
        
        # Criar nova tarefa
        task = Task(
            gid=str(uuid.uuid4()),
            name=data['name'],
            notes=data.get('notes', ''),
            assignee_gid=data.get('assignee_gid'),
            completed=data.get('completed', False),
            due_on=data.get('due_on'),
            start_on=data.get('start_on'),
            parent_gid=data.get('parent_gid'),
            workspace_gid=data['workspace_gid'],
            resource_subtype=data.get('resource_subtype')
        )
        
        db.session.add(task)
        
        # Se project_gids for fornecido, adicionar tarefa aos projetos (multi-homing)
        if 'project_gids' in data and data['project_gids']:
            for project_gid in data['project_gids']:
                project = Project.query.get(project_gid)
                if project:
                    project_task = ProjectTask(project_gid=project_gid, task_gid=task.gid)
                    db.session.add(project_task)
        
        db.session.commit()
        
        return jsonify(task.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Obter tarefa por ID"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        return jsonify(task.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """Listar tarefas com filtros opcionais"""
    try:
        # Filtros disponíveis
        workspace_gid = request.args.get('workspace_gid')
        project_gid = request.args.get('project_gid')
        assignee_gid = request.args.get('assignee_gid')
        completed = request.args.get('completed')
        
        query = Task.query
        
        if workspace_gid:
            query = query.filter_by(workspace_gid=workspace_gid)
        
        if assignee_gid:
            query = query.filter_by(assignee_gid=assignee_gid)
        
        if completed is not None:
            completed_bool = completed.lower() == 'true'
            query = query.filter_by(completed=completed_bool)
        
        # Filtrar por projeto (usando tabela de junção)
        if project_gid:
            query = query.join(ProjectTask).filter(ProjectTask.project_gid == project_gid)
        
        tasks = query.all()
        
        return jsonify([task.to_dict() for task in tasks]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/projects/<project_id>/tasks', methods=['GET'])
def get_project_tasks(project_id):
    """Obter todas as tarefas de um projeto específico"""
    try:
        # Verificar se projeto existe
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Projeto não encontrado'}), 404
        
        # Buscar tarefas do projeto através da tabela de junção
        tasks = db.session.query(Task).join(ProjectTask).filter(
            ProjectTask.project_gid == project_id
        ).all()
        
        return jsonify([task.to_dict() for task in tasks]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Atualizar tarefa"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        data = request.get_json()
        
        # Atualizar campos se fornecidos
        if 'name' in data:
            task.name = data['name']
        if 'notes' in data:
            task.notes = data['notes']
        if 'assignee_gid' in data:
            if data['assignee_gid']:
                assignee = User.query.get(data['assignee_gid'])
                if not assignee:
                    return jsonify({'error': 'Usuário responsável não encontrado'}), 404
            task.assignee_gid = data['assignee_gid']
        if 'completed' in data:
            task.completed = data['completed']
            # Se marcada como concluída, definir completed_at
            if data['completed']:
                task.completed_at = datetime.utcnow()
            else:
                task.completed_at = None
        if 'due_on' in data:
            task.due_on = data['due_on']
        if 'start_on' in data:
            task.start_on = data['start_on']
        if 'parent_gid' in data:
            if data['parent_gid']:
                parent_task = Task.query.get(data['parent_gid'])
                if not parent_task:
                    return jsonify({'error': 'Tarefa pai não encontrada'}), 404
            task.parent_gid = data['parent_gid']
        if 'resource_subtype' in data:
            task.resource_subtype = data['resource_subtype']
        
        # Atualizar modified_at
        task.modified_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(task.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Deletar tarefa"""
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        # Remover associações com projetos
        ProjectTask.query.filter_by(task_gid=task_id).delete()
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Tarefa deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/tasks/<task_id>/projects', methods=['POST'])
def add_task_to_project(task_id):
    """Adicionar tarefa a um projeto (multi-homing)"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        data = request.get_json()
        if not data or 'project_gid' not in data:
            return jsonify({'error': 'project_gid é obrigatório'}), 400
        
        project = Project.query.get(data['project_gid'])
        if not project:
            return jsonify({'error': 'Projeto não encontrado'}), 404
        
        # Verificar se associação já existe
        existing = ProjectTask.query.filter_by(
            project_gid=data['project_gid'],
            task_gid=task_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Tarefa já está associada a este projeto'}), 400
        
        # Criar associação
        project_task = ProjectTask(project_gid=data['project_gid'], task_gid=task_id)
        db.session.add(project_task)
        db.session.commit()
        
        return jsonify({'message': 'Tarefa adicionada ao projeto com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/tasks/<task_id>/projects/<project_id>', methods=['DELETE'])
def remove_task_from_project(task_id, project_id):
    """Remover tarefa de um projeto"""
    try:
        project_task = ProjectTask.query.filter_by(
            project_gid=project_id,
            task_gid=task_id
        ).first()
        
        if not project_task:
            return jsonify({'error': 'Associação não encontrada'}), 404
        
        db.session.delete(project_task)
        db.session.commit()
        
        return jsonify({'message': 'Tarefa removida do projeto com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

