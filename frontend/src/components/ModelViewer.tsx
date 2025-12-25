'use client';

import { useState } from 'react';

interface ChartInfo {
    name: string;
    category?: string;
}

interface ModelStats {
    status: string;
    model_type: string;
    problem_type: string;
    target_column: string;
    features: string[];
    feature_count: number;
    metrics: {
        train_accuracy?: number;
        test_accuracy?: number;
        n_classes?: number;
        train_r2?: number;
        test_r2?: number;
        rmse?: number;
    };
    top_features: Record<string, number>;
    file_size_mb: number;
    model_path: string;
}

interface ModelViewerProps {
    modelStats: ModelStats | null;
    apiBaseUrl: string;
    charts: ChartInfo[];
}

// Define which chart patterns are model-relevant
const MODEL_CHART_PATTERNS = [
    'feature_importance',
    'shap_summary',
    'lime_explanation',
    'impact_',
];

export default function ModelViewer({ modelStats, apiBaseUrl, charts }: ModelViewerProps) {
    const [selectedChart, setSelectedChart] = useState<string | null>(null);

    // Filter charts to only show model-relevant ones
    const modelCharts = charts.filter(chart =>
        MODEL_CHART_PATTERNS.some(pattern => chart.name.includes(pattern))
    );

    if (!modelStats) {
        return (
            <div>
                <h1 className="text-h1 mb-8">TRAINED MODEL</h1>
                <div className="card-brutal-edge">
                    <div className="flex items-stretch">
                        <div className="aspect-square w-56 bg-black flex items-center justify-center shrink-0">
                            <img src="/model.svg" alt="" className="w-32 h-32" />
                        </div>
                        <div className="flex-1 p-8 flex flex-col justify-center">
                            <p className="text-xl font-black uppercase tracking-tight mb-1">NO MODEL TRAINED</p>
                            <p className="text-sm text-gray-500 tracking-wide">Run the EDA analysis first to train a machine learning model.</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const isClassification = modelStats.problem_type === 'classification';
    const topFeatures = Object.entries(modelStats.top_features || {}).slice(0, 5);
    const maxImportance = topFeatures.length > 0 ? Math.max(...topFeatures.map(([_, v]) => v)) : 1;

    return (
        <div>
            {/* Header with download button */}
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-h1">TRAINED MODEL</h1>
                <a
                    href={`${apiBaseUrl}/api/model/download`}
                    download
                    className="btn-brutal btn-brutal-action"
                >
                    ■ DOWNLOAD MODEL (.pkl)
                </a>
            </div>

            {/* Model Info Stats Grid - matching Dashboard StatCard pattern */}
            <div className="grid-brutal grid-brutal-4 mb-8">
                <div className="p-4 border-[3px] border-black bg-[#00AA00] text-white">
                    <p className="text-label text-green-200 mb-2">MODEL TYPE</p>
                    <p className="text-h3">{modelStats.model_type === 'RandomForestClassifier' ? 'RF CLASSIFIER' : 'RF REGRESSOR'}</p>
                </div>
                <div className="p-4 border-[3px] border-black bg-black text-white">
                    <p className="text-label text-gray-400 mb-2">PROBLEM TYPE</p>
                    <p className="text-h3 uppercase">{modelStats.problem_type}</p>
                </div>
                <div className="p-4 border-[3px] border-black bg-white">
                    <p className="text-label text-gray-500 mb-2">TARGET</p>
                    <p className="text-mono font-bold uppercase truncate">{modelStats.target_column}</p>
                </div>
                <div className="p-4 border-[3px] border-black bg-[#FFFF00]">
                    <p className="text-label mb-2">FEATURES</p>
                    <p className="text-stat">{modelStats.feature_count}</p>
                </div>
            </div>

            <hr className="divider-brutal" />

            {/* Performance Metrics Section */}
            <div className="section-accented mb-8">
                <h2 className="text-h2 mb-4">PERFORMANCE METRICS</h2>

                {isClassification ? (
                    <div className="grid-brutal grid-brutal-3">
                        <div className="p-6 border-[3px] border-black bg-[#7f7f7f] text-white text-center">
                            <p className="text-stat">{((modelStats.metrics.train_accuracy || 0) * 100).toFixed(1)}%</p>
                            <p className="text-label mt-2">TRAIN ACCURACY</p>
                        </div>
                        <div className="p-6 border-[3px] border-black bg-[#FFFF00] text-center">
                            <p className="text-stat">{((modelStats.metrics.test_accuracy || 0) * 100).toFixed(1)}%</p>
                            <p className="text-label mt-2">TEST ACCURACY</p>
                        </div>
                        <div className="p-6 border-[3px] border-black bg-black text-white text-center">
                            <p className="text-stat">{modelStats.metrics.n_classes || 'N/A'}</p>
                            <p className="text-label mt-2">CLASSES</p>
                        </div>
                    </div>
                ) : (
                    <div className="grid-brutal grid-brutal-3">
                        <div className="p-6 border-[3px] border-black bg-[#7f7f7f] text-white text-center">
                            <p className="text-stat">{(modelStats.metrics.train_r2 || 0).toFixed(4)}</p>
                            <p className="text-label mt-2">TRAIN R²</p>
                        </div>
                        <div className="p-6 border-[3px] border-black bg-[#FFFF00] text-center">
                            <p className="text-stat">{(modelStats.metrics.test_r2 || 0).toFixed(4)}</p>
                            <p className="text-label mt-2">TEST R²</p>
                        </div>
                        <div className="p-6 border-[3px] border-black bg-black text-white text-center">
                            <p className="text-stat">{(modelStats.metrics.rmse || 0).toFixed(4)}</p>
                            <p className="text-label mt-2">RMSE</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Top Features Section */}
            {topFeatures.length > 0 && (
                <div className="section-accented mb-8">
                    <h2 className="text-h2 mb-4">TOP FEATURES</h2>
                    <div className="card-brutal p-6">
                        <div className="space-y-4">
                            {topFeatures.map(([feature, importance], index) => (
                                <div key={feature} className="flex items-center gap-4">
                                    <span className="text-label w-8 font-bold">{String(index + 1).padStart(2, '0')}</span>
                                    <span className="font-mono font-bold w-48 truncate">{feature}</span>
                                    <div className="flex-1 h-6 bg-gray-100 border-[2px] border-black relative overflow-hidden">
                                        <div
                                            className="h-full bg-black transition-all"
                                            style={{ width: `${(importance / maxImportance) * 100}%` }}
                                        />
                                    </div>
                                    <span className="font-mono text-sm w-20 text-right font-bold">
                                        {(importance * 100).toFixed(2)}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Model Visualizations Section */}
            {modelCharts.length > 0 && (
                <div className="section-accented mb-8">
                    <h2 className="text-h2 mb-4">MODEL VISUALIZATIONS</h2>
                    <div className="grid-brutal grid-brutal-2">
                        {modelCharts.map((chart) => (
                            <div
                                key={chart.name}
                                onClick={() => setSelectedChart(chart.name)}
                                className="card-brutal cursor-pointer hover:bg-[#F0F0F0] transition-colors"
                            >
                                <img
                                    src={`${apiBaseUrl}/charts/${chart.name}`}
                                    alt={chart.name}
                                    className="w-full aspect-video object-cover border-b-[3px] border-black"
                                />
                                <div className="p-3">
                                    <p className="text-mono text-sm truncate">
                                        {chart.name.replace('.png', '').replace(/_/g, ' ').toUpperCase()}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Chart Modal */}
            {selectedChart && (
                <div
                    className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8"
                    onClick={() => setSelectedChart(null)}
                >
                    <div className="max-w-5xl w-full" onClick={e => e.stopPropagation()}>
                        <div className="bg-white border-[6px] border-black">
                            <div className="bg-black text-white p-3 flex items-center justify-between">
                                <span className="text-mono">{selectedChart}</span>
                                <button
                                    onClick={() => setSelectedChart(null)}
                                    className="text-h3 hover:text-[#FF0000]"
                                >
                                    ✕
                                </button>
                            </div>
                            <img
                                src={`${apiBaseUrl}/charts/${selectedChart}`}
                                alt={selectedChart}
                                className="w-full"
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Model File Info - Compact */}
            <div className="card-brutal-edge">
                <div className="flex items-stretch">
                    {/* File Info */}
                    <div className="flex-1 p-4 flex items-center justify-between">
                        <div>
                            <p className="text-label text-gray-500 mb-1">EXPORTED MODEL</p>
                            <div className="flex items-center gap-2">
                                <p className="font-mono font-bold">
                                    {modelStats.model_path.split('/').pop()}
                                </p>
                                <span className="tag-brutal text-xs">.PKL</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-label text-gray-500">SIZE</p>
                            <p className="font-mono font-bold text-xl">{modelStats.file_size_mb} MB</p>
                        </div>
                    </div>

                    {/* Download Button - enhanced UX */}
                    <a
                        href={`${apiBaseUrl}/api/model/download`}
                        download
                        className="w-20 shrink-0 bg-black text-white flex flex-col items-center justify-center cursor-pointer group transition-all hover:bg-[#222]"
                        title="Download trained model file"
                    >
                        <span className="text-2xl transition-transform group-hover:translate-y-1 group-hover:text-[#FFFF00]">↓</span>
                        <span className="text-[10px] mt-1 opacity-70 group-hover:opacity-100">DOWNLOAD</span>
                    </a>
                </div>
            </div>
        </div>
    );
}
