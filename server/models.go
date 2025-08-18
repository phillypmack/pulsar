package main

import (
	"database/sql"
	"time"

	"github.com/lib/pq"
)

// Workspace representa a tabela workspaces
type Workspace struct {
	Gid          string         `gorm:"primaryKey" json:"gid"`
	ResourceType string         `gorm:"default:\'workspace\'" json:"resource_type"`
	Name         string         `json:"name"`
	IsOrganization bool         `gorm:"default:false" json:"is_organization"`
	EmailDomains pq.StringArray `gorm:"type:text[]" json:"email_domains"`
}

// User representa a tabela users
type User struct {
	Gid          string `gorm:"primaryKey" json:"gid"`
	ResourceType string `gorm:"default:

-- Tabela workspaces
CREATE TABLE workspaces (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'workspace',
    name VARCHAR(255) NOT NULL,
    is_organization BOOLEAN NOT NULL DEFAULT FALSE,
    email_domains TEXT[]
);

-- Tabela users
CREATE TABLE users (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'user',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    photo VARCHAR(255)
);

-- Tabela teams
CREATE TABLE teams (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'team',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_gid VARCHAR(255) REFERENCES workspaces(gid)
);

-- Tabela projects
CREATE TABLE projects (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'project',
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    team_gid VARCHAR(255) REFERENCES teams(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    default_view VARCHAR(255) NOT NULL DEFAULT 'list',
    color VARCHAR(255),
    privacy_setting VARCHAR(255),
    due_on DATE,
    start_on DATE
);

-- Tabela sections
CREATE TABLE sections (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'section',
    name VARCHAR(255) NOT NULL,
    project_gid VARCHAR(255) REFERENCES projects(gid)
);

-- Tabela tasks
CREATE TABLE tasks (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'task',
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    assignee_gid VARCHAR(255) REFERENCES users(gid) NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_on DATE NULL,
    start_on DATE NULL,
    parent_gid VARCHAR(255) REFERENCES tasks(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    resource_subtype VARCHAR(255)
);

-- Tabela portfolios
CREATE TABLE portfolios (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid)
);

-- Tabela goals
CREATE TABLE goals (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    time_period_gid VARCHAR(255),
    metric JSONB
);

-- Tabela de junção project_tasks (multi-homing)
CREATE TABLE project_tasks (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (project_gid, task_gid)
);

-- Tabela de junção task_dependencies
CREATE TABLE task_dependencies (
    blocking_task_gid VARCHAR(255) REFERENCES tasks(gid),
    blocked_task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (blocking_task_gid, blocked_task_gid)
);

-- Tabela de junção task_followers
CREATE TABLE task_followers (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    PRIMARY KEY (task_gid, user_gid)
);

-- Tabela de junção task_tags (assumindo que tags terão uma tabela própria)
CREATE TABLE tags (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    tag_gid VARCHAR(255) REFERENCES tags(gid),
    PRIMARY KEY (task_gid, tag_gid)
);

-- Tabela de junção portfolio_projects
CREATE TABLE portfolio_projects (
    portfolio_gid VARCHAR(255) REFERENCES portfolios(gid),
    project_gid VARCHAR(255) REFERENCES projects(gid),
    PRIMARY KEY (portfolio_gid, project_gid)
);

-- Tabela de junção goal_relationships (para metas hierárquicas)
CREATE TABLE goal_relationships (
    parent_goal_gid VARCHAR(255) REFERENCES goals(gid),
    child_goal_gid VARCHAR(255) REFERENCES goals(gid),
    PRIMARY KEY (parent_goal_gid, child_goal_gid)
);

-- Tabela custom_fields
CREATE TABLE custom_fields (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL -- e.g., 'text', 'number', 'enum'
);

-- Tabela project_custom_fields
CREATE TABLE project_custom_fields (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    PRIMARY KEY (project_gid, custom_field_gid)
);

-- Tabela task_custom_field_values
CREATE TABLE task_custom_field_values (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    text_value TEXT NULL,
    number_value NUMERIC NULL,
    enum_option_gid VARCHAR(255) NULL, -- Referência a uma tabela de opções de enum, se necessário
    PRIMARY KEY (task_gid, custom_field_gid)
);

-- Tabela rules
CREATE TABLE rules (
    gid VARCHAR(255) PRIMARY KEY,
    project_gid VARCHAR(255) REFERENCES projects(gid) NOT NULL,
    trigger_type VARCHAR(255) NOT NULL, -- e.g., 'task.created', 'task.custom_field.changed'
    name VARCHAR(255)
);

-- Tabela rule_conditions
CREATE TABLE rule_conditions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    field VARCHAR(255) NOT NULL,
    operator VARCHAR(255) NOT NULL, -- e.g., '=', '>', '<'
    value TEXT NOT NULL
);

-- Tabela rule_actions
CREATE TABLE rule_actions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    action_type VARCHAR(255) NOT NULL, -- e.g., 'update_task', 'add_comment'
    parameters JSONB -- JSON para parâmetros específicos da ação
);

-- Tabela audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_gid VARCHAR(255) NOT NULL,
    user_gid VARCHAR(255) REFERENCES users(gid) NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Tabela project_memberships
CREATE TABLE project_memberships (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'owner', 'editor', 'commenter', 'viewer'
    PRIMARY KEY (project_gid, user_gid)
);

-- Tabela team_memberships
CREATE TABLE team_memberships (
    team_gid VARCHAR(255) REFERENCES teams(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (team_gid, user_gid)
);

-- Tabela workspace_memberships (para administradores de workspace)
CREATE TABLE workspace_memberships (
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (workspace_gid, user_gid)
);

'" json:"resource_type"`
	Name         string `json:"name"`
	Email        string `gorm:"unique" json:"email"`
	Photo        string `json:"photo"`
}

// Team representa a tabela teams
type Team struct {
	Gid           string `gorm:"primaryKey" json:"gid"`
	ResourceType  string `gorm:"default:

-- Tabela workspaces
CREATE TABLE workspaces (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'workspace',
    name VARCHAR(255) NOT NULL,
    is_organization BOOLEAN NOT NULL DEFAULT FALSE,
    email_domains TEXT[]
);

-- Tabela users
CREATE TABLE users (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'user',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    photo VARCHAR(255)
);

-- Tabela teams
CREATE TABLE teams (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'team',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_gid VARCHAR(255) REFERENCES workspaces(gid)
);

-- Tabela projects
CREATE TABLE projects (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'project',
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    team_gid VARCHAR(255) REFERENCES teams(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    default_view VARCHAR(255) NOT NULL DEFAULT 'list',
    color VARCHAR(255),
    privacy_setting VARCHAR(255),
    due_on DATE,
    start_on DATE
);

-- Tabela sections
CREATE TABLE sections (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'section',
    name VARCHAR(255) NOT NULL,
    project_gid VARCHAR(255) REFERENCES projects(gid)
);

-- Tabela tasks
CREATE TABLE tasks (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'task',
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    assignee_gid VARCHAR(255) REFERENCES users(gid) NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_on DATE NULL,
    start_on DATE NULL,
    parent_gid VARCHAR(255) REFERENCES tasks(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    resource_subtype VARCHAR(255)
);

-- Tabela portfolios
CREATE TABLE portfolios (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid)
);

-- Tabela goals
CREATE TABLE goals (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    time_period_gid VARCHAR(255),
    metric JSONB
);

-- Tabela de junção project_tasks (multi-homing)
CREATE TABLE project_tasks (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (project_gid, task_gid)
);

-- Tabela de junção task_dependencies
CREATE TABLE task_dependencies (
    blocking_task_gid VARCHAR(255) REFERENCES tasks(gid),
    blocked_task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (blocking_task_gid, blocked_task_gid)
);

-- Tabela de junção task_followers
CREATE TABLE task_followers (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    PRIMARY KEY (task_gid, user_gid)
);

-- Tabela de junção task_tags (assumindo que tags terão uma tabela própria)
CREATE TABLE tags (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    tag_gid VARCHAR(255) REFERENCES tags(gid),
    PRIMARY KEY (task_gid, tag_gid)
);

-- Tabela de junção portfolio_projects
CREATE TABLE portfolio_projects (
    portfolio_gid VARCHAR(255) REFERENCES portfolios(gid),
    project_gid VARCHAR(255) REFERENCES projects(gid),
    PRIMARY KEY (portfolio_gid, project_gid)
);

-- Tabela de junção goal_relationships (para metas hierárquicas)
CREATE TABLE goal_relationships (
    parent_goal_gid VARCHAR(255) REFERENCES goals(gid),
    child_goal_gid VARCHAR(255) REFERENCES goals(gid),
    PRIMARY KEY (parent_goal_gid, child_goal_gid)
);

-- Tabela custom_fields
CREATE TABLE custom_fields (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL -- e.g., 'text', 'number', 'enum'
);

-- Tabela project_custom_fields
CREATE TABLE project_custom_fields (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    PRIMARY KEY (project_gid, custom_field_gid)
);

-- Tabela task_custom_field_values
CREATE TABLE task_custom_field_values (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    text_value TEXT NULL,
    number_value NUMERIC NULL,
    enum_option_gid VARCHAR(255) NULL, -- Referência a uma tabela de opções de enum, se necessário
    PRIMARY KEY (task_gid, custom_field_gid)
);

-- Tabela rules
CREATE TABLE rules (
    gid VARCHAR(255) PRIMARY KEY,
    project_gid VARCHAR(255) REFERENCES projects(gid) NOT NULL,
    trigger_type VARCHAR(255) NOT NULL, -- e.g., 'task.created', 'task.custom_field.changed'
    name VARCHAR(255)
);

-- Tabela rule_conditions
CREATE TABLE rule_conditions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    field VARCHAR(255) NOT NULL,
    operator VARCHAR(255) NOT NULL, -- e.g., '=', '>', '<'
    value TEXT NOT NULL
);

-- Tabela rule_actions
CREATE TABLE rule_actions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    action_type VARCHAR(255) NOT NULL, -- e.g., 'update_task', 'add_comment'
    parameters JSONB -- JSON para parâmetros específicos da ação
);

-- Tabela audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_gid VARCHAR(255) NOT NULL,
    user_gid VARCHAR(255) REFERENCES users(gid) NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Tabela project_memberships
CREATE TABLE project_memberships (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'owner', 'editor', 'commenter', 'viewer'
    PRIMARY KEY (project_gid, user_gid)
);

-- Tabela team_memberships
CREATE TABLE team_memberships (
    team_gid VARCHAR(255) REFERENCES teams(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (team_gid, user_gid)
);

-- Tabela workspace_memberships (para administradores de workspace)
CREATE TABLE workspace_memberships (
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (workspace_gid, user_gid)
);

'" json:"resource_type"`
	Name          string `json:"name"`
	Description   string `json:"description"`
	OrganizationGid string `gorm:"foreignKey:OrganizationGid" json:"organization_gid"`
}

// Project representa a tabela projects
type Project struct {
	Gid          string         `gorm:"primaryKey" json:"gid"`
	ResourceType string         `gorm:"default:

-- Tabela workspaces
CREATE TABLE workspaces (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'workspace',
    name VARCHAR(255) NOT NULL,
    is_organization BOOLEAN NOT NULL DEFAULT FALSE,
    email_domains TEXT[]
);

-- Tabela users
CREATE TABLE users (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'user',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    photo VARCHAR(255)
);

-- Tabela teams
CREATE TABLE teams (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'team',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_gid VARCHAR(255) REFERENCES workspaces(gid)
);

-- Tabela projects
CREATE TABLE projects (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'project',
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    team_gid VARCHAR(255) REFERENCES teams(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    default_view VARCHAR(255) NOT NULL DEFAULT 'list',
    color VARCHAR(255),
    privacy_setting VARCHAR(255),
    due_on DATE,
    start_on DATE
);

-- Tabela sections
CREATE TABLE sections (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'section',
    name VARCHAR(255) NOT NULL,
    project_gid VARCHAR(255) REFERENCES projects(gid)
);

-- Tabela tasks
CREATE TABLE tasks (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'task',
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    assignee_gid VARCHAR(255) REFERENCES users(gid) NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_on DATE NULL,
    start_on DATE NULL,
    parent_gid VARCHAR(255) REFERENCES tasks(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    resource_subtype VARCHAR(255)
);

-- Tabela portfolios
CREATE TABLE portfolios (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid)
);

-- Tabela goals
CREATE TABLE goals (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    time_period_gid VARCHAR(255),
    metric JSONB
);

-- Tabela de junção project_tasks (multi-homing)
CREATE TABLE project_tasks (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (project_gid, task_gid)
);

-- Tabela de junção task_dependencies
CREATE TABLE task_dependencies (
    blocking_task_gid VARCHAR(255) REFERENCES tasks(gid),
    blocked_task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (blocking_task_gid, blocked_task_gid)
);

-- Tabela de junção task_followers
CREATE TABLE task_followers (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    PRIMARY KEY (task_gid, user_gid)
);

-- Tabela de junção task_tags (assumindo que tags terão uma tabela própria)
CREATE TABLE tags (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    tag_gid VARCHAR(255) REFERENCES tags(gid),
    PRIMARY KEY (task_gid, tag_gid)
);

-- Tabela de junção portfolio_projects
CREATE TABLE portfolio_projects (
    portfolio_gid VARCHAR(255) REFERENCES portfolios(gid),
    project_gid VARCHAR(255) REFERENCES projects(gid),
    PRIMARY KEY (portfolio_gid, project_gid)
);

-- Tabela de junção goal_relationships (para metas hierárquicas)
CREATE TABLE goal_relationships (
    parent_goal_gid VARCHAR(255) REFERENCES goals(gid),
    child_goal_gid VARCHAR(255) REFERENCES goals(gid),
    PRIMARY KEY (parent_goal_gid, child_goal_gid)
);

-- Tabela custom_fields
CREATE TABLE custom_fields (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL -- e.g., 'text', 'number', 'enum'
);

-- Tabela project_custom_fields
CREATE TABLE project_custom_fields (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    PRIMARY KEY (project_gid, custom_field_gid)
);

-- Tabela task_custom_field_values
CREATE TABLE task_custom_field_values (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    text_value TEXT NULL,
    number_value NUMERIC NULL,
    enum_option_gid VARCHAR(255) NULL, -- Referência a uma tabela de opções de enum, se necessário
    PRIMARY KEY (task_gid, custom_field_gid)
);

-- Tabela rules
CREATE TABLE rules (
    gid VARCHAR(255) PRIMARY KEY,
    project_gid VARCHAR(255) REFERENCES projects(gid) NOT NULL,
    trigger_type VARCHAR(255) NOT NULL, -- e.g., 'task.created', 'task.custom_field.changed'
    name VARCHAR(255)
);

-- Tabela rule_conditions
CREATE TABLE rule_conditions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    field VARCHAR(255) NOT NULL,
    operator VARCHAR(255) NOT NULL, -- e.g., '=', '>', '<'
    value TEXT NOT NULL
);

-- Tabela rule_actions
CREATE TABLE rule_actions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    action_type VARCHAR(255) NOT NULL, -- e.g., 'update_task', 'add_comment'
    parameters JSONB -- JSON para parâmetros específicos da ação
);

-- Tabela audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_gid VARCHAR(255) NOT NULL,
    user_gid VARCHAR(255) REFERENCES users(gid) NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Tabela project_memberships
CREATE TABLE project_memberships (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'owner', 'editor', 'commenter', 'viewer'
    PRIMARY KEY (project_gid, user_gid)
);

-- Tabela team_memberships
CREATE TABLE team_memberships (
    team_gid VARCHAR(255) REFERENCES teams(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (team_gid, user_gid)
);

-- Tabela workspace_memberships (para administradores de workspace)
CREATE TABLE workspace_memberships (
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (workspace_gid, user_gid)
);

'" json:"resource_type"`
	Name         string    `json:"name"`
	OwnerGid     string    `gorm:"foreignKey:OwnerGid" json:"owner_gid"`
	TeamGid      sql.NullString `gorm:"foreignKey:TeamGid" json:"team_gid"`
	WorkspaceGid string    `gorm:"foreignKey:WorkspaceGid" json:"workspace_gid"`
	DefaultView  string    `gorm:"default:

-- Tabela workspaces
CREATE TABLE workspaces (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'workspace',
    name VARCHAR(255) NOT NULL,
    is_organization BOOLEAN NOT NULL DEFAULT FALSE,
    email_domains TEXT[]
);

-- Tabela users
CREATE TABLE users (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'user',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    photo VARCHAR(255)
);

-- Tabela teams
CREATE TABLE teams (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'team',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_gid VARCHAR(255) REFERENCES workspaces(gid)
);

-- Tabela projects
CREATE TABLE projects (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'project',
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    team_gid VARCHAR(255) REFERENCES teams(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    default_view VARCHAR(255) NOT NULL DEFAULT 'list',
    color VARCHAR(255),
    privacy_setting VARCHAR(255),
    due_on DATE,
    start_on DATE
);

-- Tabela sections
CREATE TABLE sections (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'section',
    name VARCHAR(255) NOT NULL,
    project_gid VARCHAR(255) REFERENCES projects(gid)
);

-- Tabela tasks
CREATE TABLE tasks (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'task',
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    assignee_gid VARCHAR(255) REFERENCES users(gid) NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_on DATE NULL,
    start_on DATE NULL,
    parent_gid VARCHAR(255) REFERENCES tasks(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    resource_subtype VARCHAR(255)
);

-- Tabela portfolios
CREATE TABLE portfolios (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid)
);

-- Tabela goals
CREATE TABLE goals (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    time_period_gid VARCHAR(255),
    metric JSONB
);

-- Tabela de junção project_tasks (multi-homing)
CREATE TABLE project_tasks (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (project_gid, task_gid)
);

-- Tabela de junção task_dependencies
CREATE TABLE task_dependencies (
    blocking_task_gid VARCHAR(255) REFERENCES tasks(gid),
    blocked_task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (blocking_task_gid, blocked_task_gid)
);

-- Tabela de junção task_followers
CREATE TABLE task_followers (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    PRIMARY KEY (task_gid, user_gid)
);

-- Tabela de junção task_tags (assumindo que tags terão uma tabela própria)
CREATE TABLE tags (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    tag_gid VARCHAR(255) REFERENCES tags(gid),
    PRIMARY KEY (task_gid, tag_gid)
);

-- Tabela de junção portfolio_projects
CREATE TABLE portfolio_projects (
    portfolio_gid VARCHAR(255) REFERENCES portfolios(gid),
    project_gid VARCHAR(255) REFERENCES projects(gid),
    PRIMARY KEY (portfolio_gid, project_gid)
);

-- Tabela de junção goal_relationships (para metas hierárquicas)
CREATE TABLE goal_relationships (
    parent_goal_gid VARCHAR(255) REFERENCES goals(gid),
    child_goal_gid VARCHAR(255) REFERENCES goals(gid),
    PRIMARY KEY (parent_goal_gid, child_goal_gid)
);

-- Tabela custom_fields
CREATE TABLE custom_fields (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL -- e.g., 'text', 'number', 'enum'
);

-- Tabela project_custom_fields
CREATE TABLE project_custom_fields (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    PRIMARY KEY (project_gid, custom_field_gid)
);

-- Tabela task_custom_field_values
CREATE TABLE task_custom_field_values (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    text_value TEXT NULL,
    number_value NUMERIC NULL,
    enum_option_gid VARCHAR(255) NULL, -- Referência a uma tabela de opções de enum, se necessário
    PRIMARY KEY (task_gid, custom_field_gid)
);

-- Tabela rules
CREATE TABLE rules (
    gid VARCHAR(255) PRIMARY KEY,
    project_gid VARCHAR(255) REFERENCES projects(gid) NOT NULL,
    trigger_type VARCHAR(255) NOT NULL, -- e.g., 'task.created', 'task.custom_field.changed'
    name VARCHAR(255)
);

-- Tabela rule_conditions
CREATE TABLE rule_conditions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    field VARCHAR(255) NOT NULL,
    operator VARCHAR(255) NOT NULL, -- e.g., '=', '>', '<'
    value TEXT NOT NULL
);

-- Tabela rule_actions
CREATE TABLE rule_actions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    action_type VARCHAR(255) NOT NULL, -- e.g., 'update_task', 'add_comment'
    parameters JSONB -- JSON para parâmetros específicos da ação
);

-- Tabela audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_gid VARCHAR(255) NOT NULL,
    user_gid VARCHAR(255) REFERENCES users(gid) NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Tabela project_memberships
CREATE TABLE project_memberships (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'owner', 'editor', 'commenter', 'viewer'
    PRIMARY KEY (project_gid, user_gid)
);

-- Tabela team_memberships
CREATE TABLE team_memberships (
    team_gid VARCHAR(255) REFERENCES teams(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (team_gid, user_gid)
);

-- Tabela workspace_memberships (para administradores de workspace)
CREATE TABLE workspace_memberships (
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (workspace_gid, user_gid)
);

'list\'" json:"default_view"`
	Color        string    `json:"color"`
	PrivacySetting string    `json:"privacy_setting"`
	DueOn        sql.NullTime `json:"due_on"`
	StartOn      sql.NullTime `json:"start_on"`
}

// Section representa a tabela sections
type Section struct {
	Gid         string `gorm:"primaryKey" json:"gid"`
	ResourceType string `gorm:"default:

-- Tabela workspaces
CREATE TABLE workspaces (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'workspace',
    name VARCHAR(255) NOT NULL,
    is_organization BOOLEAN NOT NULL DEFAULT FALSE,
    email_domains TEXT[]
);

-- Tabela users
CREATE TABLE users (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'user',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    photo VARCHAR(255)
);

-- Tabela teams
CREATE TABLE teams (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'team',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_gid VARCHAR(255) REFERENCES workspaces(gid)
);

-- Tabela projects
CREATE TABLE projects (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'project',
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    team_gid VARCHAR(255) REFERENCES teams(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    default_view VARCHAR(255) NOT NULL DEFAULT 'list',
    color VARCHAR(255),
    privacy_setting VARCHAR(255),
    due_on DATE,
    start_on DATE
);

-- Tabela sections
CREATE TABLE sections (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'section',
    name VARCHAR(255) NOT NULL,
    project_gid VARCHAR(255) REFERENCES projects(gid)
);

-- Tabela tasks
CREATE TABLE tasks (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'task',
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    assignee_gid VARCHAR(255) REFERENCES users(gid) NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_on DATE NULL,
    start_on DATE NULL,
    parent_gid VARCHAR(255) REFERENCES tasks(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    resource_subtype VARCHAR(255)
);

-- Tabela portfolios
CREATE TABLE portfolios (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid)
);

-- Tabela goals
CREATE TABLE goals (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    time_period_gid VARCHAR(255),
    metric JSONB
);

-- Tabela de junção project_tasks (multi-homing)
CREATE TABLE project_tasks (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (project_gid, task_gid)
);

-- Tabela de junção task_dependencies
CREATE TABLE task_dependencies (
    blocking_task_gid VARCHAR(255) REFERENCES tasks(gid),
    blocked_task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (blocking_task_gid, blocked_task_gid)
);

-- Tabela de junção task_followers
CREATE TABLE task_followers (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    PRIMARY KEY (task_gid, user_gid)
);

-- Tabela de junção task_tags (assumindo que tags terão uma tabela própria)
CREATE TABLE tags (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    tag_gid VARCHAR(255) REFERENCES tags(gid),
    PRIMARY KEY (task_gid, tag_gid)
);

-- Tabela de junção portfolio_projects
CREATE TABLE portfolio_projects (
    portfolio_gid VARCHAR(255) REFERENCES portfolios(gid),
    project_gid VARCHAR(255) REFERENCES projects(gid),
    PRIMARY KEY (portfolio_gid, project_gid)
);

-- Tabela de junção goal_relationships (para metas hierárquicas)
CREATE TABLE goal_relationships (
    parent_goal_gid VARCHAR(255) REFERENCES goals(gid),
    child_goal_gid VARCHAR(255) REFERENCES goals(gid),
    PRIMARY KEY (parent_goal_gid, child_goal_gid)
);

-- Tabela custom_fields
CREATE TABLE custom_fields (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL -- e.g., 'text', 'number', 'enum'
);

-- Tabela project_custom_fields
CREATE TABLE project_custom_fields (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    PRIMARY KEY (project_gid, custom_field_gid)
);

-- Tabela task_custom_field_values
CREATE TABLE task_custom_field_values (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    text_value TEXT NULL,
    number_value NUMERIC NULL,
    enum_option_gid VARCHAR(255) NULL, -- Referência a uma tabela de opções de enum, se necessário
    PRIMARY KEY (task_gid, custom_field_gid)
);

-- Tabela rules
CREATE TABLE rules (
    gid VARCHAR(255) PRIMARY KEY,
    project_gid VARCHAR(255) REFERENCES projects(gid) NOT NULL,
    trigger_type VARCHAR(255) NOT NULL, -- e.g., 'task.created', 'task.custom_field.changed'
    name VARCHAR(255)
);

-- Tabela rule_conditions
CREATE TABLE rule_conditions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    field VARCHAR(255) NOT NULL,
    operator VARCHAR(255) NOT NULL, -- e.g., '=', '>', '<'
    value TEXT NOT NULL
);

-- Tabela rule_actions
CREATE TABLE rule_actions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    action_type VARCHAR(255) NOT NULL, -- e.g., 'update_task', 'add_comment'
    parameters JSONB -- JSON para parâmetros específicos da ação
);

-- Tabela audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_gid VARCHAR(255) NOT NULL,
    user_gid VARCHAR(255) REFERENCES users(gid) NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Tabela project_memberships
CREATE TABLE project_memberships (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'owner', 'editor', 'commenter', 'viewer'
    PRIMARY KEY (project_gid, user_gid)
);

-- Tabela team_memberships
CREATE TABLE team_memberships (
    team_gid VARCHAR(255) REFERENCES teams(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (team_gid, user_gid)
);

-- Tabela workspace_memberships (para administradores de workspace)
CREATE TABLE workspace_memberships (
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (workspace_gid, user_gid)
);

'section\'" json:"resource_type"`
	Name      string `json:"name"`
	ProjectGid string `gorm:"foreignKey:ProjectGid" json:"project_gid"`
}

// Task representa a tabela tasks
type Task struct {
	Gid          string         `gorm:"primaryKey" json:"gid"`
	ResourceType string         `gorm:"default:

-- Tabela workspaces
CREATE TABLE workspaces (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'workspace',
    name VARCHAR(255) NOT NULL,
    is_organization BOOLEAN NOT NULL DEFAULT FALSE,
    email_domains TEXT[]
);

-- Tabela users
CREATE TABLE users (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'user',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    photo VARCHAR(255)
);

-- Tabela teams
CREATE TABLE teams (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'team',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_gid VARCHAR(255) REFERENCES workspaces(gid)
);

-- Tabela projects
CREATE TABLE projects (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'project',
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    team_gid VARCHAR(255) REFERENCES teams(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    default_view VARCHAR(255) NOT NULL DEFAULT 'list',
    color VARCHAR(255),
    privacy_setting VARCHAR(255),
    due_on DATE,
    start_on DATE
);

-- Tabela sections
CREATE TABLE sections (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'section',
    name VARCHAR(255) NOT NULL,
    project_gid VARCHAR(255) REFERENCES projects(gid)
);

-- Tabela tasks
CREATE TABLE tasks (
    gid VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(255) NOT NULL DEFAULT 'task',
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    assignee_gid VARCHAR(255) REFERENCES users(gid) NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_on DATE NULL,
    start_on DATE NULL,
    parent_gid VARCHAR(255) REFERENCES tasks(gid) NULL,
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    resource_subtype VARCHAR(255)
);

-- Tabela portfolios
CREATE TABLE portfolios (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid)
);

-- Tabela goals
CREATE TABLE goals (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_gid VARCHAR(255) REFERENCES users(gid),
    time_period_gid VARCHAR(255),
    metric JSONB
);

-- Tabela de junção project_tasks (multi-homing)
CREATE TABLE project_tasks (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (project_gid, task_gid)
);

-- Tabela de junção task_dependencies
CREATE TABLE task_dependencies (
    blocking_task_gid VARCHAR(255) REFERENCES tasks(gid),
    blocked_task_gid VARCHAR(255) REFERENCES tasks(gid),
    PRIMARY KEY (blocking_task_gid, blocked_task_gid)
);

-- Tabela de junção task_followers
CREATE TABLE task_followers (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    PRIMARY KEY (task_gid, user_gid)
);

-- Tabela de junção task_tags (assumindo que tags terão uma tabela própria)
CREATE TABLE tags (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    tag_gid VARCHAR(255) REFERENCES tags(gid),
    PRIMARY KEY (task_gid, tag_gid)
);

-- Tabela de junção portfolio_projects
CREATE TABLE portfolio_projects (
    portfolio_gid VARCHAR(255) REFERENCES portfolios(gid),
    project_gid VARCHAR(255) REFERENCES projects(gid),
    PRIMARY KEY (portfolio_gid, project_gid)
);

-- Tabela de junção goal_relationships (para metas hierárquicas)
CREATE TABLE goal_relationships (
    parent_goal_gid VARCHAR(255) REFERENCES goals(gid),
    child_goal_gid VARCHAR(255) REFERENCES goals(gid),
    PRIMARY KEY (parent_goal_gid, child_goal_gid)
);

-- Tabela custom_fields
CREATE TABLE custom_fields (
    gid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL -- e.g., 'text', 'number', 'enum'
);

-- Tabela project_custom_fields
CREATE TABLE project_custom_fields (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    PRIMARY KEY (project_gid, custom_field_gid)
);

-- Tabela task_custom_field_values
CREATE TABLE task_custom_field_values (
    task_gid VARCHAR(255) REFERENCES tasks(gid),
    custom_field_gid VARCHAR(255) REFERENCES custom_fields(gid),
    text_value TEXT NULL,
    number_value NUMERIC NULL,
    enum_option_gid VARCHAR(255) NULL, -- Referência a uma tabela de opções de enum, se necessário
    PRIMARY KEY (task_gid, custom_field_gid)
);

-- Tabela rules
CREATE TABLE rules (
    gid VARCHAR(255) PRIMARY KEY,
    project_gid VARCHAR(255) REFERENCES projects(gid) NOT NULL,
    trigger_type VARCHAR(255) NOT NULL, -- e.g., 'task.created', 'task.custom_field.changed'
    name VARCHAR(255)
);

-- Tabela rule_conditions
CREATE TABLE rule_conditions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    field VARCHAR(255) NOT NULL,
    operator VARCHAR(255) NOT NULL, -- e.g., '=', '>', '<'
    value TEXT NOT NULL
);

-- Tabela rule_actions
CREATE TABLE rule_actions (
    gid VARCHAR(255) PRIMARY KEY,
    rule_gid VARCHAR(255) REFERENCES rules(gid) NOT NULL,
    action_type VARCHAR(255) NOT NULL, -- e.g., 'update_task', 'add_comment'
    parameters JSONB -- JSON para parâmetros específicos da ação
);

-- Tabela audit_log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_gid VARCHAR(255) NOT NULL,
    user_gid VARCHAR(255) REFERENCES users(gid) NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Tabela project_memberships
CREATE TABLE project_memberships (
    project_gid VARCHAR(255) REFERENCES projects(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'owner', 'editor', 'commenter', 'viewer'
    PRIMARY KEY (project_gid, user_gid)
);

-- Tabela team_memberships
CREATE TABLE team_memberships (
    team_gid VARCHAR(255) REFERENCES teams(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (team_gid, user_gid)
);

-- Tabela workspace_memberships (para administradores de workspace)
CREATE TABLE workspace_memberships (
    workspace_gid VARCHAR(255) REFERENCES workspaces(gid),
    user_gid VARCHAR(255) REFERENCES users(gid),
    role VARCHAR(255) NOT NULL, -- e.g., 'member', 'admin'
    PRIMARY KEY (workspace_gid, user_gid)
);

'task\'" json:"resource_type"`
	Name         string         `json:"name"`
	Notes        string         `json:"notes"`
	AssigneeGid  sql.NullString `gorm:"foreignKey:AssigneeGid" json:"assignee_gid"`
	Completed    bool           `gorm:"default:false" json:"completed"`
	DueOn        sql.NullTime   `json:"due_on"`
	StartOn      sql.NullTime   `json:"start_on"`
	ParentGid    sql.NullString `gorm:"foreignKey:ParentGid" json:"parent_gid"`
	WorkspaceGid string         `gorm:"foreignKey:WorkspaceGid" json:"workspace_gid"`
	CreatedAt    time.Time      `gorm:"default:CURRENT_TIMESTAMP" json:"created_at"`
	ModifiedAt   time.Time      `gorm:"default:CURRENT_TIMESTAMP" json:"modified_at"`
	CompletedAt  sql.NullTime   `json:"completed_at"`
	ResourceSubtype string      `json:"resource_subtype"`
}

// Portfolio representa a tabela portfolios
type Portfolio struct {
	Gid      string `gorm:"primaryKey" json:"gid"`
	Name     string `json:"name"`
	OwnerGid string `gorm:"foreignKey:OwnerGid" json:"owner_gid"`
}

// Goal representa a tabela goals
type Goal struct {
	Gid         string `gorm:"primaryKey" json:"gid"`
	Name        string `json:"name"`
	OwnerGid    string `gorm:"foreignKey:OwnerGid" json:"owner_gid"`
	TimePeriodGid string `json:"time_period_gid"`
	Metric      []byte `gorm:"type:jsonb" json:"metric"` // Usar []byte para JSONB
}

// ProjectTask representa a tabela de junção project_tasks
type ProjectTask struct {
	ProjectGid string `gorm:"primaryKey" json:"project_gid"`
	TaskGid    string `gorm:"primaryKey" json:"task_gid"`
}

// TaskDependency representa a tabela de junção task_dependencies
type TaskDependency struct {
	BlockingTaskGid string `gorm:"primaryKey" json:"blocking_task_gid"`
	BlockedTaskGid  string `gorm:"primaryKey" json:"blocked_task_gid"`
}

// TaskFollower representa a tabela de junção task_followers
type TaskFollower struct {
	TaskGid string `gorm:"primaryKey" json:"task_gid"`
	UserGid string `gorm:"primaryKey" json:"user_gid"`
}

// Tag representa a tabela tags
type Tag struct {
	Gid  string `gorm:"primaryKey" json:"gid"`
	Name string `gorm:"unique" json:"name"`
}

// TaskTag representa a tabela de junção task_tags
type TaskTag struct {
	TaskGid string `gorm:"primaryKey" json:"task_gid"`
	TagGid  string `gorm:"primaryKey" json:"tag_gid"`
}

// PortfolioProject representa a tabela de junção portfolio_projects
type PortfolioProject struct {
	PortfolioGid string `gorm:"primaryKey" json:"portfolio_gid"`
	ProjectGid   string `gorm:"primaryKey" json:"project_gid"`
}

// GoalRelationship representa a tabela de junção goal_relationships
type GoalRelationship struct {
	ParentGoalGid string `gorm:"primaryKey" json:"parent_goal_gid"`
	ChildGoalGid  string `gorm:"primaryKey" json:"child_goal_gid"`
}

// CustomField representa a tabela custom_fields
type CustomField struct {
	Gid  string `gorm:"primaryKey" json:"gid"`
	Name string `json:"name"`
	Type string `json:"type"`
}

// ProjectCustomField representa a tabela project_custom_fields
type ProjectCustomField struct {
	ProjectGid   string `gorm:"primaryKey" json:"project_gid"`
	CustomFieldGid string `gorm:"primaryKey" json:"custom_field_gid"`
}

// TaskCustomFieldValue representa a tabela task_custom_field_values
type TaskCustomFieldValue struct {
	TaskGid      string         `gorm:"primaryKey" json:"task_gid"`
	CustomFieldGid string         `gorm:"primaryKey" json:"custom_field_gid"`
	TextValue    sql.NullString `json:"text_value"`
	NumberValue  sql.NullFloat64 `json:"number_value"`
	EnumOptionGid sql.NullString `json:"enum_option_gid"`
}

// Rule representa a tabela rules
type Rule struct {
	Gid        string `gorm:"primaryKey" json:"gid"`
	ProjectGid string `gorm:"foreignKey:ProjectGid" json:"project_gid"`
	TriggerType string `json:"trigger_type"`
	Name       string `json:"name"`
}

// RuleCondition representa a tabela rule_conditions
type RuleCondition struct {
	Gid     string `gorm:"primaryKey" json:"gid"`
	RuleGid string `gorm:"foreignKey:RuleGid" json:"rule_gid"`
	Field   string `json:"field"`
	Operator string `json:"operator"`
	Value   string `json:"value"`
}

// RuleAction representa a tabela rule_actions
type RuleAction struct {
	Gid        string `gorm:"primaryKey" json:"gid"`
	RuleGid    string `gorm:"foreignKey:RuleGid" json:"rule_gid"`
	ActionType string `json:"action_type"`
	Parameters []byte `gorm:"type:jsonb" json:"parameters"` // Usar []byte para JSONB
}

// AuditLog representa a tabela audit_log
type AuditLog struct {
	ID        int       `gorm:"primaryKey;autoIncrement" json:"id"`
	EventType string    `json:"event_type"`
	EntityType string    `json:"entity_type"`
	EntityGid string    `json:"entity_gid"`
	UserGid   sql.NullString `gorm:"foreignKey:UserGid" json:"user_gid"`
	Timestamp time.Time `gorm:"default:CURRENT_TIMESTAMP" json:"timestamp"`
	Details   []byte    `gorm:"type:jsonb" json:"details"` // Usar []byte para JSONB
}

// ProjectMembership representa a tabela project_memberships
type ProjectMembership struct {
	ProjectGid string `gorm:"primaryKey" json:"project_gid"`
	UserGid    string `gorm:"primaryKey" json:"user_gid"`
	Role       string `json:"role"`
}

// TeamMembership representa a tabela team_memberships
type TeamMembership struct {
	TeamGid string `gorm:"primaryKey" json:"team_gid"`
	UserGid string `gorm:"primaryKey" json:"user_gid"`
	Role    string `json:"role"`
}

// WorkspaceMembership representa a tabela workspace_memberships
type WorkspaceMembership struct {
	WorkspaceGid string `gorm:"primaryKey" json:"workspace_gid"`
	UserGid      string `gorm:"primaryKey" json:"user_gid"`
	Role         string `json:"role"`
}


