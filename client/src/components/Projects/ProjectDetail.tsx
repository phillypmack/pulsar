import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '../../contexts/ProjectContext';
import { useAuth } from '../../contexts/AuthContext';
import { Project, projectService } from '../../services/api';
import TaskList from './TaskList';
import CreateTaskModal from './CreateTaskModal';
import './ProjectDetail.css';

const ProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { tasks, fetchProjectTasks, loading } = useProject();
  
  const [project, setProject] = useState<Project | null>(null);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [projectLoading, setProjectLoading] = useState(true);

  const loadProject = useCallback(async () => {
    if (!projectId) return;
    
    setProjectLoading(true);
    try {
      const projectData = await projectService.getProject(projectId);
      setProject(projectData);
    } catch (error) {
      console.error('Erro ao carregar projeto:', error);
      navigate('/dashboard');
    } finally {
      setProjectLoading(false);
    }
  }, [projectId, navigate]);

  useEffect(() => {
    if (projectId) {
      loadProject();
      fetchProjectTasks(projectId);
    }
  }, [projectId, fetchProjectTasks, loadProject]);

  if (projectLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Carregando projeto...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="error-container">
        <h2>Projeto não encontrado</h2>
        <button onClick={() => navigate('/dashboard')}>
          Voltar ao Dashboard
        </button>
      </div>
    );
  }

  const completedTasks = tasks.filter(task => task.completed).length;
  const totalTasks = tasks.length;
  const completionPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return (
    <div className="project-detail">
      <header className="project-header">
        <div className="header-left">
          <button onClick={() => navigate('/dashboard')} className="back-button">
            ← Voltar
          </button>
          <div className="project-info">
            <div className="project-title">
              <div 
                className="project-color-indicator"
                style={{ backgroundColor: project.color || '#667eea' }}
              />
              <h1>{project.name}</h1>
            </div>
            <div className="project-stats">
              <span className="stat">
                {completedTasks} de {totalTasks} tarefas concluídas
              </span>
              <span className="stat">
                {completionPercentage}% completo
              </span>
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <button
            onClick={() => setShowCreateTask(true)}
            className="create-task-button"
          >
            + Nova Tarefa
          </button>
        </div>
      </header>

      <div className="project-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ 
              width: `${completionPercentage}%`,
              backgroundColor: project.color || '#667eea'
            }}
          />
        </div>
      </div>

      <main className="project-main">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner">Carregando tarefas...</div>
          </div>
        ) : (
          <TaskList
            tasks={tasks}
            projectColor={project.color || '#667eea'}
          />
        )}
      </main>

      {showCreateTask && (
        <CreateTaskModal
          projectId={project.gid}
          workspaceId={project.workspace_gid}
          onClose={() => setShowCreateTask(false)}
          onTaskCreated={() => {
            setShowCreateTask(false);
            if (projectId) {
              fetchProjectTasks(projectId);
            }
          }}
        />
      )}
    </div>
  );
};

export default ProjectDetail;

