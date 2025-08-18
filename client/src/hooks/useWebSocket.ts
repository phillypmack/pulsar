import { useEffect, useState, useCallback } from 'react';
import { websocketService, TaskUpdate, TaskChange, ProjectChange, TypingIndicator } from '../services/websocket';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(websocketService.isConnected());

  useEffect(() => {
    const unsubscribe = websocketService.onConnectionChange(setIsConnected);
    return unsubscribe;
  }, []);

  const connect = useCallback(() => {
    websocketService.connect();
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const joinProject = useCallback((projectGid: string) => {
    websocketService.joinProject(projectGid);
  }, []);

  const leaveProject = useCallback((projectGid: string) => {
    websocketService.leaveProject(projectGid);
  }, []);

  const joinWorkspace = useCallback((workspaceGid: string) => {
    websocketService.joinWorkspace(workspaceGid);
  }, []);

  const sendTaskUpdate = useCallback((taskGid: string, updateType: string, updateData: any) => {
    websocketService.sendTaskUpdate(taskGid, updateType, updateData);
  }, []);

  const sendTypingIndicator = useCallback((targetType: string, targetGid: string, field: string, isTyping: boolean) => {
    websocketService.sendTypingIndicator(targetType, targetGid, field, isTyping);
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    joinProject,
    leaveProject,
    joinWorkspace,
    sendTaskUpdate,
    sendTypingIndicator
  };
};

export const useTaskUpdates = (onTaskUpdate?: (update: TaskUpdate) => void) => {
  useEffect(() => {
    if (!onTaskUpdate) return;

    const unsubscribe = websocketService.onTaskUpdate(onTaskUpdate);
    return unsubscribe;
  }, [onTaskUpdate]);
};

export const useTaskChanges = (onTaskChange?: (change: TaskChange) => void) => {
  useEffect(() => {
    if (!onTaskChange) return;

    const unsubscribe = websocketService.onTaskChange(onTaskChange);
    return unsubscribe;
  }, [onTaskChange]);
};

export const useProjectChanges = (onProjectChange?: (change: ProjectChange) => void) => {
  useEffect(() => {
    if (!onProjectChange) return;

    const unsubscribe = websocketService.onProjectChange(onProjectChange);
    return unsubscribe;
  }, [onProjectChange]);
};

export const useTypingIndicators = (onTypingIndicator?: (indicator: TypingIndicator) => void) => {
  const [typingUsers, setTypingUsers] = useState<Map<string, TypingIndicator>>(new Map());

  useEffect(() => {
    const handleTypingIndicator = (indicator: TypingIndicator) => {
      const key = `${indicator.target_gid}_${indicator.field}_${indicator.user.gid}`;
      
      setTypingUsers(prev => {
        const newMap = new Map(prev);
        
        if (indicator.is_typing) {
          newMap.set(key, indicator);
          
          // Auto-remove after 3 seconds of inactivity
          setTimeout(() => {
            setTypingUsers(current => {
              const updated = new Map(current);
              updated.delete(key);
              return updated;
            });
          }, 3000);
        } else {
          newMap.delete(key);
        }
        
        return newMap;
      });

      if (onTypingIndicator) {
        onTypingIndicator(indicator);
      }
    };

    const unsubscribe = websocketService.onTypingIndicator(handleTypingIndicator);
    return unsubscribe;
  }, [onTypingIndicator]);

  const getTypingUsers = useCallback((targetGid: string, field: string = 'notes') => {
    const users: TypingIndicator[] = [];
    
    typingUsers.forEach((indicator, key) => {
      if (indicator.target_gid === targetGid && indicator.field === field) {
        users.push(indicator);
      }
    });
    
    return users;
  }, [typingUsers]);

  return {
    typingUsers: Array.from(typingUsers.values()),
    getTypingUsers
  };
};

// Hook para gerenciar presença em projeto
export const useProjectPresence = (projectGid: string | null) => {
  const { joinProject, leaveProject, isConnected } = useWebSocket();

  useEffect(() => {
    if (!projectGid || !isConnected) return;

    joinProject(projectGid);

    return () => {
      leaveProject(projectGid);
    };
  }, [projectGid, isConnected, joinProject, leaveProject]);
};

// Hook para gerenciar presença em workspace
export const useWorkspacePresence = (workspaceGid: string | null) => {
  const { joinWorkspace, isConnected } = useWebSocket();

  useEffect(() => {
    if (!workspaceGid || !isConnected) return;

    joinWorkspace(workspaceGid);
  }, [workspaceGid, isConnected, joinWorkspace]);
};

