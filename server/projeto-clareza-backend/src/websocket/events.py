from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from functools import wraps
import jwt
import logging
from src.config import Config
from src.models.enhanced_work_graph import User

logger = logging.getLogger(__name__)

def authenticated_only(f):
    """Decorator para garantir que apenas usuários autenticados acessem eventos WebSocket."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            # Obter token do handshake
            token = request.args.get('token')
            if not token:
                logger.warning("WebSocket connection attempted without token")
                disconnect()
                return False
            
            # Verificar token JWT
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            user_gid = payload.get('user_gid')
            
            if not user_gid:
                logger.warning("Invalid token in WebSocket connection")
                disconnect()
                return False
            
            # Verificar se usuário existe
            user = User.query.get(user_gid)
            if not user:
                logger.warning(f"User {user_gid} not found for WebSocket connection")
                disconnect()
                return False
            
            # Adicionar usuário ao contexto
            kwargs['current_user'] = user
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token in WebSocket connection")
            disconnect()
            return False
        except jwt.InvalidTokenError:
            logger.warning("Invalid token in WebSocket connection")
            disconnect()
            return False
        except Exception as e:
            logger.error(f"Error in WebSocket authentication: {str(e)}")
            disconnect()
            return False
    
    return wrapped

def init_websocket_events(socketio):
    """Inicializa todos os eventos WebSocket."""
    
    @socketio.on('connect')
    @authenticated_only
    def handle_connect(current_user):
        """Evento de conexão WebSocket."""
        logger.info(f"User {current_user.name} ({current_user.gid}) connected via WebSocket")
        emit('connected', {
            'message': 'Connected successfully',
            'user': current_user.to_dict()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Evento de desconexão WebSocket."""
        logger.info("User disconnected from WebSocket")
    
    @socketio.on('join_project')
    @authenticated_only
    def handle_join_project(data, current_user):
        """Usuário entra em uma sala de projeto para receber atualizações em tempo real."""
        try:
            project_gid = data.get('project_gid')
            if not project_gid:
                emit('error', {'message': 'project_gid is required'})
                return
            
            # Verificar se usuário tem acesso ao projeto
            from src.models.enhanced_work_graph import Project
            project = Project.query.get(project_gid)
            if not project:
                emit('error', {'message': 'Project not found'})
                return
            
            # Entrar na sala do projeto
            room = f"project_{project_gid}"
            join_room(room)
            
            logger.info(f"User {current_user.name} joined project room {room}")
            emit('joined_project', {
                'project_gid': project_gid,
                'project_name': project.name
            })
            
            # Notificar outros usuários na sala
            emit('user_joined_project', {
                'user_name': current_user.name,
                'user_gid': current_user.gid,
                'project_gid': project_gid
            }, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error joining project room: {str(e)}")
            emit('error', {'message': 'Failed to join project'})
    
    @socketio.on('leave_project')
    @authenticated_only
    def handle_leave_project(data, current_user):
        """Usuário sai de uma sala de projeto."""
        try:
            project_gid = data.get('project_gid')
            if not project_gid:
                emit('error', {'message': 'project_gid is required'})
                return
            
            room = f"project_{project_gid}"
            leave_room(room)
            
            logger.info(f"User {current_user.name} left project room {room}")
            emit('left_project', {'project_gid': project_gid})
            
            # Notificar outros usuários na sala
            emit('user_left_project', {
                'user_name': current_user.name,
                'user_gid': current_user.gid,
                'project_gid': project_gid
            }, room=room)
            
        except Exception as e:
            logger.error(f"Error leaving project room: {str(e)}")
            emit('error', {'message': 'Failed to leave project'})
    
    @socketio.on('join_workspace')
    @authenticated_only
    def handle_join_workspace(data, current_user):
        """Usuário entra em uma sala de workspace."""
        try:
            workspace_gid = data.get('workspace_gid')
            if not workspace_gid:
                emit('error', {'message': 'workspace_gid is required'})
                return
            
            # Verificar se usuário tem acesso ao workspace
            from src.models.enhanced_work_graph import Workspace
            workspace = Workspace.query.get(workspace_gid)
            if not workspace:
                emit('error', {'message': 'Workspace not found'})
                return
            
            room = f"workspace_{workspace_gid}"
            join_room(room)
            
            logger.info(f"User {current_user.name} joined workspace room {room}")
            emit('joined_workspace', {
                'workspace_gid': workspace_gid,
                'workspace_name': workspace.name
            })
            
        except Exception as e:
            logger.error(f"Error joining workspace room: {str(e)}")
            emit('error', {'message': 'Failed to join workspace'})
    
    @socketio.on('task_update')
    @authenticated_only
    def handle_task_update(data, current_user):
        """Recebe atualizações de tarefa em tempo real (usado para colaboração)."""
        try:
            task_gid = data.get('task_gid')
            update_type = data.get('update_type')  # 'name_change', 'status_change', 'assignment_change', etc.
            update_data = data.get('update_data', {})
            
            if not task_gid or not update_type:
                emit('error', {'message': 'task_gid and update_type are required'})
                return
            
            # Verificar se tarefa existe e usuário tem acesso
            from src.models.enhanced_work_graph import Task
            task = Task.query.get(task_gid)
            if not task:
                emit('error', {'message': 'Task not found'})
                return
            
            # Emitir atualização para todas as salas relevantes
            update_payload = {
                'task_gid': task_gid,
                'update_type': update_type,
                'update_data': update_data,
                'updated_by': {
                    'gid': current_user.gid,
                    'name': current_user.name
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Emitir para salas de projetos que contêm a tarefa
            for project in task.projects:
                room = f"project_{project.gid}"
                emit('task_updated', update_payload, room=room, include_self=False)
            
            # Emitir para sala do workspace
            workspace_room = f"workspace_{task.workspace_gid}"
            emit('task_updated', update_payload, room=workspace_room, include_self=False)
            
            logger.info(f"Task update broadcasted: {update_type} for task {task_gid}")
            
        except Exception as e:
            logger.error(f"Error handling task update: {str(e)}")
            emit('error', {'message': 'Failed to process task update'})
    
    @socketio.on('typing_indicator')
    @authenticated_only
    def handle_typing_indicator(data, current_user):
        """Gerencia indicadores de digitação em tempo real."""
        try:
            target_type = data.get('target_type')  # 'task', 'project'
            target_gid = data.get('target_gid')
            is_typing = data.get('is_typing', False)
            field = data.get('field', 'notes')  # Campo sendo editado
            
            if not target_type or not target_gid:
                emit('error', {'message': 'target_type and target_gid are required'})
                return
            
            # Determinar sala baseada no tipo de alvo
            if target_type == 'project':
                room = f"project_{target_gid}"
            elif target_type == 'task':
                # Buscar projetos da tarefa para determinar salas
                from src.models.enhanced_work_graph import Task
                task = Task.query.get(target_gid)
                if task and task.projects:
                    room = f"project_{task.projects[0].gid}"  # Usar primeiro projeto
                else:
                    emit('error', {'message': 'Task not found or not in any project'})
                    return
            else:
                emit('error', {'message': 'Invalid target_type'})
                return
            
            # Emitir indicador de digitação
            typing_payload = {
                'target_type': target_type,
                'target_gid': target_gid,
                'field': field,
                'is_typing': is_typing,
                'user': {
                    'gid': current_user.gid,
                    'name': current_user.name
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            emit('typing_indicator', typing_payload, room=room, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling typing indicator: {str(e)}")
            emit('error', {'message': 'Failed to process typing indicator'})

def broadcast_task_change(task_gid, change_type, change_data, actor_gid):
    """
    Função utilitária para transmitir mudanças de tarefa para todos os clientes conectados.
    Chamada pelas APIs REST quando há mudanças.
    """
    try:
        from src.models.enhanced_work_graph import Task, User
        from datetime import datetime
        
        task = Task.query.get(task_gid)
        actor = User.query.get(actor_gid)
        
        if not task or not actor:
            return
        
        # Preparar payload da mudança
        change_payload = {
            'task_gid': task_gid,
            'change_type': change_type,
            'change_data': change_data,
            'task_data': task.to_dict(),
            'changed_by': {
                'gid': actor.gid,
                'name': actor.name
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emitir para todas as salas relevantes
        from flask import current_app
        socketio = current_app.extensions['socketio']
        
        # Emitir para salas de projetos
        for project in task.projects:
            room = f"project_{project.gid}"
            socketio.emit('task_changed', change_payload, room=room)
        
        # Emitir para sala do workspace
        workspace_room = f"workspace_{task.workspace_gid}"
        socketio.emit('task_changed', change_payload, room=workspace_room)
        
        logger.info(f"Task change broadcasted: {change_type} for task {task_gid}")
        
    except Exception as e:
        logger.error(f"Error broadcasting task change: {str(e)}")

def broadcast_project_change(project_gid, change_type, change_data, actor_gid):
    """
    Função utilitária para transmitir mudanças de projeto.
    """
    try:
        from src.models.enhanced_work_graph import Project, User
        from datetime import datetime
        
        project = Project.query.get(project_gid)
        actor = User.query.get(actor_gid)
        
        if not project or not actor:
            return
        
        change_payload = {
            'project_gid': project_gid,
            'change_type': change_type,
            'change_data': change_data,
            'project_data': project.to_dict(),
            'changed_by': {
                'gid': actor.gid,
                'name': actor.name
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        from flask import current_app
        socketio = current_app.extensions['socketio']
        
        # Emitir para sala do projeto
        project_room = f"project_{project_gid}"
        socketio.emit('project_changed', change_payload, room=project_room)
        
        # Emitir para sala do workspace
        workspace_room = f"workspace_{project.workspace_gid}"
        socketio.emit('project_changed', change_payload, room=workspace_room)
        
        logger.info(f"Project change broadcasted: {change_type} for project {project_gid}")
        
    except Exception as e:
        logger.error(f"Error broadcasting project change: {str(e)}")

