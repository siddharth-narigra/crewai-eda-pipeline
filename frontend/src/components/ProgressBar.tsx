'use client';

interface ProgressBarProps {
    progress: number;
    status: string;
}

export default function ProgressBar({ progress, status }: ProgressBarProps) {
    return (
        <div className="card-brutal">
            <div className="flex items-center justify-between mb-3">
                <span className="text-h3">ANALYSIS IN PROGRESS</span>
                <span className="text-mono text-xl font-bold">{progress}%</span>
            </div>

            <div className="progress-brutal">
                <div
                    className="progress-brutal-fill"
                    style={{ width: `${progress}%` }}
                />
            </div>

            <div className="mt-3 flex items-center gap-2">
                <div className="spinner-brutal" />
                <span className="text-label">{status.toUpperCase()}</span>
            </div>
        </div>
    );
}
