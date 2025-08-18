import React from 'react';
import { Task } from '../../services/api';
import { useProject } from '../../contexts/ProjectContext';
import './TaskList.css';

interface TaskListProps {
  tasks: Task[];
  projectColor: string;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, projectColor }) => {
  const { updateTask, deleteTask } = useProject();

  const handleToggleComplete = async (task: Task) => {
    try {
      await updateTask(task.gid, { completed: !task.completed });
    } catch (error) {
      console.error('Erro ao atualizar tarefa:', error);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (window.confirm('Tem certeza que deseja deletar esta tarefa?')) {
      try {
        await deleteTask(taskId);
      } catch (error) {
        console.error('Erro ao deletar tarefa:', error);
      }
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const isOverdue = (dateString?: string) => {
    if (!dateString) return false;
    return new Date(dateString) < new Date();
  };

  if (tasks.length === 0) {
    return (
      <div className="empty-tasks">
        <div className="empty-icon">✅</div>
        <h3>Nenhuma tarefa encontrada</h3>
        <p>Crie sua primeira tarefa para começar a trabalhar neste projeto.</p>
      </div>
    );
  }

  const incompleteTasks = tasks.filter(task => !task.completed);
  const completedTasks = tasks.filter(task => task.completed);

  return (
    <div className="task-list">
      {incompleteTasks.length > 0 && (
        <div className="task-section">
          <h3 className="section-title">
            Tarefas Pendentes ({incompleteTasks.length})
          </h3>
          <div className="tasks">
            {incompleteTasks.map((task) => (
              <div key={task.gid} className="task-card">
                <div className="task-main">
                  <button
                    className="task-checkbox"
                    onClick={() => handleToggleComplete(task)}
                    style={{ borderColor: projectColor }}
                  >
                    {task.completed && (
                      <div 
                        className="checkbox-check"
                        style={{ backgroundColor: projectColor }}
                      />
                    )}
                  </button>
                  
                  <div className="task-content">
                    <h4 className={`task-name ${task.completed ? 'completed' : ''}`}>
                      {task.name}
                    </h4>
                    {task.notes && (
                      <p className="task-notes">{task.notes}</p>
                    )}
                    
                    <div className="task-meta">
                      {task.assignee_gid && (
                        <span className="task-assignee">
                          Responsável: {task.assignee_gid}
                        </span>
                      )}
                      {task.due_on && (
                        <span 
                          className={`task-due ${isOverdue(task.due_on) ? 'overdue' : ''}`}
                        >
                          Vencimento: {formatDate(task.due_on)}
                        </span>
                      )}
                      {task.start_on && (
                        <span className="task-start">
                          Início: {formatDate(task.start_on)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="task-actions">
                  <button
                    className="delete-button"
                    onClick={() => handleDeleteTask(task.gid)}
                    title="Deletar tarefa"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {completedTasks.length > 0 && (
        <div className="task-section">
          <h3 className="section-title">
            Tarefas Concluídas ({completedTasks.length})
          </h3>
          <div className="tasks completed-section">
            {completedTasks.map((task) => (
              <div key={task.gid} className="task-card completed">
                <div className="task-main">
                  <button
                    className="task-checkbox completed"
                    onClick={() => handleToggleComplete(task)}
                    style={{ borderColor: projectColor }}
                  >
                    <div 
                      className="checkbox-check"
                      style={{ backgroundColor: projectColor }}
                    />
                  </button>
                  
                  <div className="task-content">
                    <h4 className="task-name completed">
                      {task.name}
                    </h4>
                    {task.notes && (
                      <p className="task-notes">{task.notes}</p>
                    )}
                    
                    <div className="task-meta">
                      {task.completed_at && (
                        <span className="task-completed">
                          Concluída em: {formatDate(task.completed_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="task-actions">
                  <button
                    className="delete-button"
                    onClick={() => handleDeleteTask(task.gid)}
                    title="Deletar tarefa"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskList;

