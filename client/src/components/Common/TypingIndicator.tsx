import React from 'react';
import { TypingIndicator as TypingIndicatorType } from '../../services/websocket';
import './TypingIndicator.css';

interface TypingIndicatorProps {
  indicators: TypingIndicatorType[];
  className?: string;
}

const TypingIndicator: React.FC<TypingIndicatorProps> = ({ indicators, className = '' }) => {
  if (indicators.length === 0) {
    return null;
  }

  const formatTypingMessage = (indicators: TypingIndicatorType[]): string => {
    const names = indicators.map(indicator => indicator.user.name);
    
    if (names.length === 1) {
      return `${names[0]} está digitando...`;
    } else if (names.length === 2) {
      return `${names[0]} e ${names[1]} estão digitando...`;
    } else if (names.length === 3) {
      return `${names[0]}, ${names[1]} e ${names[2]} estão digitando...`;
    } else {
      return `${names[0]}, ${names[1]} e mais ${names.length - 2} pessoas estão digitando...`;
    }
  };

  return (
    <div className={`typing-indicator ${className}`}>
      <div className="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <span className="typing-message">
        {formatTypingMessage(indicators)}
      </span>
    </div>
  );
};

export default TypingIndicator;

