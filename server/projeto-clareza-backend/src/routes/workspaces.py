from flask import Blueprint, request, jsonify
from src.models.work_graph import db, Workspace
import uuid
import json

workspaces_bp = Blueprint('workspaces', __name__)

@workspaces_bp.route('/workspaces', methods=['POST'])
def create_workspace():
    """Criar um novo workspace"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'name' not in data:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        
        # Criar novo workspace
        workspace = Workspace(
            gid=str(uuid.uuid4()),
            name=data['name'],
            is_organization=data.get('is_organization', False),
            email_domains=json.dumps(data.get('email_domains', []))
        )
        
        db.session.add(workspace)
        db.session.commit()
        
        return jsonify(workspace.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workspaces_bp.route('/workspaces/<workspace_id>', methods=['GET'])
def get_workspace(workspace_id):
    """Obter workspace por ID"""
    try:
        workspace = Workspace.query.get(workspace_id)
        
        if not workspace:
            return jsonify({'error': 'Workspace não encontrado'}), 404
        
        return jsonify(workspace.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspaces_bp.route('/workspaces', methods=['GET'])
def list_workspaces():
    """Listar todos os workspaces"""
    try:
        workspaces = Workspace.query.all()
        return jsonify([workspace.to_dict() for workspace in workspaces]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workspaces_bp.route('/workspaces/<workspace_id>', methods=['PUT'])
def update_workspace(workspace_id):
    """Atualizar workspace"""
    try:
        workspace = Workspace.query.get(workspace_id)
        
        if not workspace:
            return jsonify({'error': 'Workspace não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos se fornecidos
        if 'name' in data:
            workspace.name = data['name']
        if 'is_organization' in data:
            workspace.is_organization = data['is_organization']
        if 'email_domains' in data:
            workspace.email_domains = json.dumps(data['email_domains'])
        
        db.session.commit()
        
        return jsonify(workspace.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workspaces_bp.route('/workspaces/<workspace_id>', methods=['DELETE'])
def delete_workspace(workspace_id):
    """Deletar workspace"""
    try:
        workspace = Workspace.query.get(workspace_id)
        
        if not workspace:
            return jsonify({'error': 'Workspace não encontrado'}), 404
        
        db.session.delete(workspace)
        db.session.commit()
        
        return jsonify({'message': 'Workspace deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

