import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { login, register, passkeyRegisterStart, passkeyRegisterVerify, passkeyAuthStart, passkeyAuthVerify } from '../api';
import { Shield, Mail, Lock, Key, UserPlus, LogIn } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login({ email, password });
      authLogin(res.data.access_token, res.data.user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    }
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register({ email, password, full_name: fullName });
      // Auto login after register
      const res = await login({ email, password });
      authLogin(res.data.access_token, res.data.user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
    setLoading(false);
  };

  const handlePasskeyLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const startRes = await passkeyAuthStart({});
      const options = startRes.data;

      const credential = await navigator.credentials.get({
        publicKey: {
          challenge: Uint8Array.from(atob(options.challenge.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0)),
          allowCredentials: options.allowCredentials?.map(c => ({
            id: Uint8Array.from(atob(c.id.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0)),
            type: c.type
          })) || [],
          rpId: options.rpId,
          userVerification: options.userVerification,
          timeout: options.timeout,
        }
      });

      if (!credential) {
        throw new Error('No credential selected');
      }

      const authData = {
        credential_id: Array.from(new Uint8Array(credential.rawId)).map(b => b.toString(16).padStart(2, '0')).join(''),
        response: {
          challenge_hex: options.challenge_hex,
          authenticatorData: Array.from(new Uint8Array(credential.response.authenticatorData)).map(b => b.toString(16).padStart(2, '0')).join(''),
          clientDataJSON: Array.from(new Uint8Array(credential.response.clientDataJSON)).map(b => b.toString(16).padStart(2, '0')).join(''),
          signature: Array.from(new Uint8Array(credential.response.signature)).map(b => b.toString(16).padStart(2, '0')).join(''),
          userHandle: credential.response.userHandle ? Array.from(new Uint8Array(credential.response.userHandle)).map(b => b.toString(16).padStart(2, '0')).join('') : null,
        }
      };

      const verifyRes = await passkeyAuthVerify(authData);
      authLogin(verifyRes.data.access_token, verifyRes.data.user);
      navigate('/');
    } catch (err) {
      console.error('Passkey error:', err);
      setError(err.message || 'Passkey authentication failed');
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0a0e1a'
    }}>
      <div style={{
        width: '400px',
        background: '#0f1525',
        border: '1px solid #1a2340',
        borderRadius: '12px',
        padding: '32px'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: '#3b82f620',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px'
          }}>
            <Shield size={24} color="#3b82f6" />
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>Sentinel CRM</h1>
          <p style={{ fontSize: '14px', color: '#8b95a8', marginTop: '4px' }}>
            {isRegister ? 'Create your account' : 'Sign in to continue'}
          </p>
        </div>

        {error && (
          <div style={{
            background: '#ef444420',
            border: '1px solid #ef444440',
            color: '#ef4444',
            padding: '10px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '16px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={isRegister ? handleRegister : handleEmailLogin}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {isRegister && (
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Full Name</label>
                <div style={{ position: 'relative' }}>
                  <UserPlus size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b95a8' }} />
                  <input
                    type="text"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    placeholder="John Doe"
                    required
                    style={{
                      width: '100%',
                      padding: '10px 12px 10px 36px',
                      background: '#131b2e',
                      border: '1px solid #1a2340',
                      borderRadius: '6px',
                      color: '#e0e6ed',
                      fontSize: '14px'
                    }}
                  />
                </div>
              </div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Email</label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b95a8' }} />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  style={{
                    width: '100%',
                    padding: '10px 12px 10px 36px',
                    background: '#131b2e',
                    border: '1px solid #1a2340',
                    borderRadius: '6px',
                    color: '#e0e6ed',
                    fontSize: '14px'
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#8b95a8', marginBottom: '4px' }}>Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b95a8' }} />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%',
                    padding: '10px 12px 10px 36px',
                    background: '#131b2e',
                    border: '1px solid #1a2340',
                    borderRadius: '6px',
                    color: '#e0e6ed',
                    fontSize: '14px'
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                marginTop: '4px'
              }}
            >
              {isRegister ? <UserPlus size={16} /> : <LogIn size={16} />}
              {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
            </button>
          </div>
        </form>

        <div style={{ margin: '16px 0', textAlign: 'center' }}>
          <span style={{ color: '#8b95a8', fontSize: '12px' }}>OR</span>
        </div>

        <button
          onClick={handlePasskeyLogin}
          disabled={loading}
          style={{
            width: '100%',
            background: '#131b2e',
            border: '1px solid #1a2340',
            color: '#e0e6ed',
            padding: '12px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px'
          }}
        >
          <Key size={16} color="#10b981" />
          Sign in with Passkey
        </button>

        <div style={{ textAlign: 'center', marginTop: '16px' }}>
          <button
            onClick={() => { setIsRegister(!isRegister); setError(''); }}
            style={{
              background: 'none',
              border: 'none',
              color: '#3b82f6',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Create one"}
          </button>
        </div>
      </div>
    </div>
  );
}
