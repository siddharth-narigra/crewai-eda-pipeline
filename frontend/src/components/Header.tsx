'use client';

interface HeaderProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
    isAnalyzing: boolean;
}

export default function Header({ activeTab, onTabChange, isAnalyzing }: HeaderProps) {
    const tabs = [
        { id: 'upload', label: 'UPLOAD' },
        { id: 'dashboard', label: 'DASHBOARD' },
        { id: 'charts', label: 'CHARTS' },
        { id: 'model', label: 'MODEL' },
        { id: 'report', label: 'REPORT' },
    ];

    return (
        <header className="border-b-[6px] border-black bg-white">
            <div className="container-brutal">
                <div className="flex items-center justify-between py-4">
                    {/* Logo */}
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-black flex items-center justify-center">
                            <span className="text-white text-2xl font-black">E</span>
                        </div>
                        <div>
                            <h1 className="text-h3 leading-none">EXPLAINABLE</h1>
                            <p className="text-label text-[#888]">EDA SYSTEM</p>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex items-center gap-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => onTabChange(tab.id)}
                                className={`
                  px-6 py-3 text-label transition-all
                  ${activeTab === tab.id
                                        ? tab.id === 'upload'
                                            ? 'text-white'
                                            : tab.id === 'charts'
                                                ? 'text-black'
                                                : tab.id === 'model'
                                                    ? 'text-white'
                                                    : 'bg-black text-white'
                                        : 'bg-white text-black hover:bg-[#F0F0F0]'
                                    }
                  border-[3px] border-black
                  ${activeTab === tab.id ? '' : 'border-l-0'}
                  first:border-l-[3px]
                `}
                                style={
                                    activeTab === tab.id && tab.id === 'upload'
                                        ? { backgroundColor: '#0000FF' }
                                        : activeTab === tab.id && tab.id === 'charts'
                                            ? { backgroundColor: '#FFFF00' }
                                            : activeTab === tab.id && tab.id === 'model'
                                                ? { backgroundColor: '#00AA00' }
                                                : undefined
                                }
                            >
                                {tab.label}
                            </button>
                        ))}
                    </nav>

                    {/* Status & Links */}
                    <div className="flex items-center gap-6">
                        <a
                            href="https://github.com/siddharth-narigra/crewai-eda-pipeline"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-label hover:underline flex items-center gap-1"
                        >
                            VIEW ON GITHUB ↗
                        </a>

                        <div className="w-[1px] h-6 bg-gray-300" />

                        {isAnalyzing ? (
                            <div className="flex items-center gap-2">
                                <span className="spinner-brutal" />
                                <span className="text-label">ANALYZING</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-[#00AA00]" />
                                <span className="text-label">READY</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
