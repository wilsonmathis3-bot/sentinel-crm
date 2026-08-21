import React, { useEffect, useState } from 'react';
import { getDeals, getContacts, createDeal, updateDeal, deleteDeal } from '../api';
import { Plus, DollarSign, Calendar, ArrowRight, Trash2, Edit2 } from 'lucide-react';

const STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'];
const STAGE_COLORS = {
  lead: '#6b7280',
  qualified: '#3b82f6',
  proposal: '#8b5cf6',
  negotiation: '#f59e0b',
  closed_won: '#10b981',
  closed_lost: '#ef4444'
};

export default function Deals() {
  const [deals, setDeals] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    getDeals().then(r => setDeals(r.data));
    getContacts({ limit: 1000 }).then(r => setContacts(r.data));
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    data.value = parseFloat(data.value);
    data.probability = parseFloat(data.probability);
    data.contact_id = parseInt(data.contact_id);
    createDeal(data).then(() => {
      setShowForm(false);
      getDeals().then(r => setDeals(r.data));
    });
  };

  const handleStageChange = (deal, newStage) => {
    updateDeal(deal.id, { stage: newStage }).then(() => {
      getDeals().then(r => setDeals(r.data));
    });
  };

  const handleDelete = (id) => {
    if (confirm('Delete this deal?')) {
      deleteDeal(id).then(() => getDeals().then(r => setDeals(r.data)));
    }
  };

  const dealsByStage = STAGES.reduce((acc, stage) => {
    acc[stage] = deals.filter(d => d.stage === stage);
    return acc;
  }, {});

  const totalValue = deals.reduce((sum, d) => sum + (d.value || 0), 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '600' }}>Deals</h2>
          <div style={{ fontSize: '14px', color: '#8b95a8', marginTop: '4px' }}>Total Pipeline: ${totalValue.toLocaleString()}</div>
        </div>
        <button onClick={() => setShowForm(true)} style={{
          background: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px'
        }}>
          <Plus size={16} /> Add Deal
        </button>
      </div>

      {/* Kanban Board */}
      <div style={{ display: 'flex', gap: '12px', overflowX: 'auto' }}>
        {STAGES.map(stage => (
          <div key={stage} style={{ minWidth: '240px', flex: 1 }}>
            <div style={{
              background: '#0f1525',
              border: '1px solid #1a2340',
              borderTop: `3px solid ${STAGE_COLORS[stage]}`,
              borderRadius: '8px',
              padding: '12px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', color: STAGE_COLORS[stage] }}>
                  {stage.replace('_', ' ')}
                </span>
                <span style={{ fontSize: '12px', color: '#8b95a8' }}>{dealsByStage[stage].length}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {dealsByStage[stage].map(deal => {
                  const contact = contacts.find(c => c.id === deal.contact_id);
                  return (
                    <div key={deal.id} style={{
                      background: '#131b2e',
                      border: '1px solid #1a2340',
                      borderRadius: '6px',
                      padding: '12px',
                      cursor: 'grab'
                    }}>
                      <div style={{ fontWeight: '500', marginBottom: '4px' }}>{deal.title}</div>
                      <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '8px' }}>
                        {contact ? `${contact.first_name} ${contact.last_name}` : 'Unknown'}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '14px', fontWeight: '600', color: '#10b981' }}>${deal.value?.toLocaleString()}</span>
                        <span style={{ fontSize: '11px', color: '#8b95a8' }}>{deal.probability}%</span>
                      </div>
                      <div style={{ marginTop: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {stage !== 'closed_won' && stage !== 'closed_lost' && (
                          <>
                            <button onClick={() => handleStageChange(deal, getNextStage(stage))} style={{
                              fontSize: '10px', padding: '2px 6px', background: '#3b82f620', color: '#3b82f6', border: '1px solid #3b82f640', borderRadius: '4px', cursor: 'pointer'
                            }}>
                              Advance
                            </button>
                            <button onClick={() => handleStageChange(deal, 'closed_lost')} style={{
                              fontSize: '10px', padding: '2px 6px', background: '#ef444420', color: '#ef4444', border: '1px solid #ef444440', borderRadius: '4px', cursor: 'pointer'
                            }}>
                              Lost
                            </button>
                          </>
                        )}
                        <button onClick={() => handleDelete(deal.id)} style={{
                          fontSize: '10px', padding: '2px 6px', background: 'transparent', color: '#ef4444', border: 'none', cursor: 'pointer', marginLeft: 'auto'
                        }}>
                          <Trash2 size={10} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }} onClick={() => setShowForm(false)}>
          <div style={{ background: '#0f1525', border: '1px solid #1a2340', borderRadius: '12px', padding: '24px', width: '500px' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>New Deal</h3>
            <form onSubmit={handleCreate}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Contact *</label>
                  <select name="contact_id" required style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }}>
                    <option value="">Select contact...</option>
                    {contacts.map(c => (
                      <option key={c.id} value={c.id}>{c.first_name} {c.last_name} - {c.company}</option>
                    ))}
                  </select>
                </div>
                <FormField name="title" label="Deal Title" required />
                <FormField name="value" label="Value ($)" type="number" required />
                <FormField name="probability" label="Probability (%)" type="number" defaultValue="20" />
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Stage</label>
                  <select name="stage" style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }}>
                    {STAGES.slice(0, -1).map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                  </select>
                </div>
                <FormField name="expected_close" label="Expected Close" type="date" />
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

function getNextStage(current) {
  const idx = STAGES.indexOf(current);
  return idx < STAGES.length - 2 ? STAGES[idx + 1] : current;
}

function FormField({ name, label, type = 'text', defaultValue, required }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>{label}{required && ' *'}</label>
      <input type={type} name={name} defaultValue={defaultValue} required={required} style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }} />
    </div>
  );
}
