import React, { useEffect, useState } from 'react';
import { getMetrics, getPipeline } from '../api';
import { Users, DollarSign, TrendingUp, AlertTriangle, Activity, Target } from 'lucide-react';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [pipeline, setPipeline] = useState([]);

  useEffect(() => {
    getMetrics().then(r => setMetrics(r.data));
    getPipeline().then(r => setPipeline(r.data));
  }, []);

  if (!metrics) return <div style={{ padding: '20px' }}>Loading...</div>;

  const stageColors = {
    lead: '#6b7280',
    qualified: '#3b82f6',
    proposal: '#8b5cf6',
    negotiation: '#f59e0b',
    closed_won: '#10b981',
    closed_lost: '#ef4444'
  };

  return (
    <div>
      <h2 style={{ fontSize: '24px', marginBottom: '24px', fontWeight: '600' }}>Dashboard</h2>
      
      {/* Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '30px' }}>
        <MetricCard icon={<Users size={20} />} label="Contacts" value={metrics.total_contacts} color="#3b82f6" />
        <MetricCard icon={<DollarSign size={20} />} label="Total Pipeline" value={`$${metrics.total_value?.toLocaleString()}`} color="#10b981" />
        <MetricCard icon={<TrendingUp size={20} />} label="Win Rate" value={`${metrics.win_rate}%`} color="#8b5cf6" />
        <MetricCard icon={<AlertTriangle size={20} />} label="Overdue Tasks" value={metrics.overdue_tasks} color="#ef4444" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '30px' }}>
        <MetricCard icon={<Target size={20} />} label="Active Tasks" value={metrics.active_tasks} color="#f59e0b" />
        <MetricCard icon={<Activity size={20} />} label="Avg Deal Value" value={`$${metrics.avg_deal_value?.toLocaleString()}`} color="#06b6d4" />
        <MetricCard icon={<Users size={20} />} label="Avg Lead Score" value={metrics.avg_lead_score} color="#ec4899" />
        <MetricCard icon={<Activity size={20} />} label="Avg Health Score" value={metrics.avg_health_score} color="#84cc16" />
      </div>

      {/* Pipeline */}
      <h3 style={{ fontSize: '18px', marginBottom: '16px', fontWeight: '600' }}>Pipeline by Stage</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {pipeline.map(stage => (
          <div key={stage.stage} style={{
            background: '#0f1525',
            border: '1px solid #1a2340',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ 
                textTransform: 'capitalize', 
                fontWeight: '500',
                color: stageColors[stage.stage] || '#8b95a8'
              }}>
                {stage.stage.replace('_', ' ')}
              </span>
              <span style={{ fontSize: '20px', fontWeight: 'bold' }}>{stage.count}</span>
            </div>
            <div style={{ fontSize: '14px', color: '#8b95a8' }}>
              ${stage.value?.toLocaleString()} · {stage.avg_probability}% prob
            </div>
            <div style={{
              height: '4px',
              background: '#1a2340',
              borderRadius: '2px',
              marginTop: '12px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${Math.min(stage.avg_probability, 100)}%`,
                height: '100%',
                background: stageColors[stage.stage] || '#3b82f6',
                borderRadius: '2px',
                transition: 'width 0.3s'
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, color }) {
  return (
    <div style={{
      background: '#0f1525',
      border: '1px solid #1a2340',
      borderRadius: '8px',
      padding: '16px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    }}>
      <div style={{
        width: '40px',
        height: '40px',
        borderRadius: '8px',
        background: `${color}20`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: color
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>{label}</div>
        <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{value}</div>
      </div>
    </div>
  );
}
