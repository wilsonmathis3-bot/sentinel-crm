import React, { useState } from 'react';
import { nlQuery } from '../api';
import { MessageSquare, Send, Database, Search } from 'lucide-react';

export default function NLQuery() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const r = await nlQuery(query);
      setResult(r.data);
    } catch (e) {
      setResult({ sql: '', results: [], summary: 'Error: ' + e.message });
    }
    setLoading(false);
  };

  const examples = [
    "Show me prospects in New York who haven't been contacted in 30 days",
    "Find high value deals in negotiation",
    "Who are my most responsive contacts?",
    "Show contacts with health score below 40",
    "List all tasks due this week"
  ];

  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <MessageSquare size={24} /> Natural Language Query
      </h2>

      <p style={{ color: '#8b95a8', marginBottom: '20px', fontSize: '14px' }}>
        Ask questions about your contacts, deals, and tasks in plain English. The system converts your query to SQL and returns results.
      </p>

      {/* Query Input */}
      <form onSubmit={handleSubmit} style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Ask something like 'Show me hot leads in San Francisco'..."
            style={{
              flex: 1,
              padding: '12px 16px',
              background: '#0f1525',
              border: '1px solid #1a2340',
              borderRadius: '8px',
              color: '#e0e6ed',
              fontSize: '14px'
            }}
          />
          <button type="submit" disabled={loading} style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '12px 20px',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px'
          }}>
            {loading ? 'Querying...' : <><Send size={16} /> Query</>}
          </button>
        </div>
      </form>

      {/* Examples */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '8px', textTransform: 'uppercase' }}>Try these examples</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {examples.map((ex, i) => (
            <button key={i} onClick={() => setQuery(ex)} style={{
              padding: '6px 12px',
              background: '#131b2e',
              border: '1px solid #1a2340',
              borderRadius: '6px',
              color: '#8b95a8',
              fontSize: '12px',
              cursor: 'pointer'
            }}>
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div>
          {/* Summary */}
          <div style={{
            background: '#0f1525',
            border: '1px solid #1a2340',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '16px'
          }}>
            <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>{result.summary}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#8b95a8' }}>
              <Database size={12} />
              <code style={{ background: '#131b2e', padding: '2px 6px', borderRadius: '4px' }}>{result.sql}</code>
            </div>
          </div>

          {/* Results Table */}
          {result.results.length > 0 && (
            <div style={{
              background: '#0f1525',
              border: '1px solid #1a2340',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#131b2e' }}>
                    {Object.keys(result.results[0]).map(key => (
                      <th key={key} style={{
                        padding: '10px 12px',
                        textAlign: 'left',
                        fontSize: '11px',
                        textTransform: 'uppercase',
                        color: '#8b95a8',
                        fontWeight: '500'
                      }}>
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((row, i) => (
                    <tr key={i} style={{ borderTop: '1px solid #1a2340' }}>
                      {Object.values(row).map((val, j) => (
                        <td key={j} style={{ padding: '10px 12px', fontSize: '13px' }}>
                          {typeof val === 'number' ? val.toFixed ? val.toFixed(2) : val : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
