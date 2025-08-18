import React from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import './ConnectionStatus.css';

const ConnectionStatus: React.FC = () => {
  const { isConnected } = useWebSocket();

  if (isConnected) {
    return (
      <div className="connection-status connected">
        <div className="status-indicator"></div>
        <span>Online</span>
      </div>
    );
  }

  return (
    <div className="connection-status disconnected">
      <div className="status-indicator"></div>
      <span>Desconectado</span>
    </div>
  );
};

export default ConnectionStatus;

