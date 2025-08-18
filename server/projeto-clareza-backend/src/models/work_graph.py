from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

# Workspace model
class Workspace(db.Model):
    __tablename__ = 'workspaces'
    
    gid = db.Column(db.String(255), primary_key=True)
    resource_type = db.Column(db.String(255), nullable=False, default='workspace')
    name = db.Column(db.String(255), nullable=False)
    is_organization = db.Column(db.Boolean, nullable=False, default=False)
    email_domains = db.Column(db.Text)  # JSON array as text
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'is_organization': self.is_organization,
            'email_domains': json.loads(self.email_domains) if self.email_domains else []
        }

# User model (updated)
class User(db.Model):
    __tablename__ = 'users'
    
    gid = db.Column(db.String(255), primary_key=True)
    resource_type = db.Column(db.String(255), nullable=False, default='user')
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    photo = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'email': self.email,
            'photo': self.photo
        }

# Team model
class Team(db.Model):
    __tablename__ = 'teams'
    
    gid = db.Column(db.String(255), primary_key=True)
    resource_type = db.Column(db.String(255), nullable=False, default='team')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    organization_gid = db.Column(db.String(255), db.ForeignKey('workspaces.gid'))
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'description': self.description,
            'organization_gid': self.organization_gid
        }

# Project model
class Project(db.Model):
    __tablename__ = 'projects'
    
    gid = db.Column(db.String(255), primary_key=True)
    resource_type = db.Column(db.String(255), nullable=False, default='project')
    name = db.Column(db.String(255), nullable=False)
    owner_gid = db.Column(db.String(255), db.ForeignKey('users.gid'))
    team_gid = db.Column(db.String(255), db.ForeignKey('teams.gid'), nullable=True)
    workspace_gid = db.Column(db.String(255), db.ForeignKey('workspaces.gid'), nullable=False)
    default_view = db.Column(db.String(255), nullable=False, default='list')
    color = db.Column(db.String(255))
    privacy_setting = db.Column(db.String(255))
    due_on = db.Column(db.Date)
    start_on = db.Column(db.Date)
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'owner_gid': self.owner_gid,
            'team_gid': self.team_gid,
            'workspace_gid': self.workspace_gid,
            'default_view': self.default_view,
            'color': self.color,
            'privacy_setting': self.privacy_setting,
            'due_on': self.due_on.isoformat() if self.due_on else None,
            'start_on': self.start_on.isoformat() if self.start_on else None
        }

# Section model
class Section(db.Model):
    __tablename__ = 'sections'
    
    gid = db.Column(db.String(255), primary_key=True)
    resource_type = db.Column(db.String(255), nullable=False, default='section')
    name = db.Column(db.String(255), nullable=False)
    project_gid = db.Column(db.String(255), db.ForeignKey('projects.gid'))
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'resource_type': self.resource_type,
            'name': self.name,
            'project_gid': self.project_gid
        }

# Task model
class Task(db.Model):
    __tablename__ = 'tasks'
    
    gid = db.Column(db.String(255), primary_key=True)
    resource_type = db.Column(db.String(255), nullable=False, default='task')
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    assignee_gid = db.Column(db.String(255), db.ForeignKey('users.gid'), nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    due_on = db.Column(db.Date, nullable=True)
    start_on = db.Column(db.Date, nullable=True)
    parent_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), nullable=True)
    workspace_gid = db.Column(db.String(255), db.ForeignKey('workspaces.gid'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    resource_subtype = db.Column(db.String(255))
    
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
            'workspace_gid': self.workspace_gid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'resource_subtype': self.resource_subtype
        }

# Portfolio model
class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    gid = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    owner_gid = db.Column(db.String(255), db.ForeignKey('users.gid'))
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'name': self.name,
            'owner_gid': self.owner_gid
        }

# Goal model
class Goal(db.Model):
    __tablename__ = 'goals'
    
    gid = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    owner_gid = db.Column(db.String(255), db.ForeignKey('users.gid'))
    time_period_gid = db.Column(db.String(255))
    metric = db.Column(db.Text)  # JSON as text
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'name': self.name,
            'owner_gid': self.owner_gid,
            'time_period_gid': self.time_period_gid,
            'metric': json.loads(self.metric) if self.metric else None
        }

# Junction tables
class ProjectTask(db.Model):
    __tablename__ = 'project_tasks'
    
    project_gid = db.Column(db.String(255), db.ForeignKey('projects.gid'), primary_key=True)
    task_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), primary_key=True)

class TaskDependency(db.Model):
    __tablename__ = 'task_dependencies'
    
    blocking_task_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), primary_key=True)
    blocked_task_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), primary_key=True)

class TaskFollower(db.Model):
    __tablename__ = 'task_followers'
    
    task_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), primary_key=True)
    user_gid = db.Column(db.String(255), db.ForeignKey('users.gid'), primary_key=True)

class Tag(db.Model):
    __tablename__ = 'tags'
    
    gid = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'name': self.name
        }

class TaskTag(db.Model):
    __tablename__ = 'task_tags'
    
    task_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), primary_key=True)
    tag_gid = db.Column(db.String(255), db.ForeignKey('tags.gid'), primary_key=True)

class PortfolioProject(db.Model):
    __tablename__ = 'portfolio_projects'
    
    portfolio_gid = db.Column(db.String(255), db.ForeignKey('portfolios.gid'), primary_key=True)
    project_gid = db.Column(db.String(255), db.ForeignKey('projects.gid'), primary_key=True)

class GoalRelationship(db.Model):
    __tablename__ = 'goal_relationships'
    
    parent_goal_gid = db.Column(db.String(255), db.ForeignKey('goals.gid'), primary_key=True)
    child_goal_gid = db.Column(db.String(255), db.ForeignKey('goals.gid'), primary_key=True)

# Custom Fields
class CustomField(db.Model):
    __tablename__ = 'custom_fields'
    
    gid = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)  # 'text', 'number', 'enum'
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'name': self.name,
            'type': self.type
        }

class ProjectCustomField(db.Model):
    __tablename__ = 'project_custom_fields'
    
    project_gid = db.Column(db.String(255), db.ForeignKey('projects.gid'), primary_key=True)
    custom_field_gid = db.Column(db.String(255), db.ForeignKey('custom_fields.gid'), primary_key=True)

class TaskCustomFieldValue(db.Model):
    __tablename__ = 'task_custom_field_values'
    
    task_gid = db.Column(db.String(255), db.ForeignKey('tasks.gid'), primary_key=True)
    custom_field_gid = db.Column(db.String(255), db.ForeignKey('custom_fields.gid'), primary_key=True)
    text_value = db.Column(db.Text, nullable=True)
    number_value = db.Column(db.Numeric, nullable=True)
    enum_option_gid = db.Column(db.String(255), nullable=True)

# Rules Engine
class Rule(db.Model):
    __tablename__ = 'rules'
    
    gid = db.Column(db.String(255), primary_key=True)
    project_gid = db.Column(db.String(255), db.ForeignKey('projects.gid'), nullable=False)
    trigger_type = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'gid': self.gid,
            'project_gid': self.project_gid,
            'trigger_type': self.trigger_type,
            'name': self.name
        }

class RuleCondition(db.Model):
    __tablename__ = 'rule_conditions'
    
    gid = db.Column(db.String(255), primary_key=True)
    rule_gid = db.Column(db.String(255), db.ForeignKey('rules.gid'), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    operator = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=False)

class RuleAction(db.Model):
    __tablename__ = 'rule_actions'
    
    gid = db.Column(db.String(255), primary_key=True)
    rule_gid = db.Column(db.String(255), db.ForeignKey('rules.gid'), nullable=False)
    action_type = db.Column(db.String(255), nullable=False)
    parameters = db.Column(db.Text)  # JSON as text

# Audit Log
class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(255), nullable=False)
    entity_gid = db.Column(db.String(255), nullable=False)
    user_gid = db.Column(db.String(255), db.ForeignKey('users.gid'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)  # JSON as text

# Memberships
class ProjectMembership(db.Model):
    __tablename__ = 'project_memberships'
    
    project_gid = db.Column(db.String(255), db.ForeignKey('projects.gid'), primary_key=True)
    user_gid = db.Column(db.String(255), db.ForeignKey('users.gid'), primary_key=True)
    role = db.Column(db.String(255), nullable=False)

class TeamMembership(db.Model):
    __tablename__ = 'team_memberships'
    
    team_gid = db.Column(db.String(255), db.ForeignKey('teams.gid'), primary_key=True)
    user_gid = db.Column(db.String(255), db.ForeignKey('users.gid'), primary_key=True)
    role = db.Column(db.String(255), nullable=False)

class WorkspaceMembership(db.Model):
    __tablename__ = 'workspace_memberships'
    
    workspace_gid = db.Column(db.String(255), db.ForeignKey('workspaces.gid'), primary_key=True)
    user_gid = db.Column(db.String(255), db.ForeignKey('users.gid'), primary_key=True)
    role = db.Column(db.String(255), nullable=False)

