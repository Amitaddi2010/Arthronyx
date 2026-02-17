import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

const STUDY_TYPES = ['Meta-Analysis', 'RCT', 'Cohort', 'Case-Control', 'Case Series', 'Guidelines'];
const YEAR_RANGES = [
    { label: 'All Years', value: '' },
    { label: 'Last 2 Years', value: '2' },
    { label: 'Last 5 Years', value: '5' },
    { label: 'Last 10 Years', value: '10' },
];

const PIPELINE_STEPS = [
    { key: 'safety', label: 'Safety screening' },
    { key: 'bm25', label: 'Keyword retrieval (BM25)' },
    { key: 'dense', label: 'Semantic embedding search' },
    { key: 'rerank', label: 'Cross-encoder re-ranking' },
    { key: 'stance', label: 'Stance classification' },
    { key: 'conflict', label: 'Conflict detection' },
    { key: 'synthesis', label: 'LLM synthesis generation' },
    { key: 'validation', label: 'Citation validation' },
];

const EXAMPLE_QUERIES = [
    { text: 'What is the best surgical approach for displaced femoral neck fractures in elderly patients?', tag: 'Hip' },
    { text: 'Evidence for platelet-rich plasma in rotator cuff repair', tag: 'Shoulder' },
    { text: 'Compare cemented vs cementless total hip arthroplasty outcomes', tag: 'Arthroplasty' },
    { text: 'ACL reconstruction graft choice: autograft vs allograft', tag: 'Knee' },
];

export default function QueryPage({ onResults, initialQuery = '' }) {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [query, setQuery] = useState(initialQuery);
    const [loading, setLoading] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [selectedTypes, setSelectedTypes] = useState([]);
    const [yearRange, setYearRange] = useState('');
    const [error, setError] = useState(null);
    const [pipelineStep, setPipelineStep] = useState(-1);
    const [healthOk, setHealthOk] = useState(null);

    useEffect(() => {
        api.checkHealth()
            .then(() => setHealthOk(true))
            .catch(() => setHealthOk(false));
    }, []);

    const toggleType = (type) => {
        setSelectedTypes(prev =>
            prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
        );
    };

    const handleSubmit = async (e) => {
        e?.preventDefault();

        if (!user) {
            navigate('/signin');
            return;
        }

        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setPipelineStep(0);

        const stepInterval = setInterval(() => {
            setPipelineStep(prev => {
                if (prev >= PIPELINE_STEPS.length - 1) {
                    clearInterval(stepInterval);
                    return prev;
                }
                return prev + 1;
            });
        }, 1800);

        try {
            const payload = {
                query: query.trim(),
                ...(selectedTypes.length > 0 && { study_types: selectedTypes }),
                ...(yearRange && { year_range: parseInt(yearRange) }),
            };
            const res = await api.queryEvidence(payload);
            clearInterval(stepInterval);
            setPipelineStep(PIPELINE_STEPS.length);

            // Check if API returned a result or just an error message
            if (res.data.result) {
                setTimeout(() => onResults(res.data.result, query.trim()), 400);
            } else {
                setError(res.data.error || 'No relevant documents found. Try a different query.');
                setLoading(false);
                setPipelineStep(-1);
            }
        } catch (err) {
            clearInterval(stepInterval);
            setError(err.response?.data?.detail || err.response?.data?.error || err.message || 'An error occurred');
            setLoading(false);
            setPipelineStep(-1);
        }
    };

    return (
        <div className="relative" style={{ minHeight: 'calc(100vh - 56px)' }}>

            {/* ── Hero Section ───────────────────────────────────── */}
            <section className="pt-12 pb-6 md:pt-20 md:pb-8">
                <div className="page-container text-center">

                    {/* Headline */}
                    <div className="animate-fade-up">
                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight mb-3"
                            style={{
                                background: 'linear-gradient(135deg, #f1f5f9 0%, #93c5fd 50%, #2dd4bf 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                            }}>
                            Evidence Intelligence
                        </h1>
                        <p className="text-base md:text-lg max-w-2xl mx-auto"
                            style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                            Citation-grounded, conflict-aware evidence synthesis
                            <br className="hidden sm:block" /> for orthopedic medicine
                        </p>
                    </div>

                    {/* Pipeline chips */}
                    <div className="flex items-center justify-center flex-wrap gap-1.5 mt-4 mb-8 animate-fade-up stagger-2"
                        style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                        {['Hybrid Retrieval', 'Cross-Encoder Rerank', 'Conflict Detection', 'LLM Synthesis'].map((step, i) => (
                            <React.Fragment key={step}>
                                {i > 0 && <span style={{ opacity: 0.3 }}>→</span>}
                                <span className="px-2.5 py-1 rounded-full"
                                    style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.12)' }}>
                                    {step}
                                </span>
                            </React.Fragment>
                        ))}
                    </div>

                    {/* ── Search Card ──────────────────────────────────── */}
                    <form onSubmit={handleSubmit} className="max-w-3xl mx-auto animate-fade-up stagger-3">
                        <div className="glass-card-static p-4 md:p-6"
                            style={{ background: 'rgba(17, 24, 39, 0.7)' }}>

                            {/* Search input */}
                            <div className="search-input-wrapper mb-4">
                                <input
                                    className="search-input"
                                    type="text"
                                    placeholder="Ask a clinical question — e.g., 'best fixation for tibial plateau fractures'..."
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    disabled={loading}
                                    autoFocus
                                    style={{ fontSize: '0.95rem' }}
                                />
                                <svg className="search-input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none"
                                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="11" cy="11" r="8" />
                                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                                </svg>
                            </div>

                            {/* Action row */}
                            <div className="flex items-center gap-3">
                                <button type="button" className="btn-ghost" onClick={() => setShowFilters(!showFilters)}>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                        strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="4" y1="6" x2="20" y2="6" />
                                        <line x1="8" y1="12" x2="16" y2="12" />
                                        <line x1="11" y1="18" x2="13" y2="18" />
                                    </svg>
                                    Filters {selectedTypes.length > 0 && (
                                        <span className="ml-0.5 w-4 h-4 rounded-full text-[10px] flex items-center justify-center"
                                            style={{ background: 'var(--color-primary-500)', color: 'white' }}>
                                            {selectedTypes.length}
                                        </span>
                                    )}
                                </button>

                                {/* Health indicator */}
                                {healthOk !== null && (
                                    <div className="flex items-center gap-1.5 text-xs"
                                        style={{ color: 'var(--color-text-muted)' }}>
                                        <div className="w-1.5 h-1.5 rounded-full"
                                            style={{ background: healthOk ? 'var(--color-positive)' : 'var(--color-danger)' }} />
                                        {healthOk ? 'Connected' : 'Offline'}
                                    </div>
                                )}

                                <button type="submit" className={`ml-auto ${!user ? 'btn-secondary' : 'btn-primary'}`}
                                    disabled={loading || (!query.trim() && user === null)}> {/* Allow clicking if not logged in even if query empty, to go to signin? No, keep consistency. But if query is empty, usually disabled. If not logged in, maybe always enabled to let them go to signin? Let's stick to standard behavior: disabled if empty. */}
                                    {loading ? (
                                        <>
                                            <div className="spinner" style={{ width: 16, height: 16, borderWidth: '2px' }} />
                                            Analyzing...
                                        </>
                                    ) : !user ? (
                                        <>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                            </svg>
                                            Sign in to Synthesize
                                        </>
                                    ) : (
                                        <>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                                            </svg>
                                            Synthesize Evidence
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Filters Panel */}
                            {showFilters && (
                                <div className="mt-4 pt-4 border-t animate-fade-up"
                                    style={{ borderColor: 'var(--color-border)', textAlign: 'left' }}>
                                    <div className="mb-4">
                                        <label className="text-xs font-semibold uppercase tracking-wider mb-2 block"
                                            style={{ color: 'var(--color-text-muted)' }}>Study Type</label>
                                        <div className="flex flex-wrap gap-2">
                                            {STUDY_TYPES.map(type => (
                                                <button key={type} type="button"
                                                    className={`chip ${selectedTypes.includes(type) ? 'active' : ''}`}
                                                    onClick={() => toggleType(type)}>
                                                    {type}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-semibold uppercase tracking-wider mb-2 block"
                                            style={{ color: 'var(--color-text-muted)' }}>Year Range</label>
                                        <div className="flex flex-wrap gap-2">
                                            {YEAR_RANGES.map(yr => (
                                                <button key={yr.value} type="button"
                                                    className={`chip ${yearRange === yr.value ? 'active' : ''}`}
                                                    onClick={() => setYearRange(yr.value)}>
                                                    {yr.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </form>

                    {/* Error */}
                    {error && (
                        <div className="mt-4 max-w-3xl mx-auto p-4 rounded-xl animate-fade-up text-left"
                            style={{
                                background: 'var(--color-danger-bg)',
                                border: '1px solid var(--color-danger-border)',
                                color: '#fca5a5',
                                fontSize: '0.85rem'
                            }}>
                            <strong>Error:</strong> {error}
                        </div>
                    )}
                </div>
            </section>

            {/* ── Pipeline Progress ────────────────────────────────── */}
            {loading && (
                <section className="pb-8">
                    <div className="page-container max-w-md mx-auto">
                        <div className="glass-card-static p-5 animate-fade-up">
                            <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-secondary)' }}>
                                Evidence Pipeline
                            </h3>
                            <div className="space-y-1">
                                {PIPELINE_STEPS.map((step, i) => (
                                    <div key={step.key}
                                        className={`pipeline-step ${i === pipelineStep ? 'active' : ''} ${i < pipelineStep ? 'complete' : ''}`}>
                                        <div className={`pipeline-dot ${i < pipelineStep ? 'complete' : i === pipelineStep ? 'active' : 'pending'}`} />
                                        <span className="text-sm"
                                            style={{ color: i <= pipelineStep ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>
                                            {step.label}
                                        </span>
                                        {i === pipelineStep && (
                                            <div className="spinner ml-auto" style={{ width: 14, height: 14, borderWidth: '1.5px' }} />
                                        )}
                                        {i < pipelineStep && (
                                            <svg className="ml-auto" width="14" height="14" viewBox="0 0 24 24" fill="none"
                                                stroke="var(--color-positive)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>
            )}

            {/* ── Example Queries ──────────────────────────────────── */}
            {!loading && (
                <section className="pb-6">
                    <div className="page-container max-w-3xl mx-auto">
                        <h3 className="text-xs font-semibold uppercase tracking-widest mb-4 text-center animate-fade-up stagger-4"
                            style={{ color: 'var(--color-text-muted)', letterSpacing: '0.12em' }}>
                            Try an Example
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {EXAMPLE_QUERIES.map((q, i) => (
                                <button key={i}
                                    className={`group evidence-card p-4 text-left cursor-pointer animate-card-enter stagger-${i + 4}`}
                                    onClick={() => setQuery(q.text)}>
                                    <div className="flex items-start gap-3">
                                        <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 transition-all"
                                            style={{
                                                background: 'rgba(59,130,246,0.08)',
                                                border: '1px solid rgba(59,130,246,0.15)',
                                            }}>
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                                                stroke="var(--color-primary-400)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <circle cx="11" cy="11" r="8" />
                                                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                                            </svg>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <span className="text-sm leading-snug block"
                                                style={{ color: 'var(--color-text-secondary)' }}>
                                                {q.text}
                                            </span>
                                            <span className="inline-block mt-2 text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full"
                                                style={{
                                                    background: 'rgba(45,212,191,0.08)',
                                                    color: 'var(--color-teal-400)',
                                                    border: '1px solid rgba(45,212,191,0.15)',
                                                }}>
                                                {q.tag}
                                            </span>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </section>
            )}

            {/* ── Feature Grid ─────────────────────────────────────── */}
            {!loading && (
                <section className="pb-12">
                    <div className="page-container max-w-3xl mx-auto">
                        <div className="section-divider" />
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 animate-fade-up stagger-8">
                            {[
                                {
                                    icon: (
                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary-400)"
                                            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <circle cx="12" cy="12" r="10" />
                                            <path d="M12 6v6l4 2" />
                                        </svg>
                                    ),
                                    title: 'Hybrid Retrieval',
                                    desc: 'BM25 + dense embedding + cross-encoder reranking for comprehensive coverage',
                                },
                                {
                                    icon: (
                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--color-teal-400)"
                                            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
                                            <path d="M13 13l6 6" />
                                        </svg>
                                    ),
                                    title: 'Conflict Detection',
                                    desc: 'Stance classification with outcome clustering and resolution analysis',
                                },
                                {
                                    icon: (
                                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--color-citation)"
                                            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                                        </svg>
                                    ),
                                    title: 'Citation Grounded',
                                    desc: 'Every claim validated against source DOIs with full traceability',
                                },
                            ].map((feat, i) => (
                                <div key={i} className="glass-card-static p-5 text-center">
                                    <div className="w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-3"
                                        style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.1)' }}>
                                        {feat.icon}
                                    </div>
                                    <div className="text-sm font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>
                                        {feat.title}
                                    </div>
                                    <div className="text-xs leading-relaxed" style={{ color: 'var(--color-text-muted)' }}>
                                        {feat.desc}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
