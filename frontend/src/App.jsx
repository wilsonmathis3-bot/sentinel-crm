import React from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Contacts from './pages/Contacts';
import Deals from './pages/Deals';
import Tasks from './pages/Tasks';
import Agents from './pages/Agents';
import NLQuery from './pages/NLQuery';
import Creator from './pages/Creator';
import { Shield, Users, Target, CheckSquare, Brain, MessageSquare, LogOut, Sparkles } from 'lucide-react';

function AppLayout() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <nav style={{
        width: '220px',
        background: '#0f1525',
        borderRight: '1px solid #1a2340',
        padding: '20px 0',
        position: 'fixed',
        height: '100vh',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ padding: '0 20px 20px', borderBottom: '1px solid #1a2340' }}>
          <h1 style={{ fontSize: '20px', fontWeight: 'bold', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={24} />
            Sentinel CRM
          </h1>
        </div>
        
        <div style={{ flex: 1 }}>
          <NavItem to="/" icon={<Target size={18} />} label="Dashboard" />
          <NavItem to="/contacts" icon={<Users size={18} />} label="Contacts" />
          <NavItem to="/deals" icon={<Target size={18} />} label="Deals" />
          <NavItem to="/tasks" icon={<CheckSquare size={18} />} label="Tasks" />
          <NavItem to="/agents" icon={<Brain size={18} />} label="AI Agents" />
          <NavItem to="/creator" icon={<Sparkles size={18} />} label="Creator" />
          <NavItem to="/query" icon={<MessageSquare size={18} />} label="NL Query" />
        </div>

        <div style={{ padding: '16px 20px', borderTop: '1px solid #1a2340' }}>
          <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '8px' }}>
            {user?.email}
          </div>
          <button onClick={handleLogout} style={{
            width: '100%',
            background: 'transparent',
            border: '1px solid #1a2340',
            color: '#ef4444',
            padding: '8px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px'
          }}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ marginLeft: '220px', flex: 1, padding: '30px', maxWidth: 'calc(100% - 220px)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/contacts" element={<Contacts />} />
          <Route path="/deals" element={<Deals />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/creator" element={<Creator />} />
          <Route path="/query" element={<NLQuery />} />
        </Routes>
      </main>
    </div>
  );
}

function NavItem({ to, icon, label }) {
  const isActive = window.location.pathname === to;
  return (
    <Link to={to} style={{
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '12px 20px',
      color: isActive ? '#3b82f6' : '#8b95a8',
      textDecoration: 'none',
      fontSize: '14px',
      transition: 'all 0.2s',
      background: isActive ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
      borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent'
    }}>
      {icon}
      {label}
    </Link>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
