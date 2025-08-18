from flask import Blueprint, request, jsonify, g
from src.models.enhanced_work_graph import db, CustomField, CustomFieldValue, Workspace
from src.routes.auth import auth_required
from datetime import datetime
import json

custom_fields_bp = Blueprint('custom_fields', __name__)

@custom_fields_bp.route('/api/custom-fields', methods=['GET'])
@auth_required
def get_custom_fields():
    """Buscar campos personalizados de um workspace."""
    try:
        workspace_gid = request.args.get('workspace_gid')
        if not workspace_gid:
            return jsonify({'error': 'workspace_gid is required'}), 400
        
        custom_fields = CustomField.query.filter_by(workspace_gid=workspace_gid).all()
        return jsonify([cf.to_dict() for cf in custom_fields]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-fields', methods=['POST'])
@auth_required
def create_custom_field():
    """Criar novo campo personalizado."""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if not data.get('type'):
            return jsonify({'error': 'Type is required'}), 400
        if not data.get('workspace_gid'):
            return jsonify({'error': 'Workspace GID is required'}), 400
        
        # Verificar se workspace existe
        workspace = Workspace.query.get(data['workspace_gid'])
        if not workspace:
            return jsonify({'error': 'Workspace not found'}), 404
        
        # Validar tipo
        valid_types = ['text', 'number', 'enum', 'multi_enum', 'date']
        if data['type'] not in valid_types:
            return jsonify({'error': f'Type must be one of: {", ".join(valid_types)}'}), 400
        
        # Criar campo personalizado
        custom_field = CustomField(
            name=data['name'],
            description=data.get('description'),
            type=data['type'],
            workspace_gid=data['workspace_gid']
        )
        
        # Configurações específicas por tipo
        if data['type'] in ['enum', 'multi_enum']:
            enum_options = data.get('enum_options', [])
            if not enum_options:
                return jsonify({'error': 'enum_options is required for enum types'}), 400
            custom_field.enum_options = json.dumps(enum_options)
        
        if data['type'] == 'number':
            custom_field.number_value_min = data.get('number_value_min')
            custom_field.number_value_max = data.get('number_value_max')
            custom_field.precision = data.get('precision', 0)
        
        db.session.add(custom_field)
        db.session.commit()
        
        return jsonify(custom_field.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-fields/<custom_field_gid>', methods=['GET'])
@auth_required
def get_custom_field(custom_field_gid):
    """Buscar campo personalizado específico."""
    try:
        custom_field = CustomField.query.get(custom_field_gid)
        if not custom_field:
            return jsonify({'error': 'Custom field not found'}), 404
        
        return jsonify(custom_field.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-fields/<custom_field_gid>', methods=['PUT'])
@auth_required
def update_custom_field(custom_field_gid):
    """Atualizar campo personalizado."""
    try:
        custom_field = CustomField.query.get(custom_field_gid)
        if not custom_field:
            return jsonify({'error': 'Custom field not found'}), 404
        
        data = request.get_json()
        
        # Atualizar campos básicos
        if 'name' in data:
            custom_field.name = data['name']
        if 'description' in data:
            custom_field.description = data['description']
        
        # Atualizar configurações específicas por tipo
        if custom_field.type in ['enum', 'multi_enum'] and 'enum_options' in data:
            custom_field.enum_options = json.dumps(data['enum_options'])
        
        if custom_field.type == 'number':
            if 'number_value_min' in data:
                custom_field.number_value_min = data['number_value_min']
            if 'number_value_max' in data:
                custom_field.number_value_max = data['number_value_max']
            if 'precision' in data:
                custom_field.precision = data['precision']
        
        db.session.commit()
        
        return jsonify(custom_field.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-fields/<custom_field_gid>', methods=['DELETE'])
@auth_required
def delete_custom_field(custom_field_gid):
    """Deletar campo personalizado."""
    try:
        custom_field = CustomField.query.get(custom_field_gid)
        if not custom_field:
            return jsonify({'error': 'Custom field not found'}), 404
        
        # Verificar se há valores associados
        values_count = CustomFieldValue.query.filter_by(custom_field_gid=custom_field_gid).count()
        if values_count > 0:
            return jsonify({
                'error': f'Cannot delete custom field. It has {values_count} associated values.'
            }), 400
        
        db.session.delete(custom_field)
        db.session.commit()
        
        return jsonify({'message': 'Custom field deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-fields/<custom_field_gid>/values', methods=['GET'])
@auth_required
def get_custom_field_values(custom_field_gid):
    """Buscar todos os valores de um campo personalizado."""
    try:
        custom_field = CustomField.query.get(custom_field_gid)
        if not custom_field:
            return jsonify({'error': 'Custom field not found'}), 404
        
        # Filtros opcionais
        task_gid = request.args.get('task_gid')
        
        query = CustomFieldValue.query.filter_by(custom_field_gid=custom_field_gid)
        
        if task_gid:
            query = query.filter_by(task_gid=task_gid)
        
        values = query.all()
        
        result = []
        for value in values:
            value_data = value.to_dict()
            # Incluir dados da tarefa associada
            if value.task:
                value_data['task'] = {
                    'gid': value.task.gid,
                    'name': value.task.name
                }
            result.append(value_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-field-values', methods=['POST'])
@auth_required
def create_custom_field_value():
    """Criar ou atualizar valor de campo personalizado para uma tarefa."""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('custom_field_gid'):
            return jsonify({'error': 'custom_field_gid is required'}), 400
        if not data.get('task_gid'):
            return jsonify({'error': 'task_gid is required'}), 400
        
        custom_field = CustomField.query.get(data['custom_field_gid'])
        if not custom_field:
            return jsonify({'error': 'Custom field not found'}), 404
        
        # Verificar se já existe valor para esta tarefa e campo
        existing_value = CustomFieldValue.query.filter_by(
            custom_field_gid=data['custom_field_gid'],
            task_gid=data['task_gid']
        ).first()
        
        if existing_value:
            # Atualizar valor existente
            cfv = existing_value
        else:
            # Criar novo valor
            cfv = CustomFieldValue(
                custom_field_gid=data['custom_field_gid'],
                task_gid=data['task_gid']
            )
        
        # Definir valor baseado no tipo do campo
        if custom_field.type == 'text':
            if 'text_value' not in data:
                return jsonify({'error': 'text_value is required for text fields'}), 400
            cfv.text_value = data['text_value']
            # Limpar outros valores
            cfv.number_value = None
            cfv.enum_value = None
            cfv.multi_enum_values = None
            cfv.date_value = None
            
        elif custom_field.type == 'number':
            if 'number_value' not in data:
                return jsonify({'error': 'number_value is required for number fields'}), 400
            
            number_value = data['number_value']
            
            # Validar limites se definidos
            if custom_field.number_value_min is not None and number_value < custom_field.number_value_min:
                return jsonify({'error': f'Value must be at least {custom_field.number_value_min}'}), 400
            if custom_field.number_value_max is not None and number_value > custom_field.number_value_max:
                return jsonify({'error': f'Value must be at most {custom_field.number_value_max}'}), 400
            
            cfv.number_value = number_value
            # Limpar outros valores
            cfv.text_value = None
            cfv.enum_value = None
            cfv.multi_enum_values = None
            cfv.date_value = None
            
        elif custom_field.type == 'enum':
            if 'enum_value' not in data:
                return jsonify({'error': 'enum_value is required for enum fields'}), 400
            
            # Validar se valor está nas opções
            enum_options = json.loads(custom_field.enum_options) if custom_field.enum_options else []
            if data['enum_value'] not in enum_options:
                return jsonify({'error': f'Value must be one of: {", ".join(enum_options)}'}), 400
            
            cfv.enum_value = data['enum_value']
            # Limpar outros valores
            cfv.text_value = None
            cfv.number_value = None
            cfv.multi_enum_values = None
            cfv.date_value = None
            
        elif custom_field.type == 'multi_enum':
            if 'multi_enum_values' not in data:
                return jsonify({'error': 'multi_enum_values is required for multi_enum fields'}), 400
            
            # Validar se todos os valores estão nas opções
            enum_options = json.loads(custom_field.enum_options) if custom_field.enum_options else []
            multi_values = data['multi_enum_values']
            
            if not isinstance(multi_values, list):
                return jsonify({'error': 'multi_enum_values must be a list'}), 400
            
            for value in multi_values:
                if value not in enum_options:
                    return jsonify({'error': f'All values must be from: {", ".join(enum_options)}'}), 400
            
            cfv.multi_enum_values = json.dumps(multi_values)
            # Limpar outros valores
            cfv.text_value = None
            cfv.number_value = None
            cfv.enum_value = None
            cfv.date_value = None
            
        elif custom_field.type == 'date':
            if 'date_value' not in data:
                return jsonify({'error': 'date_value is required for date fields'}), 400
            
            try:
                cfv.date_value = datetime.strptime(data['date_value'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'date_value must be in YYYY-MM-DD format'}), 400
            
            # Limpar outros valores
            cfv.text_value = None
            cfv.number_value = None
            cfv.enum_value = None
            cfv.multi_enum_values = None
        
        cfv.modified_at = datetime.utcnow()
        
        if not existing_value:
            db.session.add(cfv)
        
        db.session.commit()
        
        return jsonify(cfv.to_dict()), 201 if not existing_value else 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/custom-field-values/<value_gid>', methods=['DELETE'])
@auth_required
def delete_custom_field_value(value_gid):
    """Deletar valor de campo personalizado."""
    try:
        cfv = CustomFieldValue.query.get(value_gid)
        if not cfv:
            return jsonify({'error': 'Custom field value not found'}), 404
        
        db.session.delete(cfv)
        db.session.commit()
        
        return jsonify({'message': 'Custom field value deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@custom_fields_bp.route('/api/tasks/<task_gid>/custom-field-values', methods=['GET'])
@auth_required
def get_task_custom_field_values(task_gid):
    """Buscar todos os valores de campos personalizados de uma tarefa."""
    try:
        from src.models.enhanced_work_graph import Task
        
        task = Task.query.get(task_gid)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        result = []
        for cfv in task.custom_field_values:
            cfv_data = cfv.to_dict()
            cfv_data['custom_field'] = cfv.custom_field.to_dict()
            result.append(cfv_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

