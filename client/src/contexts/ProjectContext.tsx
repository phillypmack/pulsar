import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Project, Task, projectService, taskService } from '../services/api';

interface ProjectContextType {
  projects: Project[];
  currentProject: Project | null;
  tasks: Task[];
  loading: boolean;
  fetchProjects: (workspaceId?: string) => Promise<void>;
  createProject: (data: Partial<Project>) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  fetchProjectTasks: (projectId: string) => Promise<void>;
  createTask: (data: Partial<Task> & { project_gids?: string[] }) => Promise<void>;
  updateTask: (taskId: string, data: Partial<Task>) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

interface ProjectProviderProps {
  children: ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchProjects = async (workspaceId?: string) => {
    setLoading(true);
    try {
      const projectsData = await projectService.getProjects(workspaceId);
      setProjects(projectsData);
    } catch (error) {
      console.error('Erro ao buscar projetos:', error);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (data: Partial<Project>) => {
    try {
      const newProject = await projectService.createProject(data);
      setProjects(prev => [...prev, newProject]);
    } catch (error) {
      console.error('Erro ao criar projeto:', error);
      throw error;
    }
  };

  const fetchProjectTasks = async (projectId: string) => {
    setLoading(true);
    try {
      const tasksData = await taskService.getProjectTasks(projectId);
      setTasks(tasksData);
    } catch (error) {
      console.error('Erro ao buscar tarefas do projeto:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTask = async (data: Partial<Task> & { project_gids?: string[] }) => {
    try {
      const newTask = await taskService.createTask(data);
      setTasks(prev => [...prev, newTask]);
    } catch (error) {
      console.error('Erro ao criar tarefa:', error);
      throw error;
    }
  };

  const updateTask = async (taskId: string, data: Partial<Task>) => {
    try {
      const updatedTask = await taskService.updateTask(taskId, data);
      setTasks(prev => prev.map(task => 
        task.gid === taskId ? updatedTask : task
      ));
    } catch (error) {
      console.error('Erro ao atualizar tarefa:', error);
      throw error;
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      await taskService.deleteTask(taskId);
      setTasks(prev => prev.filter(task => task.gid !== taskId));
    } catch (error) {
      console.error('Erro ao deletar tarefa:', error);
      throw error;
    }
  };

  const value = {
    projects,
    currentProject,
    tasks,
    loading,
    fetchProjects,
    createProject,
    setCurrentProject,
    fetchProjectTasks,
    createTask,
    updateTask,
    deleteTask,
  };

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
};

