import React from 'react';

export default function EvidenceCard({ doc, index }) {
    const levelClass = {
        'I': 'evidence-level-1',
        'II': 'evidence-level-2',
        'III': 'evidence-level-3',
        'IV': 'evidence-level-4',
        'V': 'evidence-level-4',
    };

    const stanceClass = {
        'Positive Effect': 'stance-positive',
        'Negative Effect': 'stance-negative',
        'Mixed': 'stance-mixed',
        'No Significant Difference': 'stance-neutral',
        'Unknown': 'stance-neutral',
    };

    const stanceIcon = {
        'Positive Effect': '↑',
        'Negative Effect': '↓',
        'Mixed': '↕',
        'No Significant Difference': '–',
        'Unknown': '?',
    };

    const level = doc.evidence_level || 'N/A';
    const stance = doc.outcome || doc.outcome_stance || 'Unknown';
    const score = parseFloat(doc.final_score || 0);
    const scorePercent = Math.min(score * 100, 100);

    return (
        <div className={`evidence-card p-5 animate-card-enter stagger-${Math.min(index + 1, 8)}`}>
            {/* Header Row */}
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold leading-snug mb-1 line-clamp-2"
                        style={{ color: 'var(--color-text-primary)' }}>
                        {doc.title || 'Untitled Study'}
                    </h4>
                    <div className="flex items-center flex-wrap gap-2 mt-2">
                        {doc.study_type && (
                            <span className="text-xs px-2 py-0.5 rounded-full"
                                style={{
                                    background: 'rgba(59,130,246,0.08)',
                                    color: 'var(--color-primary-400)',
                                    border: '1px solid rgba(59,130,246,0.15)',
                                    fontWeight: 500
                                }}>
                                {doc.study_type}
                            </span>
                        )}
                        <span className={`evidence-level ${levelClass[level] || 'evidence-level-4'}`}>
                            Level {level}
                        </span>
                        <span className={`stance-badge ${stanceClass[stance] || 'stance-neutral'}`}>
                            {stanceIcon[stance] || '?'} {stance}
                        </span>
                    </div>
                </div>
                {doc.year && (
                    <span className="text-xs font-semibold px-2 py-1 rounded-md flex-shrink-0 mono"
                        style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--color-text-muted)' }}>
                        {doc.year}
                    </span>
                )}
            </div>

            {/* Score Bar */}
            <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Relevance Score</span>
                    <span className="text-xs font-semibold mono" style={{ color: 'var(--color-primary-400)' }}>
                        {score.toFixed(4)}
                    </span>
                </div>
                <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: `${scorePercent}%` }} />
                </div>
            </div>

            {/* DOI */}
            {doc.doi && (
                <a href={`https://doi.org/${doc.doi}`} target="_blank" rel="noopener noreferrer"
                    className="doi-chip">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                    {doc.doi}
                </a>
            )}
        </div>
    );
}
