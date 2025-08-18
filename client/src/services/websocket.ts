import io, { Socket } from 'socket.io-client';

export interface TaskUpdate {
  task_gid: string;
  update_type: string;
  update_data: any;
  updated_by: {
    gid: string;
    name: string;
  };
  timestamp: string;
}

export interface TaskChange {
  task_gid: string;
  change_type: string;
  change_data: any;
  task_data: any;
  changed_by: {
    gid: string;
    name: string;
  };
  timestamp: string;
}

export interface ProjectChange {
  project_gid: string;
  change_type: string;
  change_data: any;
  project_data: any;
  changed_by: {
    gid: string;
    name: string;
  };
  timestamp: string;
}

export interface TypingIndicator {
  target_type: string;
  target_gid: string;
  field: string;
  is_typing: boolean;
  user: {
    gid: string;
    name: string;
  };
  timestamp: string;
}

class WebSocketService {
  private socket: Socket | null = null;
  private token: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  // Event listeners
  private taskUpdateListeners: ((update: TaskUpdate) => void)[] = [];
  private taskChangeListeners: ((change: TaskChange) => void)[] = [];
  private projectChangeListeners: ((change: ProjectChange) => void)[] = [];
  private typingIndicatorListeners: ((indicator: TypingIndicator) => void)[] = [];
  private connectionListeners: ((connected: boolean) => void)[] = [];

  constructor() {
    this.token = localStorage.getItem('token');
  }

  connect(): void {
    if (!this.token) {
      console.warn('No token available for WebSocket connection');
      return;
    }

    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    const serverUrl = process.env.REACT_APP_API_URL?.replace('/api', '') || 'http://localhost:5001';
    
    this.socket = io(serverUrl, {
      query: {
        token: this.token
      },
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true
    });

    this.setupEventListeners();
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.reconnectAttempts = 0;
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.notifyConnectionListeners(true);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.notifyConnectionListeners(false);
      
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        this.handleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    });

    this.socket.on('connected', (data) => {
      console.log('WebSocket authentication successful:', data);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // Task-related events
    this.socket.on('task_updated', (update: TaskUpdate) => {
      this.taskUpdateListeners.forEach(listener => listener(update));
    });

    this.socket.on('task_changed', (change: TaskChange) => {
      this.taskChangeListeners.forEach(listener => listener(change));
    });

    // Project-related events
    this.socket.on('project_changed', (change: ProjectChange) => {
      this.projectChangeListeners.forEach(listener => listener(change));
    });

    // Typing indicators
    this.socket.on('typing_indicator', (indicator: TypingIndicator) => {
      this.typingIndicatorListeners.forEach(listener => listener(indicator));
    });

    // User presence events
    this.socket.on('user_joined_project', (data) => {
      console.log(`${data.user_name} joined project ${data.project_gid}`);
    });

    this.socket.on('user_left_project', (data) => {
      console.log(`${data.user_name} left project ${data.project_gid}`);
    });
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private notifyConnectionListeners(connected: boolean): void {
    this.connectionListeners.forEach(listener => listener(connected));
  }

  // Room management
  joinProject(projectGid: string): void {
    if (this.socket?.connected) {
      this.socket.emit('join_project', { project_gid: projectGid });
    }
  }

  leaveProject(projectGid: string): void {
    if (this.socket?.connected) {
      this.socket.emit('leave_project', { project_gid: projectGid });
    }
  }

  joinWorkspace(workspaceGid: string): void {
    if (this.socket?.connected) {
      this.socket.emit('join_workspace', { workspace_gid: workspaceGid });
    }
  }

  // Real-time updates
  sendTaskUpdate(taskGid: string, updateType: string, updateData: any): void {
    if (this.socket?.connected) {
      this.socket.emit('task_update', {
        task_gid: taskGid,
        update_type: updateType,
        update_data: updateData
      });
    }
  }

  sendTypingIndicator(targetType: string, targetGid: string, field: string, isTyping: boolean): void {
    if (this.socket?.connected) {
      this.socket.emit('typing_indicator', {
        target_type: targetType,
        target_gid: targetGid,
        field: field,
        is_typing: isTyping
      });
    }
  }

  // Event listener management
  onTaskUpdate(listener: (update: TaskUpdate) => void): () => void {
    this.taskUpdateListeners.push(listener);
    return () => {
      const index = this.taskUpdateListeners.indexOf(listener);
      if (index > -1) {
        this.taskUpdateListeners.splice(index, 1);
      }
    };
  }

  onTaskChange(listener: (change: TaskChange) => void): () => void {
    this.taskChangeListeners.push(listener);
    return () => {
      const index = this.taskChangeListeners.indexOf(listener);
      if (index > -1) {
        this.taskChangeListeners.splice(index, 1);
      }
    };
  }

  onProjectChange(listener: (change: ProjectChange) => void): () => void {
    this.projectChangeListeners.push(listener);
    return () => {
      const index = this.projectChangeListeners.indexOf(listener);
      if (index > -1) {
        this.projectChangeListeners.splice(index, 1);
      }
    };
  }

  onTypingIndicator(listener: (indicator: TypingIndicator) => void): () => void {
    this.typingIndicatorListeners.push(listener);
    return () => {
      const index = this.typingIndicatorListeners.indexOf(listener);
      if (index > -1) {
        this.typingIndicatorListeners.splice(index, 1);
      }
    };
  }

  onConnectionChange(listener: (connected: boolean) => void): () => void {
    this.connectionListeners.push(listener);
    return () => {
      const index = this.connectionListeners.indexOf(listener);
      if (index > -1) {
        this.connectionListeners.splice(index, 1);
      }
    };
  }

  // Utility methods
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  updateToken(token: string): void {
    this.token = token;
    localStorage.setItem('token', token);
    
    // Reconnect with new token
    if (this.socket?.connected) {
      this.disconnect();
      this.connect();
    }
  }
}

// Singleton instance
export const websocketService = new WebSocketService();

// Auto-connect when token is available
if (localStorage.getItem('token')) {
  websocketService.connect();
}

