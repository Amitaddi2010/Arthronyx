import React, { useState, useEffect } from 'react';
import QueryPage from './pages/QueryPage';
import ResultsPage from './pages/ResultsPage';
import NeuralBackground from './components/NeuralBackground';
import { api } from './api/client';

function App() {
    const [result, setResult] = useState(null);
    const [queryText, setQueryText] = useState('');
    const [engineStatus, setEngineStatus] = useState(null); // null = checking, true = online, false = offline

    // Poll engine health every 15 seconds
    useEffect(() => {
        const checkHealth = () => {
            api.checkHealth()
                .then(() => setEngineStatus(true))
                .catch(() => setEngineStatus(false));
        };
        checkHealth();
        const interval = setInterval(checkHealth, 15000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-grid relative">
            {/* Animated neural-network particle background */}
            <NeuralBackground />

            {/* Top Navigation */}
            <nav className="sticky top-0 z-50 border-b border-white/[0.06]"
                style={{ background: 'rgba(6, 10, 20, 0.85)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)' }}>
                <div className="page-container-wide flex items-center justify-between h-14">
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => { setResult(null); setQueryText(''); }}>
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                            style={{ background: 'var(--gradient-primary)' }}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                                <path d="M2 17l10 5 10-5" />
                                <path d="M2 12l10 5 10-5" />
                            </svg>
                        </div>
                        <span className="text-base font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
                            Arthronyx
                        </span>
                        <span className="hidden sm:inline-block text-xs font-medium px-2 py-0.5 rounded-full"
                            style={{ background: 'rgba(59,130,246,0.1)', color: 'var(--color-primary-400)', border: '1px solid rgba(59,130,246,0.2)' }}>
                            Evidence Engine
                        </span>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Engine Status Badge */}
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
                            style={{
                                background: engineStatus === null
                                    ? 'rgba(148,163,184,0.08)'
                                    : engineStatus
                                        ? 'rgba(16,185,129,0.08)'
                                        : 'rgba(239,68,68,0.08)',
                                border: `1px solid ${engineStatus === null
                                    ? 'rgba(148,163,184,0.15)'
                                    : engineStatus
                                        ? 'rgba(16,185,129,0.25)'
                                        : 'rgba(239,68,68,0.25)'
                                    }`,
                                color: engineStatus === null
                                    ? 'var(--color-text-muted)'
                                    : engineStatus
                                        ? '#34d399'
                                        : '#f87171',
                            }}>
                            <div style={{
                                width: 7,
                                height: 7,
                                borderRadius: '50%',
                                background: engineStatus === null
                                    ? 'var(--color-text-muted)'
                                    : engineStatus
                                        ? '#10b981'
                                        : '#ef4444',
                                boxShadow: engineStatus
                                    ? '0 0 8px rgba(16,185,129,0.5)'
                                    : engineStatus === false
                                        ? '0 0 8px rgba(239,68,68,0.5)'
                                        : 'none',
                                animation: engineStatus ? 'pulseGlow 2s ease-in-out infinite' : 'none',
                            }} />
                            {engineStatus === null ? 'Checking…' : engineStatus ? 'Engine Online' : 'Engine Offline'}
                        </div>

                        <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
                            className="btn-ghost text-xs hidden sm:inline-flex">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                            </svg>
                            API Docs
                        </a>
                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold"
                            style={{ background: 'var(--gradient-primary)', color: 'white' }}>
                            A
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main>
                {result ? (
                    <ResultsPage
                        result={result}
                        queryText={queryText}
                        onBack={() => setResult(null)}
                        onNewQuery={(q) => { setResult(null); setQueryText(q); }}
                    />
                ) : (
                    <QueryPage
                        onResults={(res, q) => { setResult(res); setQueryText(q); }}
                        initialQuery={queryText}
                    />
                )}
            </main>
        </div>
    );
}

export default App;
