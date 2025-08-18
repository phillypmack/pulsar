from flask import Blueprint, request, jsonify, g
from src.models.enhanced_work_graph import db, User
import jwt
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Chave secreta para JWT (em produção, usar variável de ambiente)
JWT_SECRET = os.environ.get('JWT_SECRET', 'sua-chave-secreta-super-segura')

def generate_token(user_gid):
    """Gerar token JWT para o usuário"""
    payload = {
        'user_gid': user_gid,
        'exp': datetime.utcnow() + timedelta(hours=24)  # Token expira em 24 horas
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    """Verificar e decodificar token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_gid']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Registrar novo usuário"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'name' not in data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
        
        # Verificar se email já existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email já está em uso'}), 400
        
        # Criar novo usuário
        user = User(
            gid=str(uuid.uuid4()),
            name=data['name'],
            email=data['email'],
            photo=data.get('photo')
        )
        
        # Nota: Em uma implementação real, você armazenaria o hash da senha
        # Por simplicidade, não estamos implementando senhas no modelo atual
        # mas seria necessário adicionar um campo password_hash ao modelo User
        
        db.session.add(user)
        db.session.commit()
        
        # Gerar token
        token = generate_token(user.gid)
        
        return jsonify({
            'user': user.to_dict(),
            'token': token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Login do usuário"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        # Buscar usuário por email
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Nota: Em uma implementação real, você verificaria o hash da senha
        # Por simplicidade, estamos aceitando qualquer senha para usuários existentes
        
        # Gerar token
        token = generate_token(user.gid)
        
        return jsonify({
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """Obter informações do usuário atual"""
    try:
        # Obter token do header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autorização necessário'}), 401
        
        token = auth_header.split(' ')[1]
        user_gid = verify_token(token)
        
        if not user_gid:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        user = User.query.get(user_gid)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user = User.query.get(data['user_gid'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
            g.current_user = current_user
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated

