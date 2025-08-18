from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

# Tabela de associação para relacionamento many-to-many entre tarefas e projetos
task_projects = db.Table('task_projects',
    db.Column('task_gid', db.String(36), db.ForeignKey('tasks.gid'), primary_key=True),
    db.Column('project_gid', db.String(36), db.ForeignKey('projects.gid'), primary_key=True)
)

# Tabela de associação para dependências de tarefas
task_dependencies = db.Table('task_dependencies',
    db.Column('dependent_task_gid', db.String(36), db.ForeignKey('tasks.gid'), primary_key=True),
    db.Column('dependency_task_gid', db.String(36), db.ForeignKey('tasks.gid'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='user')
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    photo = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    owned_projects = db.relationship('Project', backref='owner', lazy=True, foreign_keys='Project.owner_gid')
    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True, foreign_keys='Task.assignee_gid')
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'email': self.email,
            'photo': self.photo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='workspace')
    name = db.Column(db.String(255), nullable=False)
    is_organization = db.Column(db.Boolean, default=False)
    email_domains = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    projects = db.relationship('Project', backref='workspace', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='workspace', lazy=True, cascade='all, delete-orphan')
    custom_fields = db.relationship('CustomField', backref='workspace', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'is_organization': self.is_organization,
            'email_domains': json.loads(self.email_domains) if self.email_domains else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'projects'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='project')
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    owner_gid = db.Column(db.String(36), db.ForeignKey('users.gid'))
    team_gid = db.Column(db.String(36))  # Para futuras implementações de teams
    workspace_gid = db.Column(db.String(36), db.ForeignKey('workspaces.gid'), nullable=False)
    default_view = db.Column(db.String(50), default='list')  # list, board, calendar, timeline
    color = db.Column(db.String(7))  # Hex color
    privacy_setting = db.Column(db.String(50))  # public_to_workspace, private_to_team
    due_on = db.Column(db.Date)
    start_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived = db.Column(db.Boolean, default=False)
    
    # Relacionamentos many-to-many com tasks
    tasks = db.relationship('Task', secondary=task_projects, back_populates='projects')
    sections = db.relationship('Section', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'notes': self.notes,
            'owner_gid': self.owner_gid,
            'team_gid': self.team_gid,
            'workspace_gid': self.workspace_gid,
            'default_view': self.default_view,
            'color': self.color,
            'privacy_setting': self.privacy_setting,
            'due_on': self.due_on.isoformat() if self.due_on else None,
            'start_on': self.start_on.isoformat() if self.start_on else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'archived': self.archived
        }

class Section(db.Model):
    __tablename__ = 'sections'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='section')
    name = db.Column(db.String(255), nullable=False)
    project_gid = db.Column(db.String(36), db.ForeignKey('projects.gid'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    tasks = db.relationship('Task', backref='section', lazy=True)
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'project_gid': self.project_gid,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='task')
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    assignee_gid = db.Column(db.String(36), db.ForeignKey('users.gid'))
    completed = db.Column(db.Boolean, default=False)
    due_on = db.Column(db.Date)
    start_on = db.Column(db.Date)
    parent_gid = db.Column(db.String(36), db.ForeignKey('tasks.gid'))  # Para subtarefas
    section_gid = db.Column(db.String(36), db.ForeignKey('sections.gid'))
    workspace_gid = db.Column(db.String(36), db.ForeignKey('workspaces.gid'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    resource_subtype = db.Column(db.String(50))  # default_task, milestone, approval
    
    # Relacionamentos
    projects = db.relationship('Project', secondary=task_projects, back_populates='tasks')
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[gid]))
    custom_field_values = db.relationship('CustomFieldValue', backref='task', lazy=True, cascade='all, delete-orphan')
    
    # Dependências de tarefas
    dependencies = db.relationship(
        'Task',
        secondary=task_dependencies,
        primaryjoin=gid == task_dependencies.c.dependent_task_gid,
        secondaryjoin=gid == task_dependencies.c.dependency_task_gid,
        backref='dependents'
    )
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'notes': self.notes,
            'assignee_gid': self.assignee_gid,
            'completed': self.completed,
            'due_on': self.due_on.isoformat() if self.due_on else None,
            'start_on': self.start_on.isoformat() if self.start_on else None,
            'parent_gid': self.parent_gid,
            'section_gid': self.section_gid,
            'workspace_gid': self.workspace_gid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'resource_subtype': self.resource_subtype,
            'project_gids': [project.gid for project in self.projects],
            'dependency_gids': [dep.gid for dep in self.dependencies],
            'dependent_gids': [dep.gid for dep in self.dependents]
        }

class CustomField(db.Model):
    __tablename__ = 'custom_fields'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='custom_field')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)  # text, number, enum, multi_enum, date
    workspace_gid = db.Column(db.String(36), db.ForeignKey('workspaces.gid'), nullable=False)
    enum_options = db.Column(db.Text)  # JSON string para opções de enum
    number_value_min = db.Column(db.Float)
    number_value_max = db.Column(db.Float)
    precision = db.Column(db.Integer)  # Para campos numéricos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    values = db.relationship('CustomFieldValue', backref='custom_field', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'workspace_gid': self.workspace_gid,
            'enum_options': json.loads(self.enum_options) if self.enum_options else None,
            'number_value_min': self.number_value_min,
            'number_value_max': self.number_value_max,
            'precision': self.precision,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CustomFieldValue(db.Model):
    __tablename__ = 'custom_field_values'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='custom_field_value')
    custom_field_gid = db.Column(db.String(36), db.ForeignKey('custom_fields.gid'), nullable=False)
    task_gid = db.Column(db.String(36), db.ForeignKey('tasks.gid'), nullable=False)
    text_value = db.Column(db.Text)
    number_value = db.Column(db.Float)
    enum_value = db.Column(db.String(255))
    multi_enum_values = db.Column(db.Text)  # JSON string
    date_value = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'custom_field_gid': self.custom_field_gid,
            'task_gid': self.task_gid,
            'text_value': self.text_value,
            'number_value': self.number_value,
            'enum_value': self.enum_value,
            'multi_enum_values': json.loads(self.multi_enum_values) if self.multi_enum_values else None,
            'date_value': self.date_value.isoformat() if self.date_value else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None
        }

class AutomationRule(db.Model):
    __tablename__ = 'automation_rules'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='automation_rule')
    name = db.Column(db.String(255), nullable=False)
    project_gid = db.Column(db.String(36), db.ForeignKey('projects.gid'), nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)  # task_completed, task_created, field_changed, etc.
    trigger_conditions = db.Column(db.Text)  # JSON string
    action_type = db.Column(db.String(50), nullable=False)  # move_to_section, assign_task, add_comment, etc.
    action_parameters = db.Column(db.Text)  # JSON string
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'project_gid': self.project_gid,
            'trigger_type': self.trigger_type,
            'trigger_conditions': json.loads(self.trigger_conditions) if self.trigger_conditions else {},
            'action_type': self.action_type,
            'action_parameters': json.loads(self.action_parameters) if self.action_parameters else {},
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ActivityFeed(db.Model):
    __tablename__ = 'activity_feed'
    
    gid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = db.Column(db.String(50), default='activity')
    event_type = db.Column(db.String(50), nullable=False)  # task_created, task_completed, etc.
    actor_gid = db.Column(db.String(36), db.ForeignKey('users.gid'))
    target_gid = db.Column(db.String(36))  # ID do objeto afetado (task, project, etc.)
    target_type = db.Column(db.String(50))  # task, project, etc.
    project_gid = db.Column(db.String(36), db.ForeignKey('projects.gid'))
    workspace_gid = db.Column(db.String(36), db.ForeignKey('workspaces.gid'), nullable=False)
    data = db.Column(db.Text)  # JSON string com dados adicionais
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    actor = db.relationship('User', backref='activities')
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'event_type': self.event_type,
            'actor_gid': self.actor_gid,
            'target_gid': self.target_gid,
            'target_type': self.target_type,
            'project_gid': self.project_gid,
            'workspace_gid': self.workspace_gid,
            'data': json.loads(self.data) if self.data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

