import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useProject } from '../../contexts/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { Workspace, workspaceService } from '../../services/api';
import ProjectList from '../Projects/ProjectList';
import CreateProjectModal from '../Projects/CreateProjectModal';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const { projects, fetchProjects, loading } = useProject();
  const navigate = useNavigate();
  
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [showCreateProject, setShowCreateProject] = useState(false);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  useEffect(() => {
    if (selectedWorkspace) {
      fetchProjects(selectedWorkspace.gid);
    }
  }, [selectedWorkspace, fetchProjects]);

  const loadWorkspaces = async () => {
    try {
      const workspacesData = await workspaceService.getWorkspaces();
      setWorkspaces(workspacesData);
      if (workspacesData.length > 0) {
        setSelectedWorkspace(workspacesData[0]);
      }
    } catch (error) {
      console.error('Erro ao carregar workspaces:', error);
    }
  };

  const handleProjectClick = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Projeto Clareza</h1>
          {selectedWorkspace && (
            <div className="workspace-selector">
              <select
                value={selectedWorkspace.gid}
                onChange={(e) => {
                  const workspace = workspaces.find(w => w.gid === e.target.value);
                  setSelectedWorkspace(workspace || null);
                }}
              >
                {workspaces.map(workspace => (
                  <option key={workspace.gid} value={workspace.gid}>
                    {workspace.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        
        <div className="header-right">
          <div className="user-info">
            <span>Olá, {user?.name}</span>
            <button onClick={handleLogout} className="logout-button">
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-content">
          <div className="content-header">
            <h2>Meus Projetos</h2>
            <button
              onClick={() => setShowCreateProject(true)}
              className="create-project-button"
            >
              + Novo Projeto
            </button>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner">Carregando projetos...</div>
            </div>
          ) : (
            <ProjectList
              projects={projects}
              onProjectClick={handleProjectClick}
            />
          )}
        </div>
      </main>

      {showCreateProject && selectedWorkspace && (
        <CreateProjectModal
          workspaceId={selectedWorkspace.gid}
          onClose={() => setShowCreateProject(false)}
          onProjectCreated={() => {
            setShowCreateProject(false);
            fetchProjects(selectedWorkspace.gid);
          }}
        />
      )}
    </div>
  );
};

export default Dashboard;

