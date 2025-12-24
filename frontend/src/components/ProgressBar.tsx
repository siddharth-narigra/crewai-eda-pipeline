'use client';

import { StageInfo, ActivityLogEntry } from '@/lib/api';

interface ProgressBarProps {
    progress: number;
    status: string;
    stages?: StageInfo[];
    activityLog?: ActivityLogEntry[];
}

export default function ProgressBar({ progress, status, stages, activityLog }: ProgressBarProps) {
    // Default stages if not provided
    const defaultStages: StageInfo[] = [
        { id: 'profiling', name: 'Data Profiling', status: 'pending' },
        { id: 'cleaning', name: 'Data Cleaning', status: 'pending' },
        { id: 'visualization', name: 'Visualization', status: 'pending' },
        { id: 'statistics', name: 'Statistical Analysis', status: 'pending' },
        { id: 'ml_xai', name: 'ML & XAI Analysis', status: 'pending' },
        { id: 'report', name: 'Report Generation', status: 'pending' },
    ];

    const displayStages = stages && stages.length > 0 ? stages : defaultStages;
    // Only show last 5 activities
    const displayLog = (activityLog || []).slice(0, 5);

    // Get stage styles - brutalist colors (no shadows)
    const getStageStyle = (stageStatus: string) => {
        switch (stageStatus) {
            case 'completed':
                return {
                    background: '#00AA00',
                    color: '#FFFFFF',
                    borderColor: '#008800',
                };
            case 'running':
                return {
                    background: '#0000FF',
                    color: '#FFFFFF',
                    borderColor: '#0000CC',
                };
            default:
                return {
                    background: '#FFFFFF',
                    color: '#000000',
                    borderColor: '#000000',
                };
        }
    };

    // Get stage icon
    const getStageIcon = (stageStatus: string) => {
        switch (stageStatus) {
            case 'completed':
                return '✓';
            case 'running':
                return '▶';
            default:
                return '○';
        }
    };

    return (
        <div className="border-[4px] border-black bg-white p-6" style={{ boxShadow: '8px 8px 0px 0px #000000' }}>
            {/* Header with progress */}
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-black uppercase tracking-tight">
                    ANALYSIS IN PROGRESS
                </h2>
                <div className="bg-black text-white px-4 py-2 font-mono text-xl font-bold">
                    {progress}%
                </div>
            </div>

            {/* Progress bar - brutalist style */}
            <div className="h-6 bg-white border-[3px] border-black mb-6">
                <div
                    className="h-full bg-black transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                />
            </div>

            {/* Patience message - brutalist yellow banner */}
            <div className="bg-[#FFFF00] border-[3px] border-black p-4 mb-8">
                <p className="font-bold text-sm uppercase tracking-wide">
                    ⚠️ THIS ANALYSIS INVOLVES <span className="underline">6 AI AGENTS</span> WORKING SEQUENTIALLY.
                    TYPICALLY TAKES <span className="underline">2-5 MINUTES</span>. PLEASE BE PATIENT.
                </p>
            </div>

            {/* Two-column layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left: Stages checklist */}
                <div>
                    <h3 className="text-lg font-black uppercase mb-4 pb-2 border-b-[3px] border-black">
                        PIPELINE STAGES
                    </h3>
                    <div className="space-y-3">
                        {displayStages.map((stage) => {
                            const style = getStageStyle(stage.status);
                            return (
                                <div
                                    key={stage.id}
                                    className={`
                                        flex items-center gap-4 p-4 border-[3px] transition-all duration-300
                                        ${stage.status === 'running' ? 'stage-running' : ''}
                                    `}
                                    style={{
                                        backgroundColor: style.background,
                                        color: style.color,
                                        borderColor: style.borderColor,
                                    }}
                                >
                                    <span className="w-8 h-8 flex items-center justify-center text-xl font-bold">
                                        {getStageIcon(stage.status)}
                                    </span>
                                    <span className="font-bold uppercase tracking-wide text-sm">
                                        {stage.name}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Right: Activity log - Terminal style */}
                <div>
                    <h3 className="text-lg font-black uppercase mb-4 pb-2 border-b-[3px] border-black">
                        LIVE TERMINAL
                    </h3>
                    <div
                        className="border-[3px] border-black bg-black p-4 h-[340px] overflow-hidden font-mono"
                    >
                        {displayLog.length === 0 ? (
                            <div className="text-[#00FF00] text-sm">
                                <span className="animate-pulse">█</span> Initializing agents...
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {displayLog.map((entry, i) => (
                                    <div key={i} className="text-sm">
                                        <div className="text-[#00FF00] font-bold flex items-center gap-2">
                                            <span className="text-[#FFFF00]">$</span>
                                            <span>{entry.agent}</span>
                                        </div>
                                        <div className="text-[#AAAAAA] ml-4 mt-1">
                                            └─ {entry.action}
                                        </div>
                                    </div>
                                ))}
                                <div className="text-[#00FF00] animate-pulse mt-4">
                                    █
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Current status footer - simplified */}
            <div className="mt-6 pt-4 border-t-[3px] border-black flex items-center gap-3">
                <span className="inline-block w-3 h-3 bg-[#0000FF] animate-pulse" />
                <span className="font-bold uppercase tracking-wide text-sm">
                    {status}
                </span>
            </div>
        </div>
    );
}
