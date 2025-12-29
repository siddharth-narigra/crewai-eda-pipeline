'use client';

interface HeaderProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
    isAnalyzing: boolean;
}

export default function Header({ activeTab, onTabChange, isAnalyzing }: HeaderProps) {
    const tabs = [
        { id: 'upload', label: 'UPLOAD', icon: '↑', svg: null },
        { id: 'dashboard', label: 'DASHBOARD', icon: '■', svg: '/m-dashboard.svg' },
        { id: 'charts', label: 'CHARTS', icon: '📊', svg: '/m-visualization.svg' },
        { id: 'model', label: 'MODEL', icon: '🤖', svg: '/m-model.svg' },
        { id: 'report', label: 'REPORT', icon: '📄', svg: '/m-report.svg' },
    ];

    return (
        <>
            {/* DESKTOP HEADER - Only shows on large screens (≥1024px) */}
            <header className="hidden lg:block border-b-[6px] border-black bg-white">
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
                                                        : tab.id === 'dashboard'
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
                                                    : activeTab === tab.id && tab.id === 'dashboard'
                                                        ? { backgroundColor: '#7f7f7f' }
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

            {/* MOBILE HEADER - Only shows on small screens (<1024px) */}
            <header className="block lg:hidden">
                {/* Top Bar - Compact */}
                <div className="border-b-[3px] border-black bg-white px-4 py-3">
                    <div className="flex items-center justify-between">
                        {/* Logo - Compact */}
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-black flex items-center justify-center">
                                <span className="text-white text-lg font-black">E</span>
                            </div>
                            <div>
                                <h1 className="text-sm font-black leading-none">EXPLAINABLE</h1>
                                <p className="text-xs font-bold text-gray-500">EDA</p>
                            </div>
                        </div>

                        {/* Status - Compact */}
                        <div className="flex items-center gap-2">
                            {isAnalyzing ? (
                                <>
                                    <span className="inline-block w-2 h-2 bg-blue-500 animate-pulse"></span>
                                    <span className="text-xs font-bold">ANALYZING</span>
                                </>
                            ) : (
                                <>
                                    <div className="w-2 h-2 bg-[#00AA00]" />
                                    <span className="text-xs font-bold">READY</span>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bottom Navigation Bar - Fixed */}
                <nav className="fixed bottom-0 left-0 right-0 bg-white border-t-[3px] border-black z-50">
                    <div className="grid grid-cols-5">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => onTabChange(tab.id)}
                                className={`
                                    flex flex-col items-center justify-center py-3 px-2
                                    border-r-[2px] border-black last:border-r-0
                                    transition-all
                                    ${activeTab === tab.id
                                        ? 'font-black'
                                        : 'font-bold opacity-60 hover:opacity-100'
                                    }
                                `}
                                style={
                                    activeTab === tab.id
                                        ? {
                                            backgroundColor:
                                                tab.id === 'upload' ? '#0000FF' :
                                                    tab.id === 'charts' ? '#FFFF00' :
                                                        tab.id === 'model' ? '#00AA00' :
                                                            tab.id === 'dashboard' ? '#7f7f7f' :
                                                                '#000000',
                                            color:
                                                tab.id === 'charts' ? '#000000' : '#FFFFFF'
                                        }
                                        : { backgroundColor: '#FFFFFF', color: '#000000' }
                                }
                            >
                                {tab.svg ? (
                                    <img
                                        src={tab.svg}
                                        alt={tab.label}
                                        className="w-5 h-5 mb-1"
                                        style={
                                            activeTab === tab.id && tab.id === 'charts'
                                                ? { filter: 'brightness(0)' }  // Black for yellow background
                                                : activeTab === tab.id
                                                    ? { filter: 'brightness(0) invert(1)' }  // White for colored backgrounds
                                                    : { filter: 'brightness(0)' }  // Black for inactive
                                        }
                                    />
                                ) : (
                                    <span className="text-lg mb-1">{tab.icon}</span>
                                )}
                                <span className="text-[10px] leading-tight uppercase">{tab.label}</span>
                            </button>
                        ))}
                    </div>
                </nav>
            </header>
        </>
    );
}
