import axios from 'axios';

// Configuração base da API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para lidar com respostas de erro
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado ou inválido
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Tipos de dados
export interface User {
  gid: string;
  resource_type: string;
  name: string;
  email: string;
  photo?: string;
}

export interface Workspace {
  gid: string;
  resource_type: string;
  name: string;
  is_organization: boolean;
  email_domains: string[];
}

export interface Project {
  gid: string;
  resource_type: string;
  name: string;
  owner_gid?: string;
  team_gid?: string;
  workspace_gid: string;
  default_view: string;
  color?: string;
  privacy_setting?: string;
  due_on?: string;
  start_on?: string;
}

export interface Task {
  gid: string;
  resource_type: string;
  name: string;
  notes?: string;
  assignee_gid?: string;
  completed: boolean;
  due_on?: string;
  start_on?: string;
  parent_gid?: string;
  workspace_gid: string;
  created_at?: string;
  modified_at?: string;
  completed_at?: string;
  resource_subtype?: string;
}

// Serviços de autenticação
export const authService = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (name: string, email: string, password: string) => {
    const response = await api.post('/auth/register', { name, email, password });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Serviços de workspaces
export const workspaceService = {
  getWorkspaces: async (): Promise<Workspace[]> => {
    const response = await api.get('/workspaces');
    return response.data;
  },

  createWorkspace: async (data: Partial<Workspace>): Promise<Workspace> => {
    const response = await api.post('/workspaces', data);
    return response.data;
  },

  getWorkspace: async (workspaceId: string): Promise<Workspace> => {
    const response = await api.get(`/workspaces/${workspaceId}`);
    return response.data;
  },
};

// Serviços de projetos
export const projectService = {
  getProjects: async (workspaceId?: string): Promise<Project[]> => {
    const params = workspaceId ? { workspace_gid: workspaceId } : {};
    const response = await api.get('/projects', { params });
    return response.data;
  },

  createProject: async (data: Partial<Project>): Promise<Project> => {
    const response = await api.post('/projects', data);
    return response.data;
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  updateProject: async (projectId: string, data: Partial<Project>): Promise<Project> => {
    const response = await api.put(`/projects/${projectId}`, data);
    return response.data;
  },

  deleteProject: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}`);
  },
};

// Serviços de tarefas
export const taskService = {
  getTasks: async (filters?: {
    workspace_gid?: string;
    project_gid?: string;
    assignee_gid?: string;
    completed?: boolean;
    include_dependencies?: boolean;
    include_assignee?: boolean;
  }): Promise<Task[]> => {
    const response = await api.get('/tasks', { params: filters });
    return response.data;
  },

  getProjectTasks: async (projectId: string, options?: any): Promise<Task[]> => {
    const params = { project_gid: projectId, ...options };
    const response = await api.get(`/tasks`, { params });
    return response.data;
  },

  createTask: async (data: Partial<Task> & { project_gids?: string[] }): Promise<Task> => {
    const response = await api.post('/tasks', data);
    return response.data;
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  updateTask: async (taskId: string, data: Partial<Task>): Promise<Task> => {
    const response = await api.put(`/tasks/${taskId}`, data);
    return response.data;
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await api.delete(`/tasks/${taskId}`);
  },

  addTaskToProject: async (taskId: string, projectId: string): Promise<void> => {
    await api.post(`/tasks/${taskId}/projects`, { project_gid: projectId });
  },

  removeTaskFromProject: async (taskId: string, projectId: string): Promise<void> => {
    await api.delete(`/tasks/${taskId}/projects/${projectId}`);
  },
};

export default api;

