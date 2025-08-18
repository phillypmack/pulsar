import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.config import config
from src.models.enhanced_work_graph import db
from src.celery_app import make_celery
from src.routes.auth import auth_bp
from src.routes.projects import projects_bp
from src.routes.tasks import tasks_bp
from src.routes.workspaces import workspaces_bp
from src.routes.user import user_bp
from src.routes.enhanced_tasks import enhanced_tasks_bp
from src.routes.custom_fields import custom_fields_bp
from src.routes.automation_rules import automation_rules_bp
from src.websocket.events import init_websocket_events
import redis
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuration
    config_name = config_name or os.environ.get('FLASK_CONFIG', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize SocketIO with Redis for scaling
    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        message_queue=app.config['SOCKETIO_REDIS_URL'],
        async_mode='threading'
    )
    
    # Initialize Celery
    celery = make_celery(app)
    app.celery = celery
    
    # Initialize WebSocket events
    init_websocket_events(socketio)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(projects_bp, url_prefix='/api')
    app.register_blueprint(tasks_bp, url_prefix='/api')
    app.register_blueprint(workspaces_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(enhanced_tasks_bp)
    app.register_blueprint(custom_fields_bp)
    app.register_blueprint(automation_rules_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            
            # Check Redis connection
            r = redis.from_url(app.config['REDIS_URL'])
            r.ping()
            
            return {'status': 'healthy', 'services': {'database': 'ok', 'redis': 'ok'}}, 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    # Serve static files (React build)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    
    # Create tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    # Start the application with SocketIO
    socketio.run(
        app,
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5001,
        allow_unsafe_werkzeug=True  # For development only
    )

