'use client';

import { ChartInfo } from '@/lib/api';

interface ChartGalleryProps {
    charts: ChartInfo[];
    onChartClick: (chartName: string) => void;
    apiBaseUrl: string;
}

export default function ChartGallery({ charts, onChartClick, apiBaseUrl }: ChartGalleryProps) {
    // Group charts by type
    const groupedCharts = charts.reduce((acc, chart) => {
        const type = chart.type.toUpperCase();
        if (!acc[type]) acc[type] = [];
        acc[type].push(chart);
        return acc;
    }, {} as Record<string, ChartInfo[]>);

    const typeLabels: Record<string, string> = {
        'DIST': 'DISTRIBUTIONS',
        'CAT': 'CATEGORICAL',
        'CORRELATION': 'CORRELATIONS',
        'IMPACT': 'CLEANING IMPACT',
        'SHAP': 'XAI / SHAP',
        'LIME': 'XAI / LIME',
        'DATA': 'DATA QUALITY',
        'BOX': 'BOX PLOTS',
        'FEATURE': 'FEATURE IMPORTANCE',
        'OTHER': 'OTHER',
    };

    return (
        <div className="space-y-8">
            {Object.entries(groupedCharts).map(([type, typeCharts]) => (
                <div key={type}>
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-2 h-6 bg-black" />
                        <h3 className="text-h3">{typeLabels[type] || type}</h3>
                        <span className="tag-brutal">{typeCharts.length}</span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {typeCharts.map((chart) => (
                            <div
                                key={chart.name}
                                onClick={() => onChartClick(chart.name)}
                                className="card-brutal cursor-pointer hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0_#000] transition-all"
                            >
                                <div className="aspect-[4/3] bg-[#F0F0F0] border-b-[3px] border-black overflow-hidden">
                                    <img
                                        src={`${apiBaseUrl}/charts/${chart.name}`}
                                        alt={chart.name}
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                                <div className="p-3">
                                    <p className="text-mono text-sm truncate">{chart.name}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}
