from flask import Blueprint, request, jsonify
from src.models.work_graph import db, Project, User, Workspace, Team
import uuid

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects', methods=['POST'])
def create_project():
    """Criar um novo projeto"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'name' not in data or 'workspace_gid' not in data:
            return jsonify({'error': 'Nome e workspace_gid são obrigatórios'}), 400
        
        # Verificar se workspace existe
        workspace = Workspace.query.get(data['workspace_gid'])
        if not workspace:
            return jsonify({'error': 'Workspace não encontrado'}), 404
        
        # Verificar se owner existe (se fornecido)
        if 'owner_gid' in data:
            owner = User.query.get(data['owner_gid'])
            if not owner:
                return jsonify({'error': 'Usuário proprietário não encontrado'}), 404
        
        # Verificar se team existe (se fornecido)
        if 'team_gid' in data and data['team_gid']:
            team = Team.query.get(data['team_gid'])
            if not team:
                return jsonify({'error': 'Equipe não encontrada'}), 404
        
        # Criar novo projeto
        project = Project(
            gid=str(uuid.uuid4()),
            name=data['name'],
            owner_gid=data.get('owner_gid'),
            team_gid=data.get('team_gid'),
            workspace_gid=data['workspace_gid'],
            default_view=data.get('default_view', 'list'),
            color=data.get('color'),
            privacy_setting=data.get('privacy_setting'),
            due_on=data.get('due_on'),
            start_on=data.get('start_on')
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify(project.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Obter projeto por ID"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': 'Projeto não encontrado'}), 404
        
        return jsonify(project.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects', methods=['GET'])
def list_projects():
    """Listar todos os projetos"""
    try:
        # Filtrar por workspace se fornecido
        workspace_gid = request.args.get('workspace_gid')
        
        if workspace_gid:
            projects = Project.query.filter_by(workspace_gid=workspace_gid).all()
        else:
            projects = Project.query.all()
        
        return jsonify([project.to_dict() for project in projects]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Atualizar projeto"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': 'Projeto não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos se fornecidos
        if 'name' in data:
            project.name = data['name']
        if 'owner_gid' in data:
            if data['owner_gid']:
                owner = User.query.get(data['owner_gid'])
                if not owner:
                    return jsonify({'error': 'Usuário proprietário não encontrado'}), 404
            project.owner_gid = data['owner_gid']
        if 'team_gid' in data:
            if data['team_gid']:
                team = Team.query.get(data['team_gid'])
                if not team:
                    return jsonify({'error': 'Equipe não encontrada'}), 404
            project.team_gid = data['team_gid']
        if 'default_view' in data:
            project.default_view = data['default_view']
        if 'color' in data:
            project.color = data['color']
        if 'privacy_setting' in data:
            project.privacy_setting = data['privacy_setting']
        if 'due_on' in data:
            project.due_on = data['due_on']
        if 'start_on' in data:
            project.start_on = data['start_on']
        
        db.session.commit()
        
        return jsonify(project.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Deletar projeto"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': 'Projeto não encontrado'}), 404
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': 'Projeto deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

