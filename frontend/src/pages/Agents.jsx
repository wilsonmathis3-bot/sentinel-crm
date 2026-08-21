import React, { useState } from 'react';
import { getProspecting, getNurturing, runHealthScores } from '../api';
import { Brain, Zap, Heart, RefreshCw, ArrowRight, Calendar } from 'lucide-react';

export default function Agents() {
  const [prospecting, setProspecting] = useState([]);
  const [nurturing, setNurturing] = useState([]);
  const [loading, setLoading] = useState({ prospecting: false, nurturing: false, health: false });

  const runAgent = async (type) => {
    setLoading(prev => ({ ...prev, [type]: true }));
    try {
      if (type === 'prospecting') {
        const r = await getProspecting();
        setProspecting(r.data);
      } else if (type === 'nurturing') {
        const r = await getNurturing();
        setNurturing(r.data);
      } else if (type === 'health') {
        await runHealthScores();
        alert('Health scores recalculated for all contacts');
      }
    } catch (e) {
      alert('Error: ' + e.message);
    }
    setLoading(prev => ({ ...prev, [type]: false }));
  };

  const getPriorityColor = (p) => {
    if (p === 'HIGH') return '#ef4444';
    if (p === 'MEDIUM') return '#f59e0b';
    return '#6b7280';
  };

  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px' }}>AI Agents</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        {/* Prospecting Agent */}
        <AgentCard
          icon={<Zap size={20} />}
          title="Prospecting Agent"
          subtitle="Scores leads based on response time + engagement"
          color="#f59e0b"
          onRun={() => runAgent('prospecting')}
          loading={loading.prospecting}
        />

        {/* Nurturing Agent */}
        <AgentCard
          icon={<Brain size={20} />}
          title="Nurturing Agent"
          subtitle="Auto-suggests follow-up timing"
          color="#8b5cf6"
          onRun={() => runAgent('nurturing')}
          loading={loading.nurturing}
        />
      </div>

      {/* Health Score Button */}
      <div style={{ marginBottom: '30px' }}>
        <button onClick={() => runAgent('health')} disabled={loading.health} style={{
          background: '#0f1525',
          border: '1px solid #1a2340',
          color: '#e0e6ed',
          padding: '12px 20px',
          borderRadius: '8px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px'
        }}>
          <Heart size={16} color="#ec4899" />
          {loading.health ? 'Recalculating...' : 'Recalculate All Health Scores'}
          <RefreshCw size={14} style={{ marginLeft: '8px' }} />
        </button>
      </div>

      {/* Prospecting Results */}
      {prospecting.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={18} color="#f59e0b" /> Prospecting Suggestions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {prospecting.map((s, i) => (
              <SuggestionCard key={i} suggestion={s} color="#f59e0b" />
            ))}
          </div>
        </div>
      )}

      {/* Nurturing Results */}
      {nurturing.length > 0 && (
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Brain size={18} color="#8b5cf6" /> Nurturing Suggestions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {nurturing.map((s, i) => (
              <SuggestionCard key={i} suggestion={s} color="#8b5cf6" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AgentCard({ icon, title, subtitle, color, onRun, loading }) {
  return (
    <div style={{
      background: '#0f1525',
      border: '1px solid #1a2340',
      borderRadius: '8px',
      padding: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
        <div style={{ color: color }}>{icon}</div>
        <h3 style={{ fontSize: '16px', fontWeight: '600' }}>{title}</h3>
      </div>
      <p style={{ fontSize: '13px', color: '#8b95a8', marginBottom: '16px' }}>{subtitle}</p>
      <button onClick={onRun} disabled={loading} style={{
        background: `${color}20`,
        color: color,
        border: `1px solid ${color}40`,
        padding: '8px 16px',
        borderRadius: '6px',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: '500',
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}>
        {loading ? 'Running...' : 'Run Agent'}
        <ArrowRight size={14} />
      </button>
    </div>
  );
}

function SuggestionCard({ suggestion, color }) {
  return (
    <div style={{
      background: '#0f1525',
      border: '1px solid #1a2340',
      borderLeft: `3px solid ${color}`,
      borderRadius: '8px',
      padding: '14px 16px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
        <div style={{ fontWeight: '500' }}>{suggestion.contact_name}</div>
        <span style={{
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: '600',
          background: `${getPriorityColor(suggestion.priority)}20`,
          color: getPriorityColor(suggestion.priority)
        }}>
          {suggestion.priority}
        </span>
      </div>
      <div style={{ fontSize: '14px', color: '#e0e6ed', marginBottom: '4px' }}>{suggestion.action}</div>
      <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '6px' }}>{suggestion.reason}</div>
      {suggestion.suggested_date && (
        <div style={{ fontSize: '12px', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Calendar size={12} />
          Suggested: {new Date(suggestion.suggested_date).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

function getPriorityColor(p) {
  if (p === 'HIGH') return '#ef4444';
  if (p === 'MEDIUM') return '#f59e0b';
  return '#6b7280';
}
