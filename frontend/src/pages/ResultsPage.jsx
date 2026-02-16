import React, { useState, useMemo } from 'react';
import Disclaimer from '../components/Disclaimer';

/* ═══════════════════════════════════════════════════════════════
   Arthronyx — Premium Results Page
   ═══════════════════════════════════════════════════════════════ */

const TABS = [
    { key: 'synthesis', label: 'Synthesis', emoji: '🧬' },
    { key: 'evidence', label: 'Evidence', emoji: '📊' },
    { key: 'conflicts', label: 'Conflicts', emoji: '⚡' },
    { key: 'timeline', label: 'Timeline', emoji: '📅' },
    { key: 'citations', label: 'Citations', emoji: '🔗' },
];

const STANCE_STYLES = {
    'Positive Effect': { color: '#34d399', bg: 'rgba(16,185,129,0.10)', border: 'rgba(16,185,129,0.25)', icon: '▲', label: 'Positive' },
    'Negative Effect': { color: '#f87171', bg: 'rgba(239,68,68,0.10)', border: 'rgba(239,68,68,0.25)', icon: '▼', label: 'Negative' },
    'Mixed': { color: '#fbbf24', bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.25)', icon: '◆', label: 'Mixed' },
    'No Significant Difference': { color: '#94a3b8', bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.15)', icon: '●', label: 'Neutral' },
    'Unknown': { color: '#64748b', bg: 'rgba(100,116,139,0.08)', border: 'rgba(100,116,139,0.15)', icon: '○', label: 'Unknown' },
};

const LEVEL_STYLES = {
    'I': { color: '#34d399', bg: 'rgba(16,185,129,0.12)', label: 'Level I' },
    'II': { color: '#60a5fa', bg: 'rgba(59,130,246,0.12)', label: 'Level II' },
    'III': { color: '#fbbf24', bg: 'rgba(245,158,11,0.12)', label: 'Level III' },
    'IV': { color: '#fb923c', bg: 'rgba(251,146,60,0.12)', label: 'Level IV' },
    'V': { color: '#f87171', bg: 'rgba(239,68,68,0.12)', label: 'Level V' },
};

const SOURCE_STYLES = {
    'PubMed': { color: '#60a5fa', bg: 'rgba(59,130,246,0.08)', icon: '🏥' },
    'OpenAlex': { color: '#a78bfa', bg: 'rgba(167,139,250,0.08)', icon: '🔬' },
    'ClinicalTrials.gov': { color: '#2dd4bf', bg: 'rgba(45,212,191,0.08)', icon: '🧪' },
    'local': { color: '#94a3b8', bg: 'rgba(148,163,184,0.08)', icon: '💾' },
};


export default function ResultsPage({ result, queryText, onBack, onNewQuery }) {
    const [activeTab, setActiveTab] = useState('synthesis');

    if (!result) return null;

    const {
        clinical_question,
        evidence_overview,
        priority_evidence = [],
        conflict_report,
        evidence_synthesis,
        limitations = [],
        final_position,
        disclaimer,
        citations = [],
        validation_passed,
    } = result;

    return (
        <div style={{ minHeight: 'calc(100vh - 56px)' }}>

            {/* ── Hero Header ─────────────────────────── */}
            <div className="animate-fade-in" style={{
                background: 'linear-gradient(180deg, rgba(59,130,246,0.06) 0%, transparent 100%)',
                borderBottom: '1px solid var(--color-border)',
            }}>
                <div className="page-container-wide" style={{ padding: '28px 24px 24px' }}>
                    {/* Back + Validation */}
                    <div className="flex items-center gap-3 mb-4">
                        <button className="btn-ghost text-xs" onClick={onBack}
                            style={{ gap: 6, padding: '6px 14px' }}>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="19" y1="12" x2="5" y2="12" />
                                <polyline points="12 19 5 12 12 5" />
                            </svg>
                            New Query
                        </button>
                        <div className="ml-auto flex items-center gap-2">
                            {validation_passed !== undefined && (
                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
                                    style={{
                                        background: validation_passed ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)',
                                        border: `1px solid ${validation_passed ? 'rgba(16,185,129,0.25)' : 'rgba(245,158,11,0.25)'}`,
                                        color: validation_passed ? '#34d399' : '#fbbf24',
                                    }}>
                                    <div style={{
                                        width: 6, height: 6, borderRadius: '50%',
                                        background: validation_passed ? '#10b981' : '#f59e0b',
                                        boxShadow: `0 0 8px ${validation_passed ? 'rgba(16,185,129,0.4)' : 'rgba(245,158,11,0.4)'}`,
                                    }} />
                                    {validation_passed ? 'Citations Verified' : 'Partial Verification'}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Question Title */}
                    <h1 style={{
                        fontSize: 'clamp(1.2rem, 2.5vw, 1.6rem)',
                        fontWeight: 700,
                        lineHeight: 1.35,
                        color: 'var(--color-text-primary)',
                        letterSpacing: '-0.02em',
                        maxWidth: '50rem',
                    }}>
                        {clinical_question || queryText}
                    </h1>

                    {/* Stats Row */}
                    {evidence_overview && (
                        <div className="flex flex-wrap gap-2 mt-4">
                            <StatPill icon="📑" label="Studies" value={evidence_overview.total_studies} accent />
                            <StatPill icon="📆" label="Years" value={evidence_overview.year_range} />
                            {evidence_overview.type_distribution?.slice(0, 4).map((td, i) => (
                                <StatPill key={i} label={td.study_type} value={td.count} />
                            ))}
                            {conflict_report?.has_conflict && (
                                <StatPill icon="⚡" label="Conflict" value="Detected" danger />
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* ── Tab Bar ─────────────────────────────── */}
            <div className="sticky top-14 z-40" style={{
                background: 'rgba(6,10,20,0.92)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                borderBottom: '1px solid var(--color-border)',
            }}>
                <div className="page-container-wide">
                    <div style={{
                        display: 'flex',
                        gap: 2,
                        padding: '8px 0',
                        overflowX: 'auto',
                    }}>
                        {TABS.map(tab => {
                            const isActive = activeTab === tab.key;
                            const showDot = tab.key === 'conflicts' && conflict_report?.has_conflict;
                            return (
                                <button key={tab.key}
                                    onClick={() => setActiveTab(tab.key)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 7,
                                        padding: '9px 18px',
                                        fontSize: '0.82rem',
                                        fontWeight: isActive ? 600 : 500,
                                        color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                                        background: isActive ? 'rgba(59,130,246,0.08)' : 'transparent',
                                        border: isActive ? '1px solid rgba(59,130,246,0.2)' : '1px solid transparent',
                                        borderRadius: 8,
                                        cursor: 'pointer',
                                        whiteSpace: 'nowrap',
                                        transition: 'all 200ms ease',
                                        position: 'relative',
                                    }}>
                                    <span style={{ fontSize: '0.9rem' }}>{tab.emoji}</span>
                                    {tab.label}
                                    {showDot && (
                                        <span style={{
                                            width: 6, height: 6, borderRadius: '50%',
                                            background: '#ef4444',
                                            boxShadow: '0 0 6px rgba(239,68,68,0.5)',
                                        }} />
                                    )}
                                    {isActive && (
                                        <div style={{
                                            position: 'absolute', bottom: -1, left: '20%', right: '20%',
                                            height: 2, borderRadius: 1,
                                            background: 'var(--gradient-primary)',
                                        }} />
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* ── Tab Content ─────────────────────────── */}
            <div className="page-container-wide" style={{ padding: '32px 24px 48px' }}>
                {activeTab === 'synthesis' && (
                    <SynthesisTab
                        synthesis={evidence_synthesis}
                        limitations={limitations}
                        finalPosition={final_position}
                        disclaimer={disclaimer}
                    />
                )}
                {activeTab === 'evidence' && (
                    <EvidenceTab evidence={priority_evidence} />
                )}
                {activeTab === 'conflicts' && (
                    <ConflictsTab conflictReport={conflict_report} />
                )}
                {activeTab === 'timeline' && (
                    <TimelineTab evidence={priority_evidence} citations={citations} />
                )}
                {activeTab === 'citations' && (
                    <CitationsTab citations={citations} />
                )}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   SHARED COMPONENTS
   ═══════════════════════════════════════════════════════════════ */

function StatPill({ icon, label, value, accent, danger }) {
    return (
        <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '5px 12px', borderRadius: 100, fontSize: '0.75rem', fontWeight: 500,
            background: danger ? 'rgba(239,68,68,0.08)' : accent ? 'rgba(59,130,246,0.08)' : 'rgba(255,255,255,0.03)',
            border: `1px solid ${danger ? 'rgba(239,68,68,0.2)' : accent ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.06)'}`,
            color: danger ? '#f87171' : accent ? '#60a5fa' : 'var(--color-text-secondary)',
        }}>
            {icon && <span style={{ fontSize: '0.85rem' }}>{icon}</span>}
            <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
            <span className="mono" style={{ fontWeight: 600, color: danger ? '#f87171' : accent ? '#93c5fd' : 'var(--color-text-primary)' }}>
                {value ?? '—'}
            </span>
        </div>
    );
}

function SectionCard({ children, style, className = '' }) {
    return (
        <div className={className} style={{
            background: 'rgba(17,24,39,0.6)',
            border: '1px solid rgba(59,130,246,0.08)',
            borderRadius: 16,
            backdropFilter: 'blur(12px)',
            ...style,
        }}>
            {children}
        </div>
    );
}

function SectionTitle({ emoji, title, subtitle }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{
                width: 36, height: 36, borderRadius: 10,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'rgba(59,130,246,0.08)',
                border: '1px solid rgba(59,130,246,0.15)',
                fontSize: '1.1rem',
            }}>
                {emoji}
            </div>
            <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)', margin: 0 }}>
                    {title}
                </h3>
                {subtitle && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: 0 }}>{subtitle}</p>
                )}
            </div>
        </div>
    );
}

function EmptyState({ emoji, title, description }) {
    return (
        <div className="animate-fade-up" style={{ textAlign: 'center', padding: '64px 24px' }}>
            <div style={{ fontSize: '3rem', marginBottom: 12 }}>{emoji}</div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 6 }}>
                {title}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', maxWidth: 320, margin: '0 auto' }}>
                {description}
            </p>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   SYNTHESIS TAB
   ═══════════════════════════════════════════════════════════════ */

function SynthesisTab({ synthesis, limitations, finalPosition, disclaimer }) {
    return (
        <div style={{ maxWidth: '52rem' }} className="animate-fade-up">

            {/* Main Synthesis */}
            <SectionTitle emoji="🧬" title="Evidence Synthesis" subtitle="AI-generated analysis of retrieved studies" />
            <SectionCard style={{ padding: '28px 28px', marginBottom: 32 }}>
                {synthesis ? (
                    <div style={{
                        color: 'var(--color-text-secondary)',
                        fontSize: '0.9rem',
                        lineHeight: 1.85,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                    }}>
                        {synthesis}
                    </div>
                ) : (
                    <div style={{
                        textAlign: 'center', padding: '32px 0',
                        color: 'var(--color-text-muted)', fontSize: '0.9rem',
                    }}>
                        No synthesis generated for this query.
                    </div>
                )}
            </SectionCard>

            {/* Limitations */}
            {limitations.length > 0 && (
                <>
                    <SectionTitle emoji="⚠️" title="Limitations" subtitle={`${limitations.length} limitation(s) identified`} />
                    <SectionCard style={{ padding: '20px 24px', marginBottom: 32 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {limitations.map((lim, i) => (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'flex-start', gap: 12,
                                    padding: '10px 14px', borderRadius: 10,
                                    background: 'rgba(245,158,11,0.04)',
                                    border: '1px solid rgba(245,158,11,0.08)',
                                }}>
                                    <div style={{
                                        width: 20, height: 20, borderRadius: 6,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        background: 'rgba(245,158,11,0.1)', fontSize: '0.65rem', fontWeight: 700,
                                        color: '#fbbf24', flexShrink: 0, marginTop: 1,
                                    }}>{i + 1}</div>
                                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                                        {lim}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </SectionCard>
                </>
            )}

            {/* Final Position */}
            {finalPosition && (
                <>
                    <SectionTitle emoji="🎯" title="Final Evidence Position" subtitle="Conclusive stance based on available evidence" />
                    <div className="animate-fade-up" style={{
                        padding: '24px 28px', borderRadius: 16, marginBottom: 32,
                        background: 'linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(45,212,191,0.05) 100%)',
                        border: '1px solid rgba(59,130,246,0.2)',
                        boxShadow: '0 0 30px rgba(59,130,246,0.08)',
                    }}>
                        <p style={{
                            fontSize: '0.92rem', lineHeight: 1.8,
                            color: 'var(--color-text-primary)', fontWeight: 400,
                        }}>
                            {finalPosition}
                        </p>
                    </div>
                </>
            )}

            {/* Disclaimer */}
            <Disclaimer text={disclaimer} />
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   EVIDENCE TAB
   ═══════════════════════════════════════════════════════════════ */

function EvidenceTab({ evidence }) {
    if (!evidence || evidence.length === 0) {
        return <EmptyState emoji="📄" title="No Evidence Retrieved" description="Run the ingestion pipeline to populate the evidence corpus." />;
    }

    return (
        <div className="animate-fade-up">
            <SectionTitle emoji="📊" title="Priority Evidence" subtitle={`Top ${evidence.length} studies ranked by relevance`} />
            <div style={{ display: 'grid', gap: 14, gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))' }}>
                {evidence.map((doc, i) => (
                    <EvidenceCardRedesigned key={i} doc={doc} index={i} />
                ))}
            </div>
        </div>
    );
}

function EvidenceCardRedesigned({ doc, index }) {
    const level = doc.evidence_level || 'N/A';
    const levelStyle = LEVEL_STYLES[level] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', label: `Level ${level}` };
    const stance = doc.outcome || doc.outcome_stance || 'Unknown';
    const stanceStyle = STANCE_STYLES[stance] || STANCE_STYLES['Unknown'];
    const score = parseFloat(doc.final_score || 0);
    const source = doc.source || 'local';
    const srcStyle = SOURCE_STYLES[source] || SOURCE_STYLES['local'];

    return (
        <SectionCard className={`animate-card-enter stagger-${Math.min(index + 1, 8)}`}
            style={{ padding: 0, overflow: 'hidden', transition: 'all 250ms ease', cursor: 'default' }}>

            {/* Top accent bar */}
            <div style={{
                height: 3,
                background: `linear-gradient(90deg, ${stanceStyle.color}80, ${stanceStyle.color}20)`,
            }} />

            <div style={{ padding: '18px 20px' }}>
                {/* Title */}
                <h4 style={{
                    fontSize: '0.88rem', fontWeight: 600, lineHeight: 1.45,
                    color: 'var(--color-text-primary)', marginBottom: 10,
                    display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
                }}>
                    {doc.title || 'Untitled Study'}
                </h4>

                {/* Badge Row */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
                    {doc.study_type && <MicroBadge label={doc.study_type} color="#60a5fa" />}
                    <MicroBadge label={levelStyle.label} color={levelStyle.color} bg={levelStyle.bg} />
                    <MicroBadge label={stanceStyle.label} color={stanceStyle.color} bg={stanceStyle.bg} icon={stanceStyle.icon} />
                    <MicroBadge label={source} color={srcStyle.color} bg={srcStyle.bg} icon={srcStyle.icon} />
                    {doc.year && <MicroBadge label={String(doc.year)} color="var(--color-text-muted)" />}
                </div>

                {/* Score Bar */}
                <div style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>Relevance</span>
                        <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 600, color: '#60a5fa' }}>
                            {score.toFixed(4)}
                        </span>
                    </div>
                    <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.05)' }}>
                        <div style={{
                            height: '100%', borderRadius: 2,
                            width: `${Math.min(score * 100, 100)}%`,
                            background: 'linear-gradient(90deg, #3b82f6, #2dd4bf)',
                            transition: 'width 0.8s cubic-bezier(0.34,1.56,0.64,1)',
                        }} />
                    </div>
                </div>

                {/* DOI */}
                {doc.doi && (
                    <a href={`https://doi.org/${doc.doi}`} target="_blank" rel="noopener noreferrer"
                        style={{
                            display: 'inline-flex', alignItems: 'center', gap: 5,
                            padding: '3px 10px', borderRadius: 100,
                            background: 'var(--color-citation-bg)', border: '1px solid var(--color-citation-border)',
                            fontSize: '0.68rem', color: 'var(--color-citation)', textDecoration: 'none',
                            fontFamily: "'JetBrains Mono', monospace",
                            transition: 'all 150ms ease',
                        }}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                            <polyline points="15 3 21 3 21 9" />
                            <line x1="10" y1="14" x2="21" y2="3" />
                        </svg>
                        {doc.doi.length > 35 ? doc.doi.slice(0, 35) + '…' : doc.doi}
                    </a>
                )}
            </div>
        </SectionCard>
    );
}


function MicroBadge({ label, color, bg, icon }) {
    return (
        <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '2px 9px', borderRadius: 100,
            fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.02em',
            color: color || 'var(--color-text-secondary)',
            background: bg || 'rgba(255,255,255,0.04)',
            border: `1px solid ${color ? color + '30' : 'rgba(255,255,255,0.06)'}`,
        }}>
            {icon && <span style={{ fontSize: '0.7rem' }}>{icon}</span>}
            {label}
        </span>
    );
}


/* ═══════════════════════════════════════════════════════════════
   CONFLICTS TAB
   ═══════════════════════════════════════════════════════════════ */

function ConflictsTab({ conflictReport }) {
    if (!conflictReport || !conflictReport.has_conflict) {
        return (
            <div className="animate-fade-up" style={{ maxWidth: '48rem' }}>
                <SectionCard style={{ padding: '32px', textAlign: 'center' }}>
                    <div style={{
                        width: 56, height: 56, borderRadius: 16, margin: '0 auto 16px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                    }}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#34d399"
                            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                        </svg>
                    </div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 6 }}>
                        No Conflicts Detected
                    </h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                        All retrieved studies show consistent outcome directions.
                    </p>
                </SectionCard>
            </div>
        );
    }

    const clusters = conflictReport.clusters || [];

    return (
        <div className="animate-fade-up" style={{ maxWidth: '48rem' }}>
            {/* Conflict Alert Banner */}
            <div style={{
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '16px 20px', borderRadius: 14, marginBottom: 24,
                background: 'rgba(239,68,68,0.06)',
                border: '1px solid rgba(239,68,68,0.2)',
            }}>
                <div style={{
                    width: 40, height: 40, borderRadius: 12,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: 'rgba(239,68,68,0.1)', flexShrink: 0, fontSize: '1.2rem',
                }}>⚡</div>
                <div>
                    <h3 style={{ fontSize: '0.92rem', fontWeight: 600, color: '#fca5a5', marginBottom: 2 }}>
                        Evidence Conflict Detected
                    </h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: 0 }}>
                        {conflictReport.conflict_summary || 'Studies show conflicting outcome directions.'}
                    </p>
                </div>
            </div>

            {/* Clusters Grid */}
            <div style={{ display: 'grid', gap: 14, gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
                {clusters.map((cluster, i) => {
                    const style = STANCE_STYLES[cluster.stance] || STANCE_STYLES['Mixed'];
                    return (
                        <SectionCard key={i} className={`animate-card-enter stagger-${i + 1}`}
                            style={{
                                padding: 0, overflow: 'hidden',
                                borderLeft: `3px solid ${style.color}`,
                            }}>
                            <div style={{ padding: '18px 20px' }}>
                                {/* Header */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                                    <span style={{ fontSize: '1.1rem' }}>{style.icon}</span>
                                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: style.color, flex: 1, margin: 0 }}>
                                        {cluster.stance}
                                    </h4>
                                    <span style={{
                                        fontSize: '0.72rem', fontWeight: 600, padding: '3px 10px', borderRadius: 100,
                                        background: style.bg, color: style.color, border: `1px solid ${style.border}`,
                                    }}>
                                        {cluster.study_count} {cluster.study_count === 1 ? 'study' : 'studies'}
                                    </span>
                                </div>

                                {/* Stats */}
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: cluster.studies?.length > 0 ? 14 : 0 }}>
                                    <MetricBox label="Sample Size" value={cluster.total_sample_size?.toLocaleString() || 'N/A'} />
                                    <MetricBox label="Evidence Level" value={cluster.avg_evidence_level || 'N/A'} />
                                </div>

                                {/* Study DOIs */}
                                {cluster.studies && cluster.studies.length > 0 && (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                        {cluster.studies.slice(0, 3).map((study, j) => (
                                            <a key={j} href={`https://doi.org/${study.doi}`} target="_blank" rel="noopener noreferrer"
                                                className="doi-chip" style={{ fontSize: '0.66rem' }}>
                                                {study.doi?.length > 28 ? study.doi.slice(0, 28) + '…' : study.doi}
                                            </a>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </SectionCard>
                    );
                })}
            </div>
        </div>
    );
}

function MetricBox({ label, value }) {
    return (
        <div style={{
            padding: '10px 12px', borderRadius: 10,
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.04)',
        }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', marginBottom: 3 }}>{label}</div>
            <div className="mono" style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{value}</div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   TIMELINE TAB
   ═══════════════════════════════════════════════════════════════ */

function TimelineTab({ evidence, citations }) {
    const sorted = useMemo(() => {
        const items = [
            ...(evidence || []).map(e => ({
                year: parseInt(e.year) || 0,
                title: e.title || 'Untitled',
                type: e.study_type || 'Study',
                doi: e.doi,
                stance: e.outcome || 'Unknown',
            })),
            ...(citations || []).filter(c => c.year > 0).map(c => ({
                year: c.year,
                title: c.title,
                type: 'Cited',
                doi: c.doi,
                stance: null,
            })),
        ];
        return [...new Map(items.filter(x => x.year > 0).map(x => [x.doi || x.title, x])).values()]
            .sort((a, b) => b.year - a.year);
    }, [evidence, citations]);

    if (sorted.length === 0) {
        return <EmptyState emoji="📅" title="No Timeline Data" description="Timeline requires studies with publication years." />;
    }

    return (
        <div className="animate-fade-up" style={{ maxWidth: '40rem' }}>
            <SectionTitle emoji="📅" title="Temporal Evidence Map" subtitle={`${sorted.length} studies across time`} />

            <div style={{ position: 'relative', paddingLeft: 40 }}>
                {/* Vertical Line */}
                <div style={{
                    position: 'absolute', left: 18, top: 0, bottom: 0, width: 2,
                    background: 'linear-gradient(to bottom, rgba(59,130,246,0.5), rgba(59,130,246,0.05))',
                }} />

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {sorted.map((item, i) => {
                        const stanceStyle = item.stance ? STANCE_STYLES[item.stance] || STANCE_STYLES['Unknown'] : null;
                        return (
                            <div key={i} className={`animate-slide-right stagger-${Math.min(i + 1, 8)}`}
                                style={{ position: 'relative', display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                                {/* Dot */}
                                <div style={{
                                    position: 'absolute', left: -28,
                                    width: 12, height: 12, borderRadius: '50%',
                                    background: stanceStyle?.color || '#3b82f6',
                                    border: '2px solid var(--color-bg-deep)',
                                    boxShadow: `0 0 0 3px ${(stanceStyle?.color || '#3b82f6') + '30'}`,
                                    marginTop: 6, zIndex: 1,
                                }} />

                                <SectionCard style={{ flex: 1, padding: '14px 18px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                        <span className="mono" style={{
                                            fontSize: '0.78rem', fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                                            background: 'rgba(59,130,246,0.1)', color: '#60a5fa',
                                        }}>
                                            {item.year}
                                        </span>
                                        <MicroBadge label={item.type} color={stanceStyle?.color || 'var(--color-text-muted)'} />
                                    </div>
                                    <h4 style={{
                                        fontSize: '0.85rem', fontWeight: 500, lineHeight: 1.4,
                                        color: 'var(--color-text-primary)', margin: 0,
                                    }}>
                                        {item.title}
                                    </h4>
                                    {item.doi && (
                                        <a href={`https://doi.org/${item.doi}`} target="_blank" rel="noopener noreferrer"
                                            className="doi-chip" style={{ marginTop: 8, display: 'inline-flex', fontSize: '0.66rem' }}>
                                            {item.doi.length > 32 ? item.doi.slice(0, 32) + '…' : item.doi}
                                        </a>
                                    )}
                                </SectionCard>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   CITATIONS TAB
   ═══════════════════════════════════════════════════════════════ */

function CitationsTab({ citations }) {
    if (!citations || citations.length === 0) {
        return <EmptyState emoji="🔗" title="No Citations" description="Citations appear after a query returns results." />;
    }

    return (
        <div className="animate-fade-up" style={{ maxWidth: '52rem' }}>
            <SectionTitle emoji="🔗" title="Referenced Sources" subtitle={`${citations.length} sources cited in the synthesis`} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {citations.map((cite, i) => (
                    <SectionCard key={i}
                        className={`animate-card-enter stagger-${Math.min(i + 1, 8)}`}
                        style={{
                            padding: '16px 20px',
                            display: 'flex', alignItems: 'flex-start', gap: 16,
                            transition: 'all 250ms ease',
                        }}>

                        {/* Index Badge */}
                        <div style={{
                            width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: 'linear-gradient(135deg, rgba(167,139,250,0.12), rgba(59,130,246,0.08))',
                            border: '1px solid rgba(167,139,250,0.2)',
                            fontSize: '0.82rem', fontWeight: 700, color: '#a78bfa',
                        }}>
                            {i + 1}
                        </div>

                        {/* Content */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <h4 style={{
                                fontSize: '0.88rem', fontWeight: 600, lineHeight: 1.45,
                                color: 'var(--color-text-primary)', marginBottom: 6,
                                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
                            }}>
                                {cite.title || 'Untitled'}
                            </h4>

                            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                                {cite.authors_short && (
                                    <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>
                                        {cite.authors_short}
                                    </span>
                                )}
                                {cite.year > 0 && (
                                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                        ({cite.year})
                                    </span>
                                )}
                                {cite.journal && (
                                    <span style={{
                                        fontSize: '0.72rem', fontStyle: 'italic', color: 'var(--color-text-muted)',
                                        maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                    }}>
                                        {cite.journal}
                                    </span>
                                )}
                            </div>

                            {cite.doi && (
                                <a href={`https://doi.org/${cite.doi}`} target="_blank" rel="noopener noreferrer"
                                    className="doi-chip" style={{ fontSize: '0.66rem' }}>
                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                        strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                        <polyline points="15 3 21 3 21 9" />
                                        <line x1="10" y1="14" x2="21" y2="3" />
                                    </svg>
                                    {cite.doi}
                                </a>
                            )}
                        </div>
                    </SectionCard>
                ))}
            </div>
        </div>
    );
}
