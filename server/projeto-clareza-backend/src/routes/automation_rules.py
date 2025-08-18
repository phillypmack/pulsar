from flask import Blueprint, request, jsonify, g
from src.models.enhanced_work_graph import db, AutomationRule, Project
from src.routes.auth import auth_required
from datetime import datetime
import json

automation_rules_bp = Blueprint('automation_rules', __name__)

@automation_rules_bp.route('/api/automation-rules', methods=['GET'])
@auth_required
def get_automation_rules():
    """Buscar regras de automação."""
    try:
        project_gid = request.args.get('project_gid')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = AutomationRule.query
        
        if project_gid:
            query = query.filter_by(project_gid=project_gid)
        
        if active_only:
            query = query.filter_by(active=True)
        
        rules = query.all()
        return jsonify([rule.to_dict() for rule in rules]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules', methods=['POST'])
@auth_required
def create_automation_rule():
    """Criar nova regra de automação."""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if not data.get('project_gid'):
            return jsonify({'error': 'Project GID is required'}), 400
        if not data.get('trigger_type'):
            return jsonify({'error': 'Trigger type is required'}), 400
        if not data.get('action_type'):
            return jsonify({'error': 'Action type is required'}), 400
        
        # Verificar se projeto existe
        project = Project.query.get(data['project_gid'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Validar tipos de trigger
        valid_triggers = [
            'task_created', 'task_completed', 'task_assigned', 'task_moved',
            'field_changed', 'due_date_approaching', 'task_overdue'
        ]
        if data['trigger_type'] not in valid_triggers:
            return jsonify({'error': f'Trigger type must be one of: {", ".join(valid_triggers)}'}), 400
        
        # Validar tipos de ação
        valid_actions = [
            'move_to_section', 'assign_task', 'mark_complete', 'add_to_project',
            'set_due_date', 'add_comment', 'send_notification'
        ]
        if data['action_type'] not in valid_actions:
            return jsonify({'error': f'Action type must be one of: {", ".join(valid_actions)}'}), 400
        
        # Criar regra
        rule = AutomationRule(
            name=data['name'],
            project_gid=data['project_gid'],
            trigger_type=data['trigger_type'],
            action_type=data['action_type'],
            active=data.get('active', True)
        )
        
        # Processar condições do trigger
        trigger_conditions = data.get('trigger_conditions', {})
        if trigger_conditions:
            rule.trigger_conditions = json.dumps(trigger_conditions)
        
        # Processar parâmetros da ação
        action_parameters = data.get('action_parameters', {})
        if action_parameters:
            rule.action_parameters = json.dumps(action_parameters)
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify(rule.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules/<rule_gid>', methods=['GET'])
@auth_required
def get_automation_rule(rule_gid):
    """Buscar regra de automação específica."""
    try:
        rule = AutomationRule.query.get(rule_gid)
        if not rule:
            return jsonify({'error': 'Automation rule not found'}), 404
        
        return jsonify(rule.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules/<rule_gid>', methods=['PUT'])
@auth_required
def update_automation_rule(rule_gid):
    """Atualizar regra de automação."""
    try:
        rule = AutomationRule.query.get(rule_gid)
        if not rule:
            return jsonify({'error': 'Automation rule not found'}), 404
        
        data = request.get_json()
        
        # Atualizar campos básicos
        if 'name' in data:
            rule.name = data['name']
        if 'active' in data:
            rule.active = data['active']
        
        # Atualizar condições do trigger
        if 'trigger_conditions' in data:
            rule.trigger_conditions = json.dumps(data['trigger_conditions'])
        
        # Atualizar parâmetros da ação
        if 'action_parameters' in data:
            rule.action_parameters = json.dumps(data['action_parameters'])
        
        db.session.commit()
        
        return jsonify(rule.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules/<rule_gid>', methods=['DELETE'])
@auth_required
def delete_automation_rule(rule_gid):
    """Deletar regra de automação."""
    try:
        rule = AutomationRule.query.get(rule_gid)
        if not rule:
            return jsonify({'error': 'Automation rule not found'}), 404
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({'message': 'Automation rule deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules/<rule_gid>/toggle', methods=['POST'])
@auth_required
def toggle_automation_rule(rule_gid):
    """Ativar/desativar regra de automação."""
    try:
        rule = AutomationRule.query.get(rule_gid)
        if not rule:
            return jsonify({'error': 'Automation rule not found'}), 404
        
        rule.active = not rule.active
        db.session.commit()
        
        return jsonify({
            'message': f'Automation rule {"activated" if rule.active else "deactivated"} successfully',
            'rule': rule.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules/templates', methods=['GET'])
@auth_required
def get_automation_rule_templates():
    """Buscar templates de regras de automação predefinidas."""
    try:
        templates = [
            {
                'name': 'Mover tarefas concluídas para "Concluído"',
                'description': 'Quando uma tarefa é marcada como concluída, move automaticamente para a seção "Concluído"',
                'trigger_type': 'task_completed',
                'trigger_conditions': {},
                'action_type': 'move_to_section',
                'action_parameters': {
                    'section_name': 'Concluído'
                }
            },
            {
                'name': 'Atribuir tarefas criadas ao proprietário do projeto',
                'description': 'Quando uma nova tarefa é criada, atribui automaticamente ao proprietário do projeto',
                'trigger_type': 'task_created',
                'trigger_conditions': {},
                'action_type': 'assign_task',
                'action_parameters': {
                    'assign_to': 'project_owner'
                }
            },
            {
                'name': 'Notificar sobre tarefas com prazo próximo',
                'description': 'Envia notificação quando uma tarefa tem prazo em 2 dias',
                'trigger_type': 'due_date_approaching',
                'trigger_conditions': {
                    'days_before': 2
                },
                'action_type': 'send_notification',
                'action_parameters': {
                    'notification_type': 'due_soon',
                    'recipients': ['assignee']
                }
            },
            {
                'name': 'Marcar tarefas dependentes como prontas',
                'description': 'Quando uma tarefa é concluída, marca suas dependentes como prontas para começar',
                'trigger_type': 'task_completed',
                'trigger_conditions': {},
                'action_type': 'send_notification',
                'action_parameters': {
                    'notification_type': 'dependency_completed',
                    'recipients': ['dependent_assignees']
                }
            },
            {
                'name': 'Mover tarefas atrasadas para "Atrasado"',
                'description': 'Quando uma tarefa passa do prazo, move automaticamente para a seção "Atrasado"',
                'trigger_type': 'task_overdue',
                'trigger_conditions': {},
                'action_type': 'move_to_section',
                'action_parameters': {
                    'section_name': 'Atrasado'
                }
            }
        ]
        
        return jsonify(templates), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_rules_bp.route('/api/automation-rules/test/<rule_gid>', methods=['POST'])
@auth_required
def test_automation_rule(rule_gid):
    """Testar regra de automação com dados simulados."""
    try:
        rule = AutomationRule.query.get(rule_gid)
        if not rule:
            return jsonify({'error': 'Automation rule not found'}), 404
        
        data = request.get_json()
        test_data = data.get('test_data', {})
        
        # Simular execução da regra
        from src.tasks.automation_tasks import process_automation_rules
        
        # Executar regra de forma síncrona para teste
        result = process_automation_rules(
            rule.trigger_type,
            test_data.get('target_gid', 'test-task-id'),
            test_data.get('target_type', 'task'),
            g.current_user.gid,
            test_data.get('workspace_gid', 'test-workspace-id'),
            rule.project_gid,
            test_data
        )
        
        return jsonify({
            'message': 'Rule test completed',
            'rule': rule.to_dict(),
            'test_result': result,
            'test_data': test_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

