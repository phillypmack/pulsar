import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import GanttChart from './GanttChart';
import { useProject } from '../../contexts/ProjectContext';
import { projectService, taskService, Project } from '../../services/api';
import './TimelineView.css';

interface Task {
  gid: string;
  name: string;
  start_on?: string;
  due_on?: string;
  completed: boolean;
  assignee_gid?: string;
  assignee?: {
    name: string;
    email: string;
  };
  dependencies?: Task[];
  progress?: number;
}

const TimelineView: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { projects } = useProject();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showTaskDetails, setShowTaskDetails] = useState(false);

  const currentProject = projects.find((p: Project) => p.gid === projectId);

  const loadProjectTasks = useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      setError(null);

      // Buscar tarefas do projeto com dependências
      const response = await taskService.getProjectTasks(projectId!, {
        include_dependencies: true,
        include_assignee: true
      } as any); // Using as any to bypass potential type mismatch in options

      const tasksWithDates = response.filter((task: any) => 
        task.start_on || task.due_on
      );

      setTasks(tasksWithDates);
    } catch (err: any) {
      console.error('Erro ao carregar tarefas:', err);
      setError(err.response?.data?.error || 'Erro ao carregar tarefas');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadProjectTasks();
    }
  }, [projectId, loadProjectTasks]);

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
    setShowTaskDetails(true);
  };

  const handleTaskUpdate = async (taskGid: string, updates: Partial<Task>) => {
    try {
      // Atualizar tarefa via API
      await taskService.updateTask(taskGid, updates);
      
      // Atualizar estado local
      setTasks(prevTasks => 
        prevTasks.map(task => 
          task.gid === taskGid ? { ...task, ...updates } : task
        )
      );
    } catch (err: any) {
      console.error('Erro ao atualizar tarefa:', err);
      // Mostrar notificação de erro
    }
  };

  const calculateProjectProgress = () => {
    if (tasks.length === 0) return 0;
    
    const completedTasks = tasks.filter(task => task.completed).length;
    return Math.round((completedTasks / tasks.length) * 100);
  };

  const getProjectStats = () => {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.completed).length;
    const overdueTasks = tasks.filter(task => {
      if (!task.due_on || task.completed) return false;
      return new Date(task.due_on) < new Date();
    }).length;
    
    const tasksWithDependencies = tasks.filter(task => 
      task.dependencies && task.dependencies.length > 0
    ).length;

    return {
      total: totalTasks,
      completed: completedTasks,
      pending: totalTasks - completedTasks,
      overdue: overdueTasks,
      withDependencies: tasksWithDependencies
    };
  };

  if (loading) {
    return (
      <div className="timeline-view loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Carregando timeline do projeto...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="timeline-view error">
        <div className="error-message">
          <h3>Erro ao carregar timeline</h3>
          <p>{error}</p>
          <button onClick={loadProjectTasks} className="retry-button">
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="timeline-view empty">
        <div className="empty-state">
          <h3>Nenhuma tarefa com datas encontrada</h3>
          <p>Para visualizar o timeline, adicione datas de início e/ou vencimento às tarefas do projeto.</p>
          <button 
            onClick={() => window.history.back()} 
            className="back-button"
          >
            Voltar ao projeto
          </button>
        </div>
      </div>
    );
  }

  const stats = getProjectStats();
  const progress = calculateProjectProgress();

  return (
    <div className="timeline-view">
      {/* Cabeçalho */}
      <div className="timeline-header">
        <div className="timeline-title">
          <h2>Timeline - {currentProject?.name}</h2>
          <p className="timeline-subtitle">
            Visualização Gantt do projeto com dependências e progresso
          </p>
        </div>

        <div className="timeline-stats">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.completed}</div>
            <div className="stat-label">Concluídas</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.pending}</div>
            <div className="stat-label">Pendentes</div>
          </div>
          <div className="stat-card overdue">
            <div className="stat-value">{stats.overdue}</div>
            <div className="stat-label">Atrasadas</div>
          </div>
        </div>

        <div className="project-progress">
          <div className="progress-label">
            Progresso do Projeto: {progress}%
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Gráfico Gantt */}
      <div className="timeline-content">
        <GanttChart
          tasks={tasks}
          onTaskClick={handleTaskClick}
          onTaskUpdate={handleTaskUpdate}
          className="project-gantt"
        />
      </div>

      {/* Painel lateral de detalhes da tarefa */}
      {showTaskDetails && selectedTask && (
        <div className="task-details-panel">
          <div className="task-details-overlay" onClick={() => setShowTaskDetails(false)} />
          <div className="task-details-content">
            <div className="task-details-header">
              <h3>{selectedTask.name}</h3>
              <button 
                className="close-button"
                onClick={() => setShowTaskDetails(false)}
              >
                ×
              </button>
            </div>

            <div className="task-details-body">
              <div className="detail-section">
                <label>Status</label>
                <div className={`status-badge ${selectedTask.completed ? 'completed' : 'pending'}`}>
                  {selectedTask.completed ? 'Concluída' : 'Pendente'}
                </div>
              </div>

              {selectedTask.assignee && (
                <div className="detail-section">
                  <label>Responsável</label>
                  <div className="assignee-info">
                    <div className="assignee-name">{selectedTask.assignee.name}</div>
                    <div className="assignee-email">{selectedTask.assignee.email}</div>
                  </div>
                </div>
              )}

              <div className="detail-section">
                <label>Datas</label>
                <div className="date-info">
                  {selectedTask.start_on && (
                    <div>Início: {new Date(selectedTask.start_on).toLocaleDateString('pt-BR')}</div>
                  )}
                  {selectedTask.due_on && (
                    <div>Vencimento: {new Date(selectedTask.due_on).toLocaleDateString('pt-BR')}</div>
                  )}
                </div>
              </div>

              {selectedTask.dependencies && selectedTask.dependencies.length > 0 && (
                <div className="detail-section">
                  <label>Dependências ({selectedTask.dependencies.length})</label>
                  <div className="dependencies-list">
                    {selectedTask.dependencies.map(dep => (
                      <div key={dep.gid} className="dependency-item">
                        <div className={`dependency-status ${dep.completed ? 'completed' : 'pending'}`}>
                          {dep.completed ? '✓' : '○'}
                        </div>
                        <div className="dependency-name">{dep.name}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="detail-section">
                <label>Progresso</label>
                <div className="task-progress-detail">
                  <div className="progress-bar small">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${selectedTask.progress || 0}%` }}
                    />
                  </div>
                  <span className="progress-text">{selectedTask.progress || 0}%</span>
                </div>
              </div>
            </div>

            <div className="task-details-footer">
              <button 
                className="edit-task-button"
                onClick={() => {
                  // Navegar para edição da tarefa
                  window.location.href = `/projects/${projectId}/tasks/${selectedTask.gid}`;
                }}
              >
                Editar Tarefa
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TimelineView;

