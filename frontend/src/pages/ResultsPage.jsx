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
                background: 'radial-gradient(circle at 50% -20%, rgba(56, 189, 248, 0.08), transparent 40%)',
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

function SectionCard({ children, title, subtitle, className, style = {} }) {
    return (
        <div className={`glass-card ${className || ''}`} style={{
            padding: '24px',
            borderRadius: 20, // Vision UI specific
            marginBottom: 24,
            ...style
        }}>
            {(title || subtitle) && (
                <div style={{ marginBottom: 20 }}>
                    {title && <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{title}</h3>}
                    {subtitle && <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>{subtitle}</p>}
                </div>
            )}
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
   SYNTHESIS TAB (ENHANCED)
   ═══════════════════════════════════════════════════════════════ */

function SynthesisTab({ synthesis, limitations, finalPosition, disclaimer }) {
    return (
        <div style={{ maxWidth: '64rem', margin: '0 auto' }} className="animate-fade-up">

            {/* Main Synthesis */}
            <SectionTitle emoji="🧬" title="Evidence Synthesis" subtitle="AI-generated analysis of retrieved studies" />

            <SectionCard style={{
                padding: '32px', marginBottom: 32,
                background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.6) 100%)',
                border: '1px solid rgba(148, 163, 184, 0.1)',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
            }}>
                {synthesis ? (
                    <div className="synthesis-content" style={{
                        color: '#e2e8f0', // Slate-200
                        fontSize: '1.0rem',
                        lineHeight: 1.8,
                        letterSpacing: '0.01em',
                    }}>
                        <RichTextRenderer text={synthesis} />
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
                    <SectionCard style={{ padding: '24px', marginBottom: 32 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {limitations.map((lim, i) => (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'flex-start', gap: 14,
                                    padding: '12px 16px', borderRadius: 12,
                                    background: 'rgba(245,158,11,0.05)',
                                    border: '1px solid rgba(245,158,11,0.1)',
                                }}>
                                    <div style={{
                                        width: 22, height: 22, borderRadius: 6,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        background: 'rgba(245,158,11,0.15)', fontSize: '0.7rem', fontWeight: 700,
                                        color: '#fbbf24', flexShrink: 0, marginTop: 2,
                                    }}>{i + 1}</div>
                                    <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
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
                        padding: '28px 32px', borderRadius: 20, marginBottom: 32,
                        background: 'linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(45,212,191,0.05) 100%)',
                        border: '1px solid rgba(59,130,246,0.25)',
                        boxShadow: '0 10px 30px -10px rgba(59,130,246,0.15)',
                    }}>
                        <div style={{
                            fontSize: '1.05rem', lineHeight: 1.75,
                            color: '#f8fafc', fontWeight: 500, // Slate-50
                            letterSpacing: '0.01em'
                        }}>
                            <RichTextRenderer text={finalPosition} />
                        </div>
                    </div>
                </>
            )}

            {/* Disclaimer */}
            <Disclaimer text={disclaimer} />
        </div>
    );
}

// ── Smart Text Parser ───────────────────────────────────────────

function RichTextRenderer({ text }) {
    if (!text) return null;

    // Split text by lines first to handle paragraph breaks
    const lines = text.split('\n');

    return (
        <React.Fragment>
            {lines.map((line, lineIndex) => {
                if (!line.trim()) return <br key={lineIndex} />;

                // Parse each line for citations: (DOI: ...)
                // Regex matches: (DOI: 10.xxxx/yyyy) or just DOI: 10.xxxx/yyyy inside parens
                const parts = line.split(/(\(DOI:\s*[^)]+\))/g);

                return (
                    <p key={lineIndex} style={{ marginBottom: '1em' }}>
                        {parts.map((part, partIndex) => {
                            // Check if this part is a citation
                            const match = part.match(/\(DOI:\s*([^)]+)\)/);
                            if (match) {
                                const doi = match[1].trim();
                                return (
                                    <CodedCitation key={partIndex} doi={doi} />
                                );
                            }
                            // Return regular text
                            return <span key={partIndex}>{part}</span>;
                        })}
                    </p>
                );
            })}
        </React.Fragment>
    );
}

function CodedCitation({ doi }) {
    // Only display first chunk of DOI if it's very long
    const shortDoi = doi.length > 20 ? doi.slice(0, 15) + '…' : doi;

    return (
        <a
            href={`https://doi.org/${doi}`}
            target="_blank"
            rel="noopener noreferrer"
            title={`View paper: ${doi}`}
            style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                margin: '0 4px', padding: '2px 8px', borderRadius: 6,
                fontSize: '0.75rem', fontWeight: 600,
                textDecoration: 'none',
                verticalAlign: 'middle',
                background: 'rgba(99, 102, 241, 0.15)', // Indigo tinted bg
                color: '#a5b4fc', // Indigo-300
                border: '1px solid rgba(99, 102, 241, 0.3)',
                cursor: 'pointer',
                fontFamily: "'JetBrains Mono', monospace",
                transition: 'all 0.15s ease'
            }}
            onMouseOver={e => {
                e.currentTarget.style.background = 'rgba(99, 102, 241, 0.3)';
                e.currentTarget.style.color = '#fff';
            }}
            onMouseOut={e => {
                e.currentTarget.style.background = 'rgba(99, 102, 241, 0.15)';
                e.currentTarget.style.color = '#a5b4fc';
            }}
        >
            <span style={{ opacity: 0.7 }}>DOI:</span>
            {shortDoi}
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
        </a>
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

/* ═══════════════════════════════════════════════════════════════
   CONFLICTS TAB (DASHBOARD STYLE)
   ═══════════════════════════════════════════════════════════════ */

function ConflictsTab({ conflictReport }) {
    if (!conflictReport || !conflictReport.has_conflict) {
        return (
            <div className="animate-fade-up" style={{ maxWidth: '64rem', margin: '0 auto' }}>
                <SectionCard style={{ padding: '48px', textAlign: 'center', background: 'linear-gradient(180deg, rgba(16,185,129,0.05) 0%, transparent 100%)', border: '1px solid rgba(16,185,129,0.15)' }}>
                    <div style={{
                        width: 64, height: 64, borderRadius: 20, margin: '0 auto 20px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)',
                    }}>
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#34d399"
                            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                            <polyline points="22 4 12 14.01 9 11.01" />
                        </svg>
                    </div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 8 }}>
                        No Conflicts Detected
                    </h3>
                    <p style={{ fontSize: '0.95rem', color: 'var(--color-text-secondary)', maxWidth: 400, margin: '0 auto' }}>
                        All retrieved evidence aligns on a consistent outcome direction. No significant contradictions found.
                    </p>
                </SectionCard>
            </div>
        );
    }

    const clusters = conflictReport.clusters || [];

    return (
        <div className="animate-fade-up" style={{ maxWidth: '72rem', margin: '0 auto' }}>

            {/* 1. Conflict Alert Banner */}
            <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 18,
                padding: '24px 28px', borderRadius: 16, marginBottom: 32,
                background: 'linear-gradient(90deg, rgba(239,68,68,0.08) 0%, rgba(239,68,68,0.04) 100%)',
                border: '1px solid rgba(239,68,68,0.25)',
                boxShadow: '0 4px 20px rgba(239,68,68,0.05)',
            }}>
                <div style={{
                    width: 48, height: 48, borderRadius: 14,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: 'rgba(239,68,68,0.15)', flexShrink: 0,
                    color: '#f87171',
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                </div>
                <div>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fca5a5', marginBottom: 6 }}>
                        Evidence Conflict Detected
                    </h3>
                    <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'rgba(252,165,165,0.9)', margin: 0, maxWidth: '42rem' }}>
                        {conflictReport.conflict_summary || 'Analysis identified contradictory findings across retrieved studies. Review the stance groupings below to understand the divergence.'}
                    </p>
                </div>
            </div>

            {/* 2. Clusters Grid */}
            <div style={{
                display: 'grid',
                gap: 20,
                gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))'
            }}>
                {clusters.map((cluster, i) => {
                    const style = STANCE_STYLES[cluster.stance] || STANCE_STYLES['Mixed'];
                    // Fallback icons if not defined
                    const icon = style.icon === '▲' || style.icon === '▼' ?
                        (style.icon === '▲' ? // Positive
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v8"></path><path d="M8 12h8"></path></svg>
                            : // Negative
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>
                        )
                        : <div style={{ width: 14, height: 14, borderRadius: '50%', background: 'currentColor' }}></div>;

                    return (
                        <div key={i} className={`animate-card-enter stagger-${i + 1}`} style={{
                            background: 'rgba(13,17,23,0.6)', // Darker card bg
                            border: `1px solid ${style.border}`,
                            borderRadius: 16,
                            padding: '24px',
                            display: 'flex', flexDirection: 'column',
                            boxShadow: `0 0 0 1px ${style.border}`, // Double border effect
                            position: 'relative', overflow: 'hidden'
                        }}>
                            {/* Stance Header */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <div style={{ color: style.color, display: 'flex' }}>{icon}</div>
                                    <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.01em' }}>
                                        {cluster.stance}
                                    </h4>
                                </div>
                                <span style={{
                                    fontSize: '0.75rem', fontWeight: 600, padding: '4px 12px', borderRadius: 100,
                                    background: 'rgba(255,255,255,0.06)', color: 'var(--color-text-secondary)',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                }}>
                                    {cluster.study_count} {cluster.study_count === 1 ? 'study' : 'studies'}
                                </span>
                            </div>

                            {/* Metrics Row */}
                            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 32 }}>
                                <MetricBox label="Studies Included" value={cluster.study_count} icon="📚" />
                                <MetricBox label="Sample Size" value={cluster.total_sample_size?.toLocaleString() || '0'} icon="👥" />
                                <MetricBox label="Evidence Level" value={cluster.avg_evidence_level || 'N/A'} icon="⚖️" />
                            </div>
                            <div style={{ marginTop: 24 }}>
                                {cluster.studies && cluster.studies.length > 0 ? (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                        {cluster.studies.map((study, j) => (
                                            <a key={j} href={`https://doi.org/${study.doi}`} target="_blank" rel="noopener noreferrer"
                                                style={{
                                                    display: 'inline-flex', alignItems: 'center',
                                                    padding: '4px 12px', borderRadius: 6,
                                                    background: 'rgba(76, 29, 149, 0.25)', // Deep purple tint
                                                    border: '1px solid rgba(139, 92, 246, 0.3)',
                                                    fontSize: '0.75rem', color: '#c4b5fd',
                                                    textDecoration: 'none', fontFamily: "'JetBrains Mono', monospace",
                                                    transition: 'all 0.2s ease',
                                                }}
                                                onMouseOver={(e) => {
                                                    e.currentTarget.style.background = 'rgba(76, 29, 149, 0.4)';
                                                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.6)';
                                                }}
                                                onMouseOut={(e) => {
                                                    e.currentTarget.style.background = 'rgba(76, 29, 149, 0.25)';
                                                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                                                }}
                                            >
                                                {study.doi?.length > 24 ? study.doi.slice(0, 24) + '…' : study.doi}
                                            </a>
                                        ))}
                                    </div>
                                ) : (
                                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                                        No linked studies
                                    </span>
                                )}
                            </div>

                        </div>
                    );
                })}
            </div>
        </div >
    );
}

function MetricBox({ label, value, icon, trend }) {
    return (
        <div style={{
            background: 'var(--color-bg-primary)', // Panel background
            borderRadius: 20,
            padding: '16px 22px',
            display: 'flex', alignItems: 'center', gap: 18,
            minWidth: 200, flex: 1,
            boxShadow: '0 20px 27px 0 rgba(0, 0, 0, 0.05)'
        }}>
            {/* Gradient Icon Box */}
            <div style={{
                width: 48, height: 48, borderRadius: 12,
                background: 'var(--color-primary-500)',
                boxShadow: '0 4px 6px rgba(0, 117, 255, 0.3)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontSize: '1.2rem'
            }}>
                {icon || '📊'}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: 700 }}>
                    {label}
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginTop: 2 }}>
                    {value}
                    {trend && <span style={{ fontSize: '0.8rem', color: 'var(--color-positive)', marginLeft: 6 }}>{trend}</span>}
                </div>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   TIMELINE TAB
   ═══════════════════════════════════════════════════════════════ */

function TimelineTab({ evidence, citations }) {
    const [selectedYear, setSelectedYear] = useState(null);

    const sorted = useMemo(() => {
        const items = [
            ...(evidence || []).map(e => ({
                year: parseInt(e.year) || 0,
                title: e.title || 'Untitled',
                type: e.study_type || 'Study',
                doi: e.doi,
                stance: e.outcome || 'Unknown',
                source: e.source || 'PubMed',
                authors: e.authors_short || '',
            })),
            ...(citations || []).filter(c => c.year > 0).map(c => ({
                year: c.year,
                title: c.title,
                type: 'Cited',
                doi: c.doi,
                stance: null,
                source: 'Cited',
                authors: c.authors_short || '',
            })),
        ];
        return [...new Map(items.filter(x => x.year > 0).map(x => [x.doi || x.title, x])).values()]
            .sort((a, b) => b.year - a.year);
    }, [evidence, citations]);

    // Year distribution for the chart
    const yearDist = useMemo(() => {
        const dist = {};
        sorted.forEach(s => { dist[s.year] = (dist[s.year] || 0) + 1; });
        return Object.entries(dist).sort(([a], [b]) => Number(a) - Number(b));
    }, [sorted]);

    // Stance summary
    const stanceCounts = useMemo(() => {
        const counts = {};
        sorted.forEach(s => {
            const key = s.stance || 'Unknown';
            counts[key] = (counts[key] || 0) + 1;
        });
        return counts;
    }, [sorted]);

    const filtered = selectedYear ? sorted.filter(s => s.year === selectedYear) : sorted;
    const yearRange = sorted.length > 0 ? `${sorted[sorted.length - 1].year} – ${sorted[0].year}` : 'N/A';
    const maxCount = yearDist.length > 0 ? Math.max(...yearDist.map(([, c]) => c)) : 1;

    if (sorted.length === 0) {
        return <EmptyState emoji="📅" title="No Timeline Data" description="Timeline requires studies with publication years." />;
    }

    return (
        <div className="animate-fade-up" style={{ maxWidth: '80rem', margin: '0 auto' }}>
            <SectionTitle emoji="📅" title="Temporal Evidence Map" subtitle={`${sorted.length} studies across time`} />

            {/* ── Top Stats Row ── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
                <MetricBox label="Total Studies" value={sorted.length} icon="📚" />
                <MetricBox label="Year Range" value={yearRange} icon="📆" />
                <MetricBox label="Most Recent" value={sorted[0]?.year || 'N/A'} icon="🆕" />
                <MetricBox label="Peak Year" value={yearDist.length > 0 ? yearDist.reduce((a, b) => b[1] > a[1] ? b : a)[0] : 'N/A'} icon="📈" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24, alignItems: 'start' }}>

                {/* ── Left: Timeline ── */}
                <div style={{ position: 'relative', paddingLeft: 40 }}>
                    {/* Vertical Line */}
                    <div style={{
                        position: 'absolute', left: 18, top: 0, bottom: 0, width: 2,
                        background: 'linear-gradient(to bottom, rgba(0,117,255,0.6), rgba(0,117,255,0.05))',
                    }} />

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                        {filtered.map((item, i) => {
                            const stanceStyle = item.stance ? STANCE_STYLES[item.stance] || STANCE_STYLES['Unknown'] : null;
                            return (
                                <div key={i} className={`animate-slide-right stagger-${Math.min(i + 1, 8)}`}
                                    style={{ position: 'relative', display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                                    {/* Dot */}
                                    <div style={{
                                        position: 'absolute', left: -28,
                                        width: 14, height: 14, borderRadius: '50%',
                                        background: stanceStyle?.color || '#0075ff',
                                        border: '3px solid var(--color-bg-deep)',
                                        boxShadow: `0 0 0 3px ${(stanceStyle?.color || '#0075ff') + '30'}`,
                                        marginTop: 6, zIndex: 1,
                                    }} />

                                    <SectionCard style={{ flex: 1, padding: '18px 22px', borderRadius: 20 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                                            <span className="mono" style={{
                                                fontSize: '0.82rem', fontWeight: 700, padding: '3px 10px', borderRadius: 8,
                                                background: 'rgba(0,117,255,0.15)', color: '#38bdf8',
                                            }}>
                                                {item.year}
                                            </span>
                                            <MicroBadge label={item.type} color={stanceStyle?.color || 'var(--color-text-muted)'} />
                                            {item.source && item.source !== 'Cited' && (
                                                <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>
                                                    {SOURCE_STYLES[item.source]?.icon || '📄'} {item.source}
                                                </span>
                                            )}
                                        </div>
                                        <h4 style={{
                                            fontSize: '0.88rem', fontWeight: 600, lineHeight: 1.5,
                                            color: '#fff', margin: 0,
                                        }}>
                                            {item.title}
                                        </h4>
                                        {item.authors && (
                                            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 6 }}>
                                                {item.authors}
                                            </p>
                                        )}
                                        {item.doi && (
                                            <a href={`https://doi.org/${item.doi}`} target="_blank" rel="noopener noreferrer"
                                                className="doi-chip" style={{ marginTop: 10, display: 'inline-flex', fontSize: '0.68rem' }}>
                                                🔗 {item.doi.length > 30 ? item.doi.slice(0, 30) + '…' : item.doi}
                                            </a>
                                        )}
                                    </SectionCard>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* ── Right: Sidebar ── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20, position: 'sticky', top: 24 }}>

                    {/* Year Distribution Chart */}
                    <SectionCard title="Publication Trend" style={{ padding: '20px 22px', borderRadius: 20 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {yearDist.map(([year, count]) => (
                                <div key={year}
                                    onClick={() => setSelectedYear(selectedYear === Number(year) ? null : Number(year))}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                                        padding: '4px 8px', borderRadius: 8,
                                        background: selectedYear === Number(year) ? 'rgba(0,117,255,0.15)' : 'transparent',
                                        transition: 'all 0.2s',
                                    }}>
                                    <span className="mono" style={{ fontSize: '0.75rem', color: '#a0aec0', width: 40 }}>{year}</span>
                                    <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                                        <div style={{
                                            width: `${(count / maxCount) * 100}%`, height: '100%', borderRadius: 4,
                                            background: selectedYear === Number(year)
                                                ? 'linear-gradient(90deg, #0075ff, #21d4fd)'
                                                : 'linear-gradient(90deg, rgba(0,117,255,0.6), rgba(33,212,253,0.4))',
                                            transition: 'width 0.5s ease',
                                        }} />
                                    </div>
                                    <span className="mono" style={{ fontSize: '0.72rem', color: '#fff', fontWeight: 700, width: 20, textAlign: 'right' }}>{count}</span>
                                </div>
                            ))}
                        </div>
                        {selectedYear && (
                            <button onClick={() => setSelectedYear(null)} style={{
                                marginTop: 12, padding: '6px 14px', borderRadius: 8,
                                background: 'rgba(0,117,255,0.1)', border: '1px solid rgba(0,117,255,0.3)',
                                color: '#38bdf8', fontSize: '0.75rem', cursor: 'pointer', width: '100%',
                            }}>Clear Filter</button>
                        )}
                    </SectionCard>

                    {/* Stance Breakdown */}
                    <SectionCard title="Outcome Distribution" style={{ padding: '20px 22px', borderRadius: 20 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {Object.entries(stanceCounts).map(([stance, count]) => {
                                const style = STANCE_STYLES[stance] || STANCE_STYLES['Unknown'];
                                return (
                                    <div key={stance} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <div style={{
                                            width: 10, height: 10, borderRadius: '50%', background: style.color, flexShrink: 0,
                                            boxShadow: `0 0 6px ${style.color}50`,
                                        }} />
                                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', flex: 1 }}>{stance}</span>
                                        <span className="mono" style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fff' }}>{count}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </SectionCard>
                </div>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   CITATIONS TAB
   ═══════════════════════════════════════════════════════════════ */

function CitationsTab({ citations }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('index'); // 'index', 'year', 'title'

    if (!citations || citations.length === 0) {
        return <EmptyState emoji="🔗" title="No Citations" description="Citations appear after a query returns results." />;
    }

    // Source breakdown
    const sourceCounts = useMemo(() => {
        const counts = {};
        citations.forEach(c => {
            const src = c.source || 'Unknown';
            counts[src] = (counts[src] || 0) + 1;
        });
        return counts;
    }, [citations]);

    // Journal breakdown (top 5)
    const topJournals = useMemo(() => {
        const jMap = {};
        citations.forEach(c => {
            if (c.journal) {
                const j = c.journal.length > 35 ? c.journal.slice(0, 35) + '…' : c.journal;
                jMap[j] = (jMap[j] || 0) + 1;
            }
        });
        return Object.entries(jMap).sort(([, a], [, b]) => b - a).slice(0, 5);
    }, [citations]);

    // Year range
    const years = citations.filter(c => c.year > 0).map(c => c.year);
    const yearRange = years.length > 0 ? `${Math.min(...years)} – ${Math.max(...years)}` : 'N/A';

    // Filtering & Sorting
    const filtered = useMemo(() => {
        let list = [...citations];
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            list = list.filter(c =>
                (c.title || '').toLowerCase().includes(term) ||
                (c.doi || '').toLowerCase().includes(term) ||
                (c.authors_short || '').toLowerCase().includes(term)
            );
        }
        if (sortBy === 'year') list.sort((a, b) => (b.year || 0) - (a.year || 0));
        else if (sortBy === 'title') list.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
        return list;
    }, [citations, searchTerm, sortBy]);

    return (
        <div className="animate-fade-up" style={{ maxWidth: '80rem', margin: '0 auto' }}>
            <SectionTitle emoji="🔗" title="Referenced Sources" subtitle={`${citations.length} sources cited in the synthesis`} />

            {/* ── Top Stats Row ── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                <MetricBox label="Total Citations" value={citations.length} icon="📄" />
                <MetricBox label="Year Range" value={yearRange} icon="📆" />
                <MetricBox label="With DOI" value={citations.filter(c => c.doi).length} icon="🔗" />
                <MetricBox label="Journals" value={topJournals.length} icon="📰" />
            </div>

            {/* ── Search Bar ── */}
            <div style={{ marginBottom: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <div style={{
                    flex: 1, minWidth: 260,
                    display: 'flex', alignItems: 'center', gap: 10,
                    background: 'rgba(6, 11, 40, 0.8)',
                    border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14,
                    padding: '10px 16px',
                }}>
                    <span style={{ fontSize: '0.9rem' }}>🔍</span>
                    <input
                        type="text"
                        placeholder="Search citations by title, DOI, or author..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        style={{
                            flex: 1, background: 'transparent', border: 'none', outline: 'none',
                            color: '#fff', fontSize: '0.85rem', fontFamily: 'inherit',
                        }}
                    />
                    {searchTerm && (
                        <button onClick={() => setSearchTerm('')} style={{
                            background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: 6,
                            color: '#a0aec0', cursor: 'pointer', padding: '2px 8px', fontSize: '0.75rem',
                        }}>✕</button>
                    )}
                </div>

                {/* Sort Buttons */}
                <div style={{ display: 'flex', gap: 6 }}>
                    {[['index', '#'], ['year', '📅'], ['title', 'A→Z']].map(([key, lbl]) => (
                        <button key={key}
                            onClick={() => setSortBy(key)}
                            style={{
                                padding: '8px 14px', borderRadius: 10,
                                background: sortBy === key ? 'rgba(0,117,255,0.2)' : 'rgba(6,11,40,0.8)',
                                border: `1px solid ${sortBy === key ? 'rgba(0,117,255,0.5)' : 'rgba(255,255,255,0.08)'}`,
                                color: sortBy === key ? '#38bdf8' : '#a0aec0',
                                cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                                transition: 'all 0.2s',
                            }}
                        >{lbl}</button>
                    ))}
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 24, alignItems: 'start' }}>
                {/* ── Left: Citation Cards ── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {filtered.map((cite, i) => {
                        const originalIndex = citations.indexOf(cite);
                        return (
                            <SectionCard key={i}
                                className={`animate-card-enter stagger-${Math.min(i + 1, 8)}`}
                                style={{
                                    padding: '20px 24px', borderRadius: 20,
                                    display: 'flex', alignItems: 'flex-start', gap: 18,
                                }}>

                                {/* Index Badge */}
                                <div style={{
                                    width: 42, height: 42, borderRadius: 12, flexShrink: 0,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    background: 'var(--gradient-info)',
                                    fontSize: '0.9rem', fontWeight: 700, color: '#fff',
                                    boxShadow: '0 4px 12px rgba(33, 82, 255, 0.3)',
                                }}>
                                    {originalIndex + 1}
                                </div>

                                {/* Content */}
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <h4 style={{
                                        fontSize: '0.9rem', fontWeight: 600, lineHeight: 1.5,
                                        color: '#fff', marginBottom: 8,
                                    }}>
                                        {cite.title || 'Untitled'}
                                    </h4>

                                    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                                        {cite.authors_short && (
                                            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                                                👤 {cite.authors_short}
                                            </span>
                                        )}
                                        {cite.year > 0 && (
                                            <span className="mono" style={{
                                                fontSize: '0.75rem', padding: '2px 8px', borderRadius: 6,
                                                background: 'rgba(0,117,255,0.12)', color: '#38bdf8', fontWeight: 600,
                                            }}>
                                                {cite.year}
                                            </span>
                                        )}
                                        {cite.journal && (
                                            <span style={{
                                                fontSize: '0.73rem', fontStyle: 'italic', color: 'var(--color-text-muted)',
                                                maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                            }}>
                                                📰 {cite.journal}
                                            </span>
                                        )}
                                        {cite.source && (
                                            <span style={{
                                                fontSize: '0.65rem', padding: '2px 8px', borderRadius: 6,
                                                background: SOURCE_STYLES[cite.source]?.bg || 'rgba(255,255,255,0.05)',
                                                color: SOURCE_STYLES[cite.source]?.color || '#a0aec0',
                                                marginLeft: 'auto',
                                            }}>
                                                {SOURCE_STYLES[cite.source]?.icon || '📄'} {cite.source}
                                            </span>
                                        )}
                                    </div>

                                    {cite.doi && (
                                        <a href={`https://doi.org/${cite.doi}`} target="_blank" rel="noopener noreferrer"
                                            className="doi-chip" style={{ fontSize: '0.7rem' }}>
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
                        );
                    })}

                    {filtered.length === 0 && (
                        <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
                            No citations match "<strong>{searchTerm}</strong>"
                        </div>
                    )}
                </div>

                {/* ── Right: Sidebar ── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20, position: 'sticky', top: 24 }}>

                    {/* Source Breakdown */}
                    <SectionCard title="Sources" style={{ padding: '20px 22px', borderRadius: 20 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {Object.entries(sourceCounts).map(([src, count]) => {
                                const srcStyle = SOURCE_STYLES[src] || {};
                                return (
                                    <div key={src} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <span style={{ fontSize: '1rem' }}>{srcStyle.icon || '📄'}</span>
                                        <span style={{ fontSize: '0.82rem', color: srcStyle.color || '#a0aec0', flex: 1 }}>{src}</span>
                                        <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>{count}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </SectionCard>

                    {/* Top Journals */}
                    {topJournals.length > 0 && (
                        <SectionCard title="Top Journals" style={{ padding: '20px 22px', borderRadius: 20 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {topJournals.map(([journal, count], i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <span style={{
                                            width: 22, height: 22, borderRadius: 6, flexShrink: 0,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            background: 'var(--gradient-dark)',
                                            fontSize: '0.65rem', fontWeight: 700, color: '#fff',
                                        }}>{i + 1}</span>
                                        <span style={{
                                            fontSize: '0.75rem', color: 'var(--color-text-secondary)', flex: 1,
                                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                        }}>
                                            {journal}
                                        </span>
                                        <span className="mono" style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fff' }}>{count}</span>
                                    </div>
                                ))}
                            </div>
                        </SectionCard>
                    )}

                    {/* Quick Actions */}
                    <SectionCard title="Quick Actions" style={{ padding: '20px 22px', borderRadius: 20 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <button
                                onClick={() => {
                                    const text = citations.map((c, i) => `[${i + 1}] ${c.title}${c.doi ? ` DOI: ${c.doi}` : ''}`).join('\n');
                                    navigator.clipboard.writeText(text);
                                }}
                                style={{
                                    padding: '10px 16px', borderRadius: 12, cursor: 'pointer',
                                    background: 'rgba(0,117,255,0.1)', border: '1px solid rgba(0,117,255,0.25)',
                                    color: '#38bdf8', fontSize: '0.82rem', fontWeight: 600,
                                    display: 'flex', alignItems: 'center', gap: 8, width: '100%',
                                    transition: 'all 0.2s',
                                }}
                            >
                                📋 Copy All Citations
                            </button>
                            <button
                                onClick={() => {
                                    const dois = citations.filter(c => c.doi).map(c => c.doi).join('\n');
                                    navigator.clipboard.writeText(dois);
                                }}
                                style={{
                                    padding: '10px 16px', borderRadius: 12, cursor: 'pointer',
                                    background: 'rgba(1,181,116,0.1)', border: '1px solid rgba(1,181,116,0.25)',
                                    color: '#01b574', fontSize: '0.82rem', fontWeight: 600,
                                    display: 'flex', alignItems: 'center', gap: 8, width: '100%',
                                    transition: 'all 0.2s',
                                }}
                            >
                                🔗 Copy All DOIs
                            </button>
                        </div>
                    </SectionCard>
                </div>
            </div>
        </div>
    );
}
