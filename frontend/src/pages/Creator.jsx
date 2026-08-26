import React, { useEffect, useState } from 'react';
import {
  getPersonas,
  getPersonaPortfolio,
  getQueue,
  approveAssets,
  rejectAssets,
  getMetricsSummary,
  getFlaggedMetrics,
  runBatch,
  getGraduation,
  getInstagramAccounts,
} from '../api';
import {
  Users, Image, CheckCircle, XCircle, Play, BarChart3,
  AlertTriangle, TrendingUp, Award, Clock, Layers, Sparkles
} from 'lucide-react';

export default function Creator() {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [queue, setQueue] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [flagged, setFlagged] = useState([]);
  const [graduation, setGraduation] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState({
    personas: true, queue: true, metrics: false, batch: false
  });

  useEffect(() => {
    loadPersonas();
    loadQueue();
    loadFlagged();
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedPersona) {
      loadPortfolio(selectedPersona.id);
      loadMetrics(selectedPersona.id);
      loadGraduation(selectedPersona.id);
    }
  }, [selectedPersona]);

  const loadPersonas = async () => {
    try {
      const r = await getPersonas();
      setPersonas(r.data);
      if (r.data.length > 0 && !selectedPersona) {
        setSelectedPersona(r.data[0]);
      }
    } catch (e) {
      console.error('Failed to load personas:', e);
    }
    setLoading(prev => ({ ...prev, personas: false }));
  };

  const loadPortfolio = async (id) => {
    try {
      const r = await getPersonaPortfolio(id);
      setPortfolio(r.data);
    } catch (e) {
      console.error('Failed to load portfolio:', e);
    }
  };

  const loadQueue = async () => {
    try {
      const r = await getQueue();
      setQueue(r.data.assets || []);
    } catch (e) {
      console.error('Failed to load queue:', e);
    }
    setLoading(prev => ({ ...prev, queue: false }));
  };

  const loadMetrics = async (id) => {
    setLoading(prev => ({ ...prev, metrics: true }));
    try {
      const r = await getMetricsSummary(id);
      setMetrics(r.data);
    } catch (e) {
      console.error('Failed to load metrics:', e);
    }
    setLoading(prev => ({ ...prev, metrics: false }));
  };

  const loadFlagged = async () => {
    try {
      const r = await getFlaggedMetrics();
      setFlagged(r.data.flagged || []);
    } catch (e) {
      console.error('Failed to load flagged:', e);
    }
  };

  const loadGraduation = async (id) => {
    try {
      const r = await getGraduation(id);
      setGraduation(r.data);
    } catch (e) {
      console.error('Failed to load graduation:', e);
    }
  };

  const loadAccounts = async () => {
    try {
      const r = await getInstagramAccounts();
      setAccounts(r.data.accounts || []);
    } catch (e) {
      console.error('Failed to load accounts:', e);
    }
  };

  const handleApprove = async (assetId) => {
    try {
      await approveAssets([assetId]);
      setQueue(prev => prev.filter(a => a.id !== assetId));
    } catch (e) {
      alert('Approve failed: ' + e.message);
    }
  };

  const handleReject = async (assetId) => {
    try {
      await rejectAssets([assetId], 'Rejected from UI');
      setQueue(prev => prev.filter(a => a.id !== assetId));
    } catch (e) {
      alert('Reject failed: ' + e.message);
    }
  };

  const handleRunBatch = async () => {
    setLoading(prev => ({ ...prev, batch: true }));
    try {
      const r = await runBatch();
      alert(`Batch started: ${r.data.total_prompts || 0} prompts queued`);
      loadQueue();
    } catch (e) {
      alert('Batch failed: ' + e.message);
    }
    setLoading(prev => ({ ...prev, batch: false }));
  };

  const getLifecycleColor = (lifecycle) => {
    if (lifecycle === 'incubating') return '#f59e0b';
    if (lifecycle === 'graduated') return '#10b981';
    if (lifecycle === 'independent') return '#8b5cf6';
    return '#6b7280';
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600' }}>Creator Studio</h2>
        <button onClick={handleRunBatch} disabled={loading.batch} style={{
          background: '#0f1525',
          border: '1px solid #1a2340',
          color: '#e0e6ed',
          padding: '10px 18px',
          borderRadius: '8px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px'
        }}>
          <Play size={16} color="#10b981" />
          {loading.batch ? 'Running...' : 'Run Batch'}
        </button>
      </div>

      {/* Persona Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '30px' }}>
        {personas.map(p => (
          <div
            key={p.id}
            onClick={() => setSelectedPersona(p)}
            style={{
              background: selectedPersona?.id === p.id ? '#0f1525' : '#0a0f1a',
              border: selectedPersona?.id === p.id ? '2px solid #3b82f6' : '1px solid #1a2340',
              borderRadius: '8px',
              padding: '16px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600' }}>{p.name}</h3>
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: '600',
                background: `${getLifecycleColor(p.lifecycle || 'incubating')}20`,
                color: getLifecycleColor(p.lifecycle || 'incubating')
              }}>
                {p.lifecycle || 'incubating'}
              </span>
            </div>
            <div style={{ fontSize: '13px', color: '#8b95a8', marginBottom: '8px' }}>{p.archetype}</div>
            {p.brief_json && (
              <div style={{ fontSize: '12px', color: '#6b7280', lineHeight: '1.4' }}>
                {(() => {
                  try {
                    const brief = JSON.parse(p.brief_json);
                    return brief.look?.substring(0, 80) + '...' || 'No look description';
                  } catch {
                    return 'Brief unavailable';
                  }
                })()}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Selected Persona Detail */}
      {selectedPersona && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '30px' }}>
          {/* Portfolio */}
          <div style={{
            background: '#0f1525',
            border: '1px solid #1a2340',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="#3b82f6" /> Portfolio: {selectedPersona.name}
            </h3>
            {portfolio?.sets?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {portfolio.sets.map(set => (
                  <div key={set.id} style={{
                    background: '#0a0f1a',
                    border: '1px solid #1a2340',
                    borderRadius: '6px',
                    padding: '12px'
                  }}>
                    <div style={{ fontWeight: '500', marginBottom: '4px' }}>{set.title}</div>
                    <div style={{ fontSize: '12px', color: '#8b95a8' }}>
                      {set.theme} {set.week_label && `· ${set.week_label}`}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#8b95a8', fontSize: '14px' }}>No portfolio sets yet</div>
            )}
          </div>

          {/* Metrics + Graduation */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Metrics Summary */}
            <div style={{
              background: '#0f1525',
              border: '1px solid #1a2340',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BarChart3 size={14} color="#3b82f6" /> Metrics (30d)
              </h4>
              {loading.metrics ? (
                <div style={{ color: '#8b95a8', fontSize: '13px' }}>Loading...</div>
              ) : metrics?.status === 'ok' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <MetricMini label="Posts" value={metrics.total_posts} />
                  <MetricMini label="Likes" value={metrics.total_likes} />
                  <MetricMini label="Views" value={metrics.total_views} />
                  <MetricMini label="Eng. Rate" value={`${(metrics.avg_engagement_rate * 100).toFixed(1)}%`} />
                </div>
              ) : (
                <div style={{ color: '#8b95a8', fontSize: '13px' }}>No metrics yet</div>
              )}
            </div>

            {/* Graduation Status */}
            {graduation && (
              <div style={{
                background: '#0f1525',
                border: '1px solid #1a2340',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Award size={14} color={graduation.eligible ? '#10b981' : '#f59e0b'} />
                  Graduation
                </h4>
                <div style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: graduation.eligible ? '#10b98120' : '#f59e0b20',
                  color: graduation.eligible ? '#10b981' : '#f59e0b',
                  fontSize: '13px',
                  fontWeight: '600',
                  marginBottom: '8px'
                }}>
                  {graduation.eligible ? 'Eligible' : 'Not Eligible'}
                </div>
                {graduation.reasons?.map((r, i) => (
                  <div key={i} style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '2px' }}>• {r}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Approval Queue */}
      <div style={{
        background: '#0f1525',
        border: '1px solid #1a2340',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '30px'
      }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={18} color="#f59e0b" /> Approval Queue ({queue.length})
        </h3>
        {queue.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {queue.map(asset => (
              <div key={asset.id} style={{
                background: '#0a0f1a',
                border: '1px solid #1a2340',
                borderRadius: '6px',
                padding: '14px 16px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                    {asset.persona_name || 'Unknown'} · Asset #{asset.id}
                  </div>
                  <div style={{ fontSize: '13px', color: '#8b95a8', marginBottom: '4px' }}>
                    {asset.prompt?.substring(0, 100)}...
                  </div>
                  {asset.caption_draft && (
                    <div style={{ fontSize: '12px', color: '#6b7280', fontStyle: 'italic' }}>
                      Caption: {asset.caption_draft.substring(0, 80)}...
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={() => handleApprove(asset.id)} style={{
                    background: '#10b98120',
                    color: '#10b981',
                    border: '1px solid #10b98140',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <CheckCircle size={12} /> Approve
                  </button>
                  <button onClick={() => handleReject(asset.id)} style={{
                    background: '#ef444420',
                    color: '#ef4444',
                    border: '1px solid #ef444440',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <XCircle size={12} /> Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: '#8b95a8', fontSize: '14px' }}>No assets pending approval</div>
        )}
      </div>

      {/* Flagged Metrics */}
      {flagged.length > 0 && (
        <div style={{
          background: '#0f1525',
          border: '1px solid #1a2340',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '30px'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#ef4444" /> Flagged Metrics ({flagged.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {flagged.map(f => (
              <div key={f.id} style={{
                background: '#0a0f1a',
                border: '1px solid #1a2340',
                borderLeft: '3px solid #ef4444',
                borderRadius: '6px',
                padding: '12px 16px'
              }}>
                <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                  {f.persona_name} · {f.platform}
                </div>
                <div style={{ fontSize: '13px', color: '#ef4444' }}>{f.flag_reason}</div>
                <div style={{ fontSize: '12px', color: '#8b95a8' }}>
                  {f.date && new Date(f.date).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instagram Accounts */}
      {accounts.length > 0 && (
        <div style={{
          background: '#0f1525',
          border: '1px solid #1a2340',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={18} color="#8b5cf6" /> Instagram Accounts
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {accounts.map(acc => (
              <div key={acc.id} style={{
                background: '#0a0f1a',
                border: '1px solid #1a2340',
                borderRadius: '6px',
                padding: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: '500' }}>@{acc.handle}</span>
                  {acc.is_incubator && (
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      background: '#f59e0b20',
                      color: '#f59e0b',
                      fontWeight: '600'
                    }}>INCUBATOR</span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: '#8b95a8', marginTop: '4px' }}>
                  {acc.is_active ? 'Active' : 'Inactive'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricMini({ label, value }) {
  return (
    <div style={{
      background: '#0a0f1a',
      borderRadius: '6px',
      padding: '8px 12px'
    }}>
      <div style={{ fontSize: '11px', color: '#8b95a8', marginBottom: '2px' }}>{label}</div>
      <div style={{ fontSize: '16px', fontWeight: '600' }}>{value}</div>
    </div>
  );
}
