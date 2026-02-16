import React from 'react';

export default function Disclaimer({ text }) {
    return (
        <div className="disclaimer-bar animate-fade-up">
            <div className="flex items-start gap-3">
                <svg className="flex-shrink-0 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none"
                    stroke="var(--color-warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                    style={{ opacity: 0.7 }}>
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <p style={{ color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
                    {text || 'This output is an evidence summary based on retrieved scientific literature. It is not medical advice and should not replace clinical judgment.'}
                </p>
            </div>
        </div>
    );
}
