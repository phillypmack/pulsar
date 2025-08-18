from flask import Blueprint, request, jsonify, g
from src.models.enhanced_work_graph import db, Section, Project, Task
from src.routes.auth import auth_required
from datetime import datetime

sections_bp = Blueprint('sections', __name__)

@sections_bp.route('/api/sections', methods=['GET'])
@auth_required
def get_sections():
    """Buscar seções de um projeto."""
    try:
        project_gid = request.args.get('project_gid')
        if not project_gid:
            return jsonify({'error': 'project_gid is required'}), 400
        
        # Verificar se projeto existe
        project = Project.query.get(project_gid)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        sections = Section.query.filter_by(project_gid=project_gid).order_by(Section.created_at).all()
        
        # Incluir contagem de tarefas se solicitado
        include_task_count = request.args.get('include_task_count', 'false').lower() == 'true'
        
        result = []
        for section in sections:
            section_data = section.to_dict()
            
            if include_task_count:
                task_count = Task.query.filter_by(section_gid=section.gid).count()
                completed_count = Task.query.filter_by(section_gid=section.gid, completed=True).count()
                section_data['task_count'] = task_count
                section_data['completed_count'] = completed_count
                section_data['pending_count'] = task_count - completed_count
            
            result.append(section_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections', methods=['POST'])
@auth_required
def create_section():
    """Criar nova seção."""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if not data.get('project_gid'):
            return jsonify({'error': 'Project GID is required'}), 400
        
        # Verificar se projeto existe
        project = Project.query.get(data['project_gid'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Criar seção
        section = Section(
            name=data['name'],
            project_gid=data['project_gid']
        )
        
        db.session.add(section)
        db.session.commit()
        
        return jsonify(section.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/<section_gid>', methods=['GET'])
@auth_required
def get_section(section_gid):
    """Buscar seção específica."""
    try:
        section = Section.query.get(section_gid)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        section_data = section.to_dict()
        
        # Incluir tarefas se solicitado
        include_tasks = request.args.get('include_tasks', 'false').lower() == 'true'
        if include_tasks:
            tasks = Task.query.filter_by(section_gid=section_gid).all()
            section_data['tasks'] = [task.to_dict() for task in tasks]
        
        return jsonify(section_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/<section_gid>', methods=['PUT'])
@auth_required
def update_section(section_gid):
    """Atualizar seção."""
    try:
        section = Section.query.get(section_gid)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        data = request.get_json()
        
        # Atualizar campos
        if 'name' in data:
            section.name = data['name']
        
        db.session.commit()
        
        return jsonify(section.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/<section_gid>', methods=['DELETE'])
@auth_required
def delete_section(section_gid):
    """Deletar seção."""
    try:
        section = Section.query.get(section_gid)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Verificar se há tarefas na seção
        task_count = Task.query.filter_by(section_gid=section_gid).count()
        if task_count > 0:
            return jsonify({
                'error': f'Cannot delete section. It contains {task_count} tasks. Move or delete tasks first.'
            }), 400
        
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({'message': 'Section deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/<section_gid>/tasks', methods=['GET'])
@auth_required
def get_section_tasks(section_gid):
    """Buscar tarefas de uma seção."""
    try:
        section = Section.query.get(section_gid)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Filtros opcionais
        completed = request.args.get('completed')
        assignee_gid = request.args.get('assignee_gid')
        
        query = Task.query.filter_by(section_gid=section_gid)
        
        if completed is not None:
            completed_bool = completed.lower() == 'true'
            query = query.filter_by(completed=completed_bool)
        
        if assignee_gid:
            query = query.filter_by(assignee_gid=assignee_gid)
        
        tasks = query.all()
        
        return jsonify([task.to_dict() for task in tasks]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/<section_gid>/move-tasks', methods=['POST'])
@auth_required
def move_tasks_to_section(section_gid):
    """Mover múltiplas tarefas para uma seção."""
    try:
        section = Section.query.get(section_gid)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        data = request.get_json()
        task_gids = data.get('task_gids', [])
        
        if not task_gids:
            return jsonify({'error': 'task_gids is required'}), 400
        
        moved_tasks = []
        for task_gid in task_gids:
            task = Task.query.get(task_gid)
            if task:
                task.section_gid = section_gid
                task.modified_at = datetime.utcnow()
                moved_tasks.append(task.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'message': f'Moved {len(moved_tasks)} tasks to section',
            'section': section.to_dict(),
            'moved_tasks': moved_tasks
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/reorder', methods=['POST'])
@auth_required
def reorder_sections():
    """Reordenar seções de um projeto."""
    try:
        data = request.get_json()
        project_gid = data.get('project_gid')
        section_order = data.get('section_order', [])  # Lista de GIDs na ordem desejada
        
        if not project_gid:
            return jsonify({'error': 'project_gid is required'}), 400
        
        # Verificar se projeto existe
        project = Project.query.get(project_gid)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Atualizar ordem das seções
        # Por simplicidade, vamos usar o timestamp created_at para simular ordem
        # Em uma implementação real, adicionaríamos um campo 'order' ou 'position'
        
        updated_sections = []
        base_time = datetime.utcnow()
        
        for i, section_gid in enumerate(section_order):
            section = Section.query.get(section_gid)
            if section and section.project_gid == project_gid:
                # Usar timestamp para simular ordem (seção mais antiga = primeira)
                section.created_at = base_time - timedelta(seconds=len(section_order) - i)
                updated_sections.append(section.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sections reordered successfully',
            'sections': updated_sections
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sections_bp.route('/api/sections/<section_gid>/duplicate', methods=['POST'])
@auth_required
def duplicate_section(section_gid):
    """Duplicar uma seção (com ou sem tarefas)."""
    try:
        section = Section.query.get(section_gid)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        data = request.get_json()
        include_tasks = data.get('include_tasks', False)
        new_name = data.get('name', f"{section.name} (Cópia)")
        
        # Criar nova seção
        new_section = Section(
            name=new_name,
            project_gid=section.project_gid
        )
        
        db.session.add(new_section)
        db.session.flush()  # Para obter o GID da nova seção
        
        # Duplicar tarefas se solicitado
        duplicated_tasks = []
        if include_tasks:
            tasks = Task.query.filter_by(section_gid=section_gid).all()
            
            for task in tasks:
                new_task = Task(
                    name=f"{task.name} (Cópia)",
                    notes=task.notes,
                    assignee_gid=task.assignee_gid,
                    workspace_gid=task.workspace_gid,
                    section_gid=new_section.gid,
                    due_on=task.due_on,
                    start_on=task.start_on,
                    resource_subtype=task.resource_subtype,
                    parent_gid=task.parent_gid
                )
                
                db.session.add(new_task)
                duplicated_tasks.append(new_task)
        
        db.session.commit()
        
        result = new_section.to_dict()
        if include_tasks:
            result['duplicated_tasks'] = [task.to_dict() for task in duplicated_tasks]
            result['duplicated_task_count'] = len(duplicated_tasks)
        
        return jsonify({
            'message': 'Section duplicated successfully',
            'section': result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

