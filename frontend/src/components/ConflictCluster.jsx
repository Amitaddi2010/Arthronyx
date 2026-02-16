import React from 'react';

export default function ConflictCluster({ conflictReport }) {
    if (!conflictReport || !conflictReport.has_conflict) {
        return (
            <div className="glass-card-static p-5 animate-fade-up">
                <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ background: 'var(--color-positive-bg)', border: '1px solid var(--color-positive-border)' }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-positive)"
                            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                            No Conflicts Detected
                        </h3>
                        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                            All retrieved studies show consistent outcome directions
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    const clusters = conflictReport.clusters || [];

    const stanceColors = {
        'Positive Effect': { bg: 'var(--color-positive-bg)', border: 'var(--color-positive-border)', color: 'var(--color-positive)', icon: '↑' },
        'Negative Effect': { bg: 'var(--color-danger-bg)', border: 'var(--color-danger-border)', color: 'var(--color-danger)', icon: '↓' },
        'Mixed': { bg: 'var(--color-warning-bg)', border: 'var(--color-warning-border)', color: 'var(--color-warning)', icon: '↕' },
        'No Significant Difference': { bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.15)', color: 'var(--color-text-secondary)', icon: '–' },
    };

    return (
        <div className="animate-fade-up">
            {/* Conflict Alert */}
            <div className="conflict-indicator mb-4">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)"
                    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <div>
                    <h3 className="text-sm font-semibold" style={{ color: '#fca5a5' }}>
                        Evidence Conflict Detected
                    </h3>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
                        {conflictReport.conflict_summary || 'Studies show conflicting outcome directions.'}
                    </p>
                </div>
            </div>

            {/* Clusters */}
            <div className="grid gap-3 md:grid-cols-2">
                {clusters.map((cluster, i) => {
                    const style = stanceColors[cluster.stance] || stanceColors['Mixed'];
                    return (
                        <div key={i}
                            className={`glass-card-static p-4 animate-card-enter stagger-${i + 1}`}
                            style={{ borderLeft: `3px solid ${style.color}` }}>
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-lg">{style.icon}</span>
                                <h4 className="text-sm font-semibold" style={{ color: style.color }}>
                                    {cluster.stance}
                                </h4>
                                <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full"
                                    style={{ background: style.bg, color: style.color, border: `1px solid ${style.border}` }}>
                                    {cluster.study_count} {cluster.study_count === 1 ? 'study' : 'studies'}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-3 text-xs">
                                <div>
                                    <span style={{ color: 'var(--color-text-muted)' }}>Sample Size</span>
                                    <div className="font-semibold mono mt-0.5" style={{ color: 'var(--color-text-primary)' }}>
                                        {cluster.total_sample_size?.toLocaleString() || 'N/A'}
                                    </div>
                                </div>
                                <div>
                                    <span style={{ color: 'var(--color-text-muted)' }}>Avg Evidence Level</span>
                                    <div className="font-semibold mono mt-0.5" style={{ color: 'var(--color-text-primary)' }}>
                                        {cluster.avg_evidence_level || 'N/A'}
                                    </div>
                                </div>
                            </div>

                            {cluster.studies && cluster.studies.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 mt-3">
                                    {cluster.studies.slice(0, 3).map((study, j) => (
                                        <a key={j} href={`https://doi.org/${study.doi}`} target="_blank" rel="noopener noreferrer"
                                            className="doi-chip text-xs">
                                            {study.doi.length > 30 ? study.doi.slice(0, 30) + '…' : study.doi}
                                        </a>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
