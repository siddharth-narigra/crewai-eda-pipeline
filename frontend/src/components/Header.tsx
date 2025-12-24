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
                                        ? 'bg-black text-white'
                                        : 'bg-white text-black hover:bg-[#F0F0F0]'
                                    }
                  border-[3px] border-black
                  ${activeTab === tab.id ? '' : 'border-l-0'}
                  first:border-l-[3px]
                `}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </nav>

                    {/* Status */}
                    <div className="flex items-center gap-3">
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
