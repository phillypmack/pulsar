import React, { useState } from 'react';
import { useProject } from '../../contexts/ProjectContext';
import { useAuth } from '../../contexts/AuthContext';
import './CreateTaskModal.css';

interface CreateTaskModalProps {
  projectId: string;
  workspaceId: string;
  onClose: () => void;
  onTaskCreated: () => void;
}

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  projectId,
  workspaceId,
  onClose,
  onTaskCreated,
}) => {
  const { createTask } = useProject();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    notes: '',
    assignee_gid: user?.gid || '',
    due_on: '',
    start_on: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await createTask({
        ...formData,
        workspace_gid: workspaceId,
        project_gids: [projectId],
        assignee_gid: formData.assignee_gid || undefined,
        due_on: formData.due_on || undefined,
        start_on: formData.start_on || undefined,
      });
      onTaskCreated();
    } catch (error) {
      console.error('Erro ao criar tarefa:', error);
      alert('Erro ao criar tarefa. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Criar Nova Tarefa</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="task-form">
          <div className="form-group">
            <label htmlFor="name">Nome da Tarefa *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              placeholder="Digite o nome da tarefa"
            />
          </div>

          <div className="form-group">
            <label htmlFor="notes">Descrição</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              placeholder="Adicione uma descrição detalhada (opcional)"
              rows={4}
            />
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

          <div className="form-group">
            <label htmlFor="assignee_gid">Responsável</label>
            <select
              id="assignee_gid"
              name="assignee_gid"
              value={formData.assignee_gid}
              onChange={handleInputChange}
            >
              <option value="">Sem responsável</option>
              <option value={user?.gid}>{user?.name} (Você)</option>
            </select>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancelar
            </button>
            <button type="submit" disabled={loading} className="submit-button">
              {loading ? 'Criando...' : 'Criar Tarefa'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTaskModal;

