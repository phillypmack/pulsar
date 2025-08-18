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



