'use client'

import { useState } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'
import { Plus, MoreHorizontal, User } from 'lucide-react'

interface Issue {
  id: string
  title: string
  status: 'backlog' | 'todo' | 'inprogress' | 'done'
  priority: 'urgent' | 'high' | 'medium' | 'low'
  assignee?: string
}

const columns = [
  { id: 'backlog', title: 'Backlog', color: 'var(--color-status-backlog)' },
  { id: 'todo', title: 'Todo', color: 'var(--color-status-todo)' },
  { id: 'inprogress', title: 'In Progress', color: 'var(--color-status-inprogress)' },
  { id: 'done', title: 'Done', color: 'var(--color-status-done)' },
]

// Demo data
const initialIssues: Issue[] = [
  { id: '1', title: 'Set up project structure', status: 'done', priority: 'high' },
  { id: '2', title: 'Design database schema', status: 'done', priority: 'high' },
  { id: '3', title: 'Implement authentication', status: 'inprogress', priority: 'urgent', assignee: 'You' },
  { id: '4', title: 'Create API endpoints', status: 'inprogress', priority: 'high' },
  { id: '5', title: 'Build dashboard UI', status: 'todo', priority: 'medium' },
  { id: '6', title: 'Add Stripe integration', status: 'todo', priority: 'medium' },
  { id: '7', title: 'Write documentation', status: 'backlog', priority: 'low' },
  { id: '8', title: 'Performance optimization', status: 'backlog', priority: 'low' },
]

const priorityColors = {
  urgent: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500',
}

export function KanbanBoard() {
  const [issues, setIssues] = useState<Issue[]>(initialIssues)

  const onDragEnd = (result: DropResult) => {
    const { destination, source, draggableId } = result

    if (!destination) return
    if (destination.droppableId === source.droppableId && destination.index === source.index) return

    setIssues((prev) =>
      prev.map((issue) =>
        issue.id === draggableId
          ? { ...issue, status: destination.droppableId as Issue['status'] }
          : issue
      )
    )
  }

  const getIssuesByStatus = (status: string) =>
    issues.filter((issue) => issue.status === status)

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin">
        {columns.map((column) => {
          const columnIssues = getIssuesByStatus(column.id)
          return (
            <div key={column.id} className="kanban-column">
              <div className="kanban-column-header">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: column.color }}
                  />
                  <span>{column.title}</span>
                  <span className="text-text-muted">{columnIssues.length}</span>
                </div>
                <button className="btn-ghost p-1">
                  <Plus className="h-4 w-4" />
                </button>
              </div>

              <Droppable droppableId={column.id}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`flex-1 p-1 rounded-lg transition-colors ${
                      snapshot.isDraggingOver ? 'bg-surface-hover' : ''
                    }`}
                  >
                    {columnIssues.map((issue, index) => (
                      <Draggable key={issue.id} draggableId={issue.id} index={index}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className={`kanban-card ${
                              snapshot.isDragging ? 'shadow-lg' : ''
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <div
                                  className={`w-2 h-2 rounded-full ${priorityColors[issue.priority]}`}
                                />
                                <span className="text-sm font-medium">{issue.title}</span>
                              </div>
                              <button className="btn-ghost p-0.5 opacity-0 group-hover:opacity-100">
                                <MoreHorizontal className="h-3.5 w-3.5" />
                              </button>
                            </div>
                            {issue.assignee && (
                              <div className="flex items-center gap-1.5 mt-2 text-xs text-text-muted">
                                <User className="h-3 w-3" />
                                {issue.assignee}
                              </div>
                            )}
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          )
        })}
      </div>
    </DragDropContext>
  )
}
