import React from 'react';
import { Project } from '../../services/api';
import './ProjectList.css';

interface ProjectListProps {
  projects: Project[];
  onProjectClick: (projectId: string) => void;
}

const ProjectList: React.FC<ProjectListProps> = ({ projects, onProjectClick }) => {
  if (projects.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📋</div>
        <h3>Nenhum projeto encontrado</h3>
        <p>Crie seu primeiro projeto para começar a organizar suas tarefas.</p>
      </div>
    );
  }

  return (
    <div className="project-list">
      {projects.map((project) => (
        <div
          key={project.gid}
          className="project-card"
          onClick={() => onProjectClick(project.gid)}
        >
          <div className="project-header">
            <div className="project-color" style={{ backgroundColor: project.color || '#667eea' }} />
            <h3 className="project-name">{project.name}</h3>
          </div>
          
          <div className="project-meta">
            <span className="project-view">
              Visualização: {getViewLabel(project.default_view)}
            </span>
            {project.due_on && (
              <span className="project-due">
                Vencimento: {new Date(project.due_on).toLocaleDateString('pt-BR')}
              </span>
            )}
          </div>

          <div className="project-actions">
            <button
              className="view-project-button"
              onClick={(e) => {
                e.stopPropagation();
                onProjectClick(project.gid);
              }}
            >
              Ver Projeto
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

const getViewLabel = (view: string): string => {
  const viewLabels: { [key: string]: string } = {
    list: 'Lista',
    board: 'Quadro',
    calendar: 'Calendário',
    timeline: 'Linha do Tempo',
  };
  return viewLabels[view] || view;
};

export default ProjectList;

