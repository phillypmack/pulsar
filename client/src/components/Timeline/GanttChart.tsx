import React, { useState, useEffect, useMemo } from 'react';
import { format, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isWeekend, differenceInDays, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import './GanttChart.css';

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

interface GanttChartProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
  onTaskUpdate?: (taskGid: string, updates: Partial<Task>) => void;
  className?: string;
}

const GanttChart: React.FC<GanttChartProps> = ({
  tasks,
  onTaskClick,
  onTaskUpdate,
  className = ''
}) => {
  const [viewMode, setViewMode] = useState<'days' | 'weeks' | 'months'>('weeks');
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [dragStartX, setDragStartX] = useState<number>(0);

  // Calcular período de visualização baseado nas tarefas
  const dateRange = useMemo(() => {
    const tasksWithDates = tasks.filter(task => task.start_on || task.due_on);
    
    if (tasksWithDates.length === 0) {
      const today = new Date();
      return {
        start: startOfWeek(today),
        end: endOfWeek(addDays(today, 30))
      };
    }

    const dates = tasksWithDates.flatMap(task => [
      task.start_on ? parseISO(task.start_on) : null,
      task.due_on ? parseISO(task.due_on) : null
    ].filter(Boolean) as Date[]);

    const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
    const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));

    return {
      start: startOfWeek(addDays(minDate, -7)),
      end: endOfWeek(addDays(maxDate, 7))
    };
  }, [tasks]);

  // Gerar colunas de tempo baseadas no modo de visualização
  const timeColumns = useMemo(() => {
    const columns = [];
    const { start, end } = dateRange;

    if (viewMode === 'days') {
      const days = eachDayOfInterval({ start, end });
      return days.map(day => ({
        date: day,
        label: format(day, 'dd/MM', { locale: ptBR }),
        isWeekend: isWeekend(day),
        width: 40
      }));
    } else if (viewMode === 'weeks') {
      let current = start;
      while (current <= end) {
        const weekEnd = endOfWeek(current);
        columns.push({
          date: current,
          label: `${format(current, 'dd/MM', { locale: ptBR })} - ${format(weekEnd, 'dd/MM', { locale: ptBR })}`,
          isWeekend: false,
          width: 100
        });
        current = addDays(weekEnd, 1);
      }
    } else {
      // months
      let current = start;
      while (current <= end) {
        columns.push({
          date: current,
          label: format(current, 'MMM yyyy', { locale: ptBR }),
          isWeekend: false,
          width: 120
        });
        current = addDays(current, 30);
      }
    }

    return columns;
  }, [dateRange, viewMode]);

  // Calcular posição e largura das barras de tarefa
  const getTaskBarStyle = (task: Task) => {
    if (!task.start_on && !task.due_on) {
      return { display: 'none' };
    }

    const startDate = task.start_on ? parseISO(task.start_on) : parseISO(task.due_on!);
    const endDate = task.due_on ? parseISO(task.due_on) : parseISO(task.start_on!);
    
    const totalDays = differenceInDays(dateRange.end, dateRange.start);
    const totalWidth = timeColumns.reduce((sum, col) => sum + col.width, 0);
    
    const startOffset = differenceInDays(startDate, dateRange.start);
    const duration = Math.max(1, differenceInDays(endDate, startDate) + 1);
    
    const left = (startOffset / totalDays) * totalWidth;
    const width = (duration / totalDays) * totalWidth;

    return {
      left: `${Math.max(0, left)}px`,
      width: `${Math.max(20, width)}px`,
      backgroundColor: task.completed ? '#28a745' : '#007bff',
      opacity: task.completed ? 0.7 : 1
    };
  };

  // Calcular progresso da tarefa
  const getTaskProgress = (task: Task) => {
    if (task.completed) return 100;
    if (task.progress !== undefined) return task.progress;
    
    // Calcular progresso baseado na data atual
    if (task.start_on && task.due_on) {
      const startDate = parseISO(task.start_on);
      const endDate = parseISO(task.due_on);
      const today = new Date();
      
      if (today < startDate) return 0;
      if (today > endDate) return 100;
      
      const totalDays = differenceInDays(endDate, startDate);
      const elapsedDays = differenceInDays(today, startDate);
      
      return Math.round((elapsedDays / totalDays) * 100);
    }
    
    return 0;
  };

  // Renderizar dependências
  const renderDependencies = (task: Task) => {
    if (!task.dependencies || task.dependencies.length === 0) return null;

    return task.dependencies.map(dep => {
      const taskIndex = tasks.findIndex(t => t.gid === task.gid);
      const depIndex = tasks.findIndex(t => t.gid === dep.gid);
      
      if (taskIndex === -1 || depIndex === -1) return null;

      const taskBarStyle = getTaskBarStyle(task);
      const depBarStyle = getTaskBarStyle(dep);
      
      if (taskBarStyle.display === 'none' || depBarStyle.display === 'none') return null;

      // Calcular posições para desenhar linha de dependência
      const depRight = parseFloat(depBarStyle.left as string) + parseFloat(depBarStyle.width as string);
      const taskLeft = parseFloat(taskBarStyle.left as string);
      
      const depY = depIndex * 50 + 25;
      const taskY = taskIndex * 50 + 25;

      return (
        <svg
          key={`dep-${dep.gid}-${task.gid}`}
          className="dependency-line"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            zIndex: 1
          }}
        >
          <path
            d={`M ${depRight} ${depY} L ${taskLeft - 10} ${depY} L ${taskLeft - 10} ${taskY} L ${taskLeft} ${taskY}`}
            stroke="#6c757d"
            strokeWidth="2"
            fill="none"
            markerEnd="url(#arrowhead)"
          />
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#6c757d"
              />
            </marker>
          </defs>
        </svg>
      );
    });
  };

  const handleTaskMouseDown = (e: React.MouseEvent, taskGid: string) => {
    if (onTaskUpdate) {
      setDraggedTask(taskGid);
      setDragStartX(e.clientX);
      e.preventDefault();
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (draggedTask && onTaskUpdate) {
      const deltaX = e.clientX - dragStartX;
      // Implementar lógica de arrastar tarefa
      // Por simplicidade, não implementado completamente aqui
    }
  };

  const handleMouseUp = () => {
    setDraggedTask(null);
    setDragStartX(0);
  };

  return (
    <div className={`gantt-chart ${className}`}>
      {/* Cabeçalho com controles */}
      <div className="gantt-header">
        <div className="gantt-controls">
          <div className="view-mode-selector">
            <button
              className={viewMode === 'days' ? 'active' : ''}
              onClick={() => setViewMode('days')}
            >
              Dias
            </button>
            <button
              className={viewMode === 'weeks' ? 'active' : ''}
              onClick={() => setViewMode('weeks')}
            >
              Semanas
            </button>
            <button
              className={viewMode === 'months' ? 'active' : ''}
              onClick={() => setViewMode('months')}
            >
              Meses
            </button>
          </div>
        </div>
      </div>

      <div className="gantt-container">
        {/* Coluna de tarefas */}
        <div className="gantt-task-list">
          <div className="gantt-task-header">
            <h4>Tarefas</h4>
          </div>
          {tasks.map((task, index) => (
            <div
              key={task.gid}
              className={`gantt-task-row ${selectedTask === task.gid ? 'selected' : ''}`}
              onClick={() => {
                setSelectedTask(task.gid);
                onTaskClick?.(task);
              }}
            >
              <div className="task-info">
                <div className="task-name" title={task.name}>
                  {task.name}
                </div>
                {task.assignee && (
                  <div className="task-assignee">
                    {task.assignee.name}
                  </div>
                )}
                <div className="task-dates">
                  {task.start_on && format(parseISO(task.start_on), 'dd/MM', { locale: ptBR })}
                  {task.start_on && task.due_on && ' - '}
                  {task.due_on && format(parseISO(task.due_on), 'dd/MM', { locale: ptBR })}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Timeline */}
        <div className="gantt-timeline">
          {/* Cabeçalho do timeline */}
          <div className="gantt-timeline-header">
            {timeColumns.map((column, index) => (
              <div
                key={index}
                className={`timeline-column-header ${column.isWeekend ? 'weekend' : ''}`}
                style={{ width: column.width }}
              >
                {column.label}
              </div>
            ))}
          </div>

          {/* Grid do timeline */}
          <div
            className="gantt-timeline-grid"
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            {/* Linhas de grid verticais */}
            {timeColumns.map((column, index) => (
              <div
                key={index}
                className={`timeline-grid-column ${column.isWeekend ? 'weekend' : ''}`}
                style={{ width: column.width }}
              />
            ))}

            {/* Barras de tarefas */}
            {tasks.map((task, index) => {
              const barStyle = getTaskBarStyle(task);
              const progress = getTaskProgress(task);

              if (barStyle.display === 'none') {
                return (
                  <div
                    key={task.gid}
                    className="gantt-task-bar-row"
                    style={{ top: index * 50 }}
                  />
                );
              }

              return (
                <div
                  key={task.gid}
                  className="gantt-task-bar-row"
                  style={{ top: index * 50 }}
                >
                  <div
                    className={`gantt-task-bar ${task.completed ? 'completed' : ''} ${selectedTask === task.gid ? 'selected' : ''}`}
                    style={barStyle}
                    onMouseDown={(e) => handleTaskMouseDown(e, task.gid)}
                    onClick={() => {
                      setSelectedTask(task.gid);
                      onTaskClick?.(task);
                    }}
                  >
                    <div
                      className="task-progress"
                      style={{ width: `${progress}%` }}
                    />
                    <div className="task-bar-content">
                      <span className="task-bar-name">{task.name}</span>
                      <span className="task-bar-progress">{progress}%</span>
                    </div>
                  </div>
                  
                  {/* Renderizar dependências */}
                  {renderDependencies(task)}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GanttChart;

