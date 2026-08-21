import React, { useEffect, useState } from 'react';
import { getTasks, getContacts, createTask, updateTask, deleteTask } from '../api';
import { Plus, CheckCircle, Clock, AlertTriangle, Trash2 } from 'lucide-react';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadTasks();
    getContacts({ limit: 1000 }).then(r => setContacts(r.data));
  }, [filter]);

  const loadTasks = () => {
    const params = {};
    if (filter === 'todo') params.status = 'todo';
    if (filter === 'in_progress') params.status = 'in_progress';
    if (filter === 'overdue') params.overdue = true;
    getTasks(params).then(r => setTasks(r.data));
  };

  const handleCreate = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    data.contact_id = parseInt(data.contact_id);
    createTask(data).then(() => {
      setShowForm(false);
      loadTasks();
    });
  };

  const toggleTask = (task) => {
    const newStatus = task.status === 'done' ? 'todo' : 'done';
    updateTask(task.id, { status: newStatus }).then(loadTasks);
  };

  const handleDelete = (id) => {
    if (confirm('Delete this task?')) {
      deleteTask(id).then(loadTasks);
    }
  };

  const getPriorityColor = (p) => {
    if (p === 'high') return '#ef4444';
    if (p === 'medium') return '#f59e0b';
    return '#6b7280';
  };

  const getStatusIcon = (status) => {
    if (status === 'done') return <CheckCircle size={18} color="#10b981" />;
    if (status === 'in_progress') return <Clock size={18} color="#3b82f6" />;
    return <div style={{ width: '18px', height: '18px', border: '2px solid #6b7280', borderRadius: '50%' }} />;
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600' }}>Tasks</h2>
        <button onClick={() => setShowForm(true)} style={{
          background: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px'
        }}>
          <Plus size={16} /> Add Task
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {['all', 'todo', 'in_progress', 'overdue'].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '6px 12px',
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            background: filter === f ? '#3b82f6' : '#1a2340',
            color: filter === f ? 'white' : '#8b95a8',
            fontSize: '13px',
            textTransform: 'capitalize'
          }}>
            {f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Task List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {tasks.map(task => {
          const contact = contacts.find(c => c.id === task.contact_id);
          const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
          
          return (
            <div key={task.id} style={{
              background: '#0f1525',
              border: '1px solid #1a2340',
              borderRadius: '8px',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              opacity: task.status === 'done' ? 0.6 : 1
            }}>
              <button onClick={() => toggleTask(task)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                {getStatusIcon(task.status)}
              </button>
              
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '500', textDecoration: task.status === 'done' ? 'line-through' : 'none' }}>{task.title}</div>
                <div style={{ fontSize: '12px', color: '#8b95a8', marginTop: '2px' }}>
                  {contact && `${contact.first_name} ${contact.last_name}`}
                  {task.due_date && ` · Due ${new Date(task.due_date).toLocaleDateString()}`}
                </div>
              </div>

              {isOverdue && <AlertTriangle size={16} color="#ef4444" />}
              
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: '600',
                background: `${getPriorityColor(task.priority)}20`,
                color: getPriorityColor(task.priority),
                textTransform: 'uppercase'
              }}>
                {task.priority}
              </span>
              
              <button onClick={() => handleDelete(task.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>
                <Trash2 size={14} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }} onClick={() => setShowForm(false)}>
          <div style={{ background: '#0f1525', border: '1px solid #1a2340', borderRadius: '12px', padding: '24px', width: '500px' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>New Task</h3>
            <form onSubmit={handleCreate}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Contact *</label>
                  <select name="contact_id" required style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }}>
                    <option value="">Select contact...</option>
                    {contacts.map(c => (
                      <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
                    ))}
                  </select>
                </div>
                <FormField name="title" label="Title" required />
                <FormField name="description" label="Description" />
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Priority</label>
                  <select name="priority" style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <FormField name="due_date" label="Due Date" type="date" />
              </div>
              <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={() => setShowForm(false)} style={{ background: '#1a2340', color: '#e0e6ed', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function FormField({ name, label, type = 'text', required }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>{label}{required && ' *'}</label>
      <input type={type} name={name} required={required} style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }} />
    </div>
  );
}
