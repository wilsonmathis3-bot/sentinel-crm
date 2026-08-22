import React, { useEffect, useState } from 'react';
import { getContacts, createContact, updateContact, deleteContact, createInteraction, importContacts } from '../api';
import { Plus, Search, Edit2, Trash2, MessageSquare, Star, Heart, Upload, FileSpreadsheet } from 'lucide-react';

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [selectedContact, setSelectedContact] = useState(null);
  const [newInteraction, setNewInteraction] = useState({ type: 'email', summary: '' });
  const [importFile, setImportFile] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const [dryRun, setDryRun] = useState(true);

  useEffect(() => { loadContacts(); }, [search]);

  const loadContacts = () => {
    getContacts({ search: search || undefined }).then(r => setContacts(r.data));
  };

  const handleImport = async (e) => {
    e.preventDefault();
    if (!importFile) return;
    setImporting(true);
    setImportResult(null);
    const formData = new FormData();
    formData.append('file', importFile);
    formData.append('dry_run', String(dryRun));
    try {
      const res = await importContacts(formData);
      setImportResult(res.data);
      if (!dryRun) loadContacts();
    } catch (err) {
      setImportResult({ error: err.response?.data?.detail || err.message });
    } finally {
      setImporting(false);
    }
  };

  const handleCreate = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    createContact(data).then(() => {
      setShowForm(false);
      loadContacts();
    });
  };

  const handleUpdate = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    updateContact(editing.id, data).then(() => {
      setEditing(null);
      loadContacts();
    });
  };

  const handleDelete = (id) => {
    if (confirm('Delete this contact?')) {
      deleteContact(id).then(loadContacts);
    }
  };

  const handleAddInteraction = (e) => {
    e.preventDefault();
    createInteraction(selectedContact.id, newInteraction).then(() => {
      setNewInteraction({ type: 'email', summary: '' });
      loadContacts();
    });
  };

  const getScoreColor = (score) => {
    if (score >= 70) return '#10b981';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600' }}>Contacts</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <form onSubmit={handleImport} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#8b95a8', cursor: 'pointer' }}>
              <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} />
              Dry run
            </label>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={e => setImportFile(e.target.files[0])}
              style={{ display: 'none' }}
              id="import-file"
            />
            <label htmlFor="import-file" style={{
              background: '#1a2340',
              color: '#e0e6ed',
              border: '1px solid #2d3a5c',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px'
            }}>
              <FileSpreadsheet size={16} /> {importFile ? importFile.name : 'Choose file'}
            </label>
            <button type="submit" disabled={!importFile || importing} style={{
              background: importFile ? '#10b981' : '#1a2340',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: importFile ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              opacity: importFile ? 1 : 0.5
            }}>
              <Upload size={16} /> {importing ? 'Importing...' : (dryRun ? 'Preview' : 'Import')}
            </button>
          </form>
          <button onClick={() => setShowForm(true)} style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Plus size={16} /> Add Contact
          </button>
        </div>
      </div>

      {/* Import Results */}
      {importResult && (
        <div style={{ background: '#0f1525', border: '1px solid #1a2340', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600' }}>
              {importResult.error ? 'Import Error' : (importResult.dry_run ? 'Dry Run Preview' : 'Import Results')}
            </h4>
            <button onClick={() => setImportResult(null)} style={{ background: 'none', border: 'none', color: '#8b95a8', cursor: 'pointer' }}>×</button>
          </div>
          {importResult.error ? (
            <div style={{ color: '#ef4444', fontSize: '13px' }}>{importResult.error}</div>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '12px' }}>
                <div style={{ textAlign: 'center', padding: '10px', background: '#131b2e', borderRadius: '6px' }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#10b981' }}>{importResult.imported}</div>
                  <div style={{ fontSize: '11px', color: '#8b95a8' }}>{importResult.dry_run ? 'Would import' : 'Imported'}</div>
                </div>
                <div style={{ textAlign: 'center', padding: '10px', background: '#131b2e', borderRadius: '6px' }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f59e0b' }}>{importResult.skipped_duplicates}</div>
                  <div style={{ fontSize: '11px', color: '#8b95a8' }}>Duplicates skipped</div>
                </div>
                <div style={{ textAlign: 'center', padding: '10px', background: '#131b2e', borderRadius: '6px' }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ef4444' }}>{importResult.errors}</div>
                  <div style={{ fontSize: '11px', color: '#8b95a8' }}>Errors</div>
                </div>
                <div style={{ textAlign: 'center', padding: '10px', background: '#131b2e', borderRadius: '6px' }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#3b82f6' }}>{Object.keys(importResult.column_map || {}).length}</div>
                  <div style={{ fontSize: '11px', color: '#8b95a8' }}>Columns mapped</div>
                </div>
              </div>
              {importResult.row_errors?.length > 0 && (
                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#131b2e' }}>
                        <th style={{ padding: '6px', textAlign: 'left', color: '#8b95a8' }}>Row</th>
                        <th style={{ padding: '6px', textAlign: 'left', color: '#8b95a8' }}>Errors</th>
                      </tr>
                    </thead>
                    <tbody>
                      {importResult.row_errors.map((err, i) => (
                        <tr key={i} style={{ borderTop: '1px solid #1a2340' }}>
                          <td style={{ padding: '6px', color: '#ef4444' }}>{err.row_number}</td>
                          <td style={{ padding: '6px' }}>{err.errors.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b95a8' }} />
          <input
            type="text"
            placeholder="Search contacts..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px 10px 36px',
              background: '#0f1525',
              border: '1px solid #1a2340',
              borderRadius: '6px',
              color: '#e0e6ed',
              fontSize: '14px'
            }}
          />
        </div>
      </div>

      {/* Contacts Table */}
      <div style={{ background: '#0f1525', border: '1px solid #1a2340', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#131b2e' }}>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#8b95a8', fontWeight: '500' }}>Name</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#8b95a8', fontWeight: '500' }}>Company</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#8b95a8', fontWeight: '500' }}>Location</th>
              <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', textTransform: 'uppercase', color: '#8b95a8', fontWeight: '500' }}>Lead Score</th>
              <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', textTransform: 'uppercase', color: '#8b95a8', fontWeight: '500' }}>Health</th>
              <th style={{ padding: '12px 16px', textAlign: 'right', fontSize: '12px', textTransform: 'uppercase', color: '#8b95a8', fontWeight: '500' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map(c => (
              <tr key={c.id} style={{ borderTop: '1px solid #1a2340', cursor: 'pointer' }} onClick={() => setSelectedContact(c)}>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: '500' }}>{c.first_name} {c.last_name}</div>
                  <div style={{ fontSize: '12px', color: '#8b95a8' }}>{c.email}</div>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '14px' }}>{c.company || '-'}</td>
                <td style={{ padding: '12px 16px', fontSize: '14px' }}>{c.city ? `${c.city}, ${c.state}` : '-'}</td>
                <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                  <span style={{ color: getScoreColor(c.lead_score), fontWeight: '600' }}>{c.lead_score?.toFixed(0)}</span>
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                  <span style={{ color: getScoreColor(c.health_score), fontWeight: '600' }}>{c.health_score?.toFixed(0)}</span>
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                  <button onClick={e => { e.stopPropagation(); setEditing(c); }} style={{ background: 'none', border: 'none', color: '#8b95a8', cursor: 'pointer', marginRight: '8px' }}>
                    <Edit2 size={14} />
                  </button>
                  <button onClick={e => { e.stopPropagation(); handleDelete(c.id); }} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Contact Detail Modal */}
      {selectedContact && (
        <Modal onClose={() => setSelectedContact(null)} title={`${selectedContact.first_name} ${selectedContact.last_name}`}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <InfoItem label="Email" value={selectedContact.email} />
            <InfoItem label="Phone" value={selectedContact.phone || '-'} />
            <InfoItem label="Company" value={selectedContact.company || '-'} />
            <InfoItem label="Industry" value={selectedContact.industry || '-'} />
            <InfoItem label="City" value={selectedContact.city || '-'} />
            <InfoItem label="State" value={selectedContact.state || '-'} />
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <div style={{ textAlign: 'center', padding: '12px', background: '#131b2e', borderRadius: '6px' }}>
              <div style={{ fontSize: '12px', color: '#8b95a8' }}>Lead Score</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: getScoreColor(selectedContact.lead_score) }}>{selectedContact.lead_score?.toFixed(0)}</div>
            </div>
            <div style={{ textAlign: 'center', padding: '12px', background: '#131b2e', borderRadius: '6px' }}>
              <div style={{ fontSize: '12px', color: '#8b95a8' }}>Health Score</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: getScoreColor(selectedContact.health_score) }}>{selectedContact.health_score?.toFixed(0)}</div>
            </div>
            <div style={{ textAlign: 'center', padding: '12px', background: '#131b2e', borderRadius: '6px' }}>
              <div style={{ fontSize: '12px', color: '#8b95a8' }}>Interactions</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{selectedContact.total_interactions}</div>
            </div>
          </div>

          {/* Add Interaction */}
          <h4 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: '600' }}>Log Interaction</h4>
          <form onSubmit={handleAddInteraction} style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
            <select 
              value={newInteraction.type} 
              onChange={e => setNewInteraction({...newInteraction, type: e.target.value})}
              style={{ background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }}
            >
              <option value="email">Email</option>
              <option value="call">Call</option>
              <option value="meeting">Meeting</option>
              <option value="note">Note</option>
              <option value="sms">SMS</option>
            </select>
            <input
              type="text"
              placeholder="Summary..."
              value={newInteraction.summary}
              onChange={e => setNewInteraction({...newInteraction, summary: e.target.value})}
              style={{ flex: 1, background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }}
            />
            <button type="submit" style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
              Log
            </button>
          </form>
        </Modal>
      )}

      {/* Create/Edit Form Modal */}
      {(showForm || editing) && (
        <Modal onClose={() => { setShowForm(false); setEditing(null); }} title={editing ? 'Edit Contact' : 'New Contact'}>
          <form onSubmit={editing ? handleUpdate : handleCreate}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <FormField name="first_name" label="First Name" defaultValue={editing?.first_name} required />
              <FormField name="last_name" label="Last Name" defaultValue={editing?.last_name} required />
              <FormField name="email" label="Email" type="email" defaultValue={editing?.email} required />
              <FormField name="phone" label="Phone" defaultValue={editing?.phone} />
              <FormField name="company" label="Company" defaultValue={editing?.company} />
              <FormField name="industry" label="Industry" defaultValue={editing?.industry} />
              <FormField name="city" label="City" defaultValue={editing?.city} />
              <FormField name="state" label="State" defaultValue={editing?.state} />
            </div>
            <FormField name="notes" label="Notes" textarea defaultValue={editing?.notes} />
            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button type="button" onClick={() => { setShowForm(false); setEditing(null); }} style={{ background: '#1a2340', color: '#e0e6ed', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              <button type="submit" style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>{editing ? 'Update' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '2px' }}>{label}</div>
      <div style={{ fontSize: '14px', fontWeight: '500' }}>{value}</div>
    </div>
  );
}

function FormField({ name, label, type = 'text', textarea, defaultValue, required }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>{label}{required && ' *'}</label>
      {textarea ? (
        <textarea name={name} defaultValue={defaultValue} rows="3" style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px', resize: 'vertical' }} />
      ) : (
        <input type={type} name={name} defaultValue={defaultValue} required={required} style={{ width: '100%', background: '#131b2e', border: '1px solid #1a2340', color: '#e0e6ed', padding: '8px', borderRadius: '6px' }} />
      )}
    </div>
  );
}

function Modal({ children, onClose, title }) {
  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100
    }} onClick={onClose}>
      <div style={{
        background: '#0f1525',
        border: '1px solid #1a2340',
        borderRadius: '12px',
        padding: '24px',
        width: '600px',
        maxHeight: '90vh',
        overflowY: 'auto'
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600' }}>{title}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#8b95a8', cursor: 'pointer', fontSize: '20px' }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}
