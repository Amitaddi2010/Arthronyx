
import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import NeuralBackground from './NeuralBackground';
import { useAuth } from '../context/AuthContext';

function Layout({ engineStatus }) {
    const { user, logout } = useAuth();
    const location = useLocation();

    return (
        <div className="min-h-screen bg-grid relative flex flex-col">
            {/* Animated Background */}
            <NeuralBackground />

            {/* Top Navigation */}
            <nav className="sticky top-0 z-50 border-b border-white/[0.06]"
                style={{ background: 'rgba(6, 10, 20, 0.85)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)' }}>
                <div className="page-container-wide flex items-center justify-between h-14">

                    {/* Brand */}
                    <Link to="/" className="flex items-center gap-3 cursor-pointer hover:opacity-90 transition-opacity">
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
                    </Link>

                    {/* Right Side Actions */}
                    <div className="flex items-center gap-4">

                        {/* Engine Status Badge - Only show on home/results */}
                        {engineStatus !== undefined && (
                            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
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
                                    width: 7, height: 7, borderRadius: '50%',
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
                        )}

                        <div className="h-6 w-[1px] bg-white/10 hidden sm:block"></div>

                        {/* Auth Buttons */}
                        {user ? (
                            <div className="flex items-center gap-3">
                                <span className="text-sm text-gray-400 hidden sm:inline">Hello, <span className="text-white font-medium">{(user.full_name || user.email || 'User').split(' ')[0]}</span></span>
                                <button
                                    onClick={logout}
                                    className="text-xs font-medium text-gray-400 hover:text-white transition-colors"
                                >
                                    Sign Out
                                </button>
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-lg shadow-blue-500/20">
                                    {(user.full_name || user.email || 'U').charAt(0).toUpperCase()}
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3">
                                <Link to="/signin" className={`text-sm font-medium transition-colors ${location.pathname === '/signin' ? 'text-white' : 'text-gray-400 hover:text-white'}`}>
                                    Sign In
                                </Link>
                                <Link to="/signup" className="px-4 py-1.5 rounded-lg text-sm font-medium bg-white/10 hover:bg-white/20 text-white transition-all border border-white/10">
                                    Sign Up
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </nav>

            {/* Page Content */}
            <main className="flex-1 flex flex-col relative z-0">
                <Outlet />
            </main>
        </div>
    );
}

export default Layout;
