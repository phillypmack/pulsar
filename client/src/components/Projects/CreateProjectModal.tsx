import React, { useState } from 'react';
import { useProject } from '../../contexts/ProjectContext';
import { useAuth } from '../../contexts/AuthContext';
import './CreateProjectModal.css';

interface CreateProjectModalProps {
  workspaceId: string;
  onClose: () => void;
  onProjectCreated: () => void;
}

const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  workspaceId,
  onClose,
  onProjectCreated,
}) => {
  const { createProject } = useProject();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    default_view: 'list',
    color: '#667eea',
    privacy_setting: 'public_to_workspace',
    due_on: '',
    start_on: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await createProject({
        ...formData,
        workspace_gid: workspaceId,
        owner_gid: user?.gid,
        due_on: formData.due_on || undefined,
        start_on: formData.start_on || undefined,
      });
      onProjectCreated();
    } catch (error) {
      console.error('Erro ao criar projeto:', error);
      alert('Erro ao criar projeto. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#f5576c',
    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
    '#ffecd2', '#fcb69f', '#a8edea', '#fed6e3',
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Criar Novo Projeto</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="project-form">
          <div className="form-group">
            <label htmlFor="name">Nome do Projeto *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              placeholder="Digite o nome do projeto"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="default_view">Visualização Padrão</label>
              <select
                id="default_view"
                name="default_view"
                value={formData.default_view}
                onChange={handleInputChange}
              >
                <option value="list">Lista</option>
                <option value="board">Quadro</option>
                <option value="calendar">Calendário</option>
                <option value="timeline">Linha do Tempo</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="privacy_setting">Privacidade</label>
              <select
                id="privacy_setting"
                name="privacy_setting"
                value={formData.privacy_setting}
                onChange={handleInputChange}
              >
                <option value="public_to_workspace">Público no Workspace</option>
                <option value="private_to_team">Privado para Equipe</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Cor do Projeto</label>
            <div className="color-picker">
              {colors.map((color) => (
                <button
                  key={color}
                  type="button"
                  className={`color-option ${formData.color === color ? 'selected' : ''}`}
                  style={{ backgroundColor: color }}
                  onClick={() => setFormData({ ...formData, color })}
                />
              ))}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start_on">Data de Início</label>
              <input
                type="date"
                id="start_on"
                name="start_on"
                value={formData.start_on}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="due_on">Data de Vencimento</label>
              <input
                type="date"
                id="due_on"
                name="due_on"
                value={formData.due_on}
                onChange={handleInputChange}
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancelar
            </button>
            <button type="submit" disabled={loading} className="submit-button">
              {loading ? 'Criando...' : 'Criar Projeto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProjectModal;

