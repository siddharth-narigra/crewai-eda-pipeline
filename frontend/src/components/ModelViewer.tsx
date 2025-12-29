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
        precision?: number;
        recall?: number;
        f1_score?: number;
        n_classes?: number;
        confusion_matrix?: number[][];
        train_r2?: number;
        test_r2?: number;
        rmse?: number;
        mae?: number;
    };
    // Training info
    trained_at?: string;
    training_duration_seconds?: number;
    random_state?: number;
    test_size?: number;
    train_samples?: number;
    test_samples?: number;
    total_samples?: number;
    // Hyperparameters
    hyperparameters?: Record<string, any>;
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

                {/* Desktop/Laptop Layout */}
                <div className="card-brutal-edge hidden lg:block">
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

                {/* Mobile Layout */}
                <div className="card-brutal-edge block lg:hidden">
                    <div className="flex flex-col items-stretch">
                        <div className="w-full h-48 bg-black flex items-center justify-center">
                            <img src="/model.svg" alt="" className="w-24 h-24" />
                        </div>
                        <div className="p-4 flex flex-col justify-center">
                            <p className="text-lg font-black uppercase tracking-tight mb-1">NO MODEL TRAINED</p>
                            <p className="text-xs text-gray-500 tracking-wide">Run the EDA analysis first to train a machine learning model.</p>
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

            {/* Training Info & Data Split Section */}
            <div className="grid grid-cols-2 gap-6 mb-8">
                {/* Training Info */}
                <div className="border-[3px] border-black">
                    <div className="flex items-center gap-3 p-4 border-b-[3px] border-black">
                        <div className="w-2 h-8 bg-black"></div>
                        <h3 className="text-h3">TRAINING INFO</h3>
                    </div>
                    <div className="divide-y divide-gray-200">
                        <div className="flex justify-between items-center p-4">
                            <span className="text-label text-gray-500">TRAINED AT</span>
                            <span className="font-mono text-sm font-bold">
                                {modelStats.trained_at
                                    ? new Date(modelStats.trained_at).toLocaleString()
                                    : 'N/A'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-4">
                            <span className="text-label text-gray-500">DURATION</span>
                            <span className="font-mono font-bold text-xl">
                                {modelStats.training_duration_seconds
                                    ? `${modelStats.training_duration_seconds}s`
                                    : 'N/A'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-4">
                            <span className="text-label text-gray-500">RANDOM SEED</span>
                            <span className="font-mono">{modelStats.random_state || 42}</span>
                        </div>
                    </div>
                </div>

                {/* Data Split */}
                <div className="border-[3px] border-black">
                    <div className="flex items-center gap-3 p-4 border-b-[3px] border-black bg-[#FFFF00]">
                        <div className="w-2 h-8 bg-black"></div>
                        <h3 className="text-h3">DATA SPLIT</h3>
                    </div>
                    <div className="p-4">
                        {/* Visual Split Bar */}
                        <div className="flex h-10 border-[3px] border-black mb-4">
                            <div
                                className="bg-black flex items-center justify-center text-white text-xs font-bold uppercase tracking-wide"
                                style={{ width: `${modelStats.test_size ? (1 - modelStats.test_size) * 100 : 80}%` }}
                            >
                                Train {modelStats.test_size ? Math.round((1 - modelStats.test_size) * 100) : 80}%
                            </div>
                            <div
                                className="bg-[#FFFF00] flex items-center justify-center text-black text-xs font-bold uppercase tracking-wide border-l-[3px] border-black"
                                style={{ width: `${modelStats.test_size ? modelStats.test_size * 100 : 20}%` }}
                            >
                                Test {modelStats.test_size ? Math.round(modelStats.test_size * 100) : 20}%
                            </div>
                        </div>
                        {/* Stats - Creative Layout */}
                        <div className="flex items-stretch">
                            {/* Train */}
                            <div className="flex-1 p-4 bg-black text-white text-center border-[3px] border-black">
                                <p className="text-3xl font-black font-mono">{modelStats.train_samples?.toLocaleString() || 'N/A'}</p>
                                <div className="flex items-center justify-center gap-1 mt-1">
                                    <span className="text-label">TRAIN</span>
                                    <span className="text-xs bg-white text-black px-1 font-bold">{modelStats.test_size ? Math.round((1 - modelStats.test_size) * 100) : 80}%</span>
                                </div>
                            </div>
                            {/* Divider Arrow */}
                            <div className="w-12 bg-[#FFFF00] flex items-center justify-center border-y-[3px] border-black">
                                <span className="text-2xl font-black">+</span>
                            </div>
                            {/* Test */}
                            <div className="flex-1 p-4 bg-[#FFFF00] text-center border-[3px] border-black border-l-0">
                                <p className="text-3xl font-black font-mono">{modelStats.test_samples?.toLocaleString() || 'N/A'}</p>
                                <div className="flex items-center justify-center gap-1 mt-1">
                                    <span className="text-label">TEST</span>
                                    <span className="text-xs bg-black text-white px-1 font-bold">{modelStats.test_size ? Math.round(modelStats.test_size * 100) : 20}%</span>
                                </div>
                            </div>
                            {/* Equals */}
                            <div className="w-12 bg-white flex items-center justify-center border-y-[3px] border-black">
                                <span className="text-2xl font-black">=</span>
                            </div>
                            {/* Total */}
                            <div className="flex-1 p-4 bg-white text-center border-[3px] border-black border-l-0">
                                <p className="text-3xl font-black font-mono">{modelStats.total_samples?.toLocaleString() || 'N/A'}</p>
                                <div className="flex items-center justify-center gap-1 mt-1">
                                    <span className="text-label text-gray-500">TOTAL</span>
                                    <span className="text-xs bg-black text-white px-1 font-bold">100%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Hyperparameters Section */}
            {modelStats.hyperparameters && Object.keys(modelStats.hyperparameters).length > 0 && (
                <div className="mb-8">
                    <div className="bg-white text-black p-4 border-[3px] border-black">
                        <span className="text-h3 font-black">HYPERPARAMETERS</span>
                    </div>
                    <div className="border-[3px] border-black border-t-0">
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                            {Object.entries(modelStats.hyperparameters).map(([key, value], index) => (
                                <div
                                    key={key}
                                    className={`p-4 border-b-[3px] border-r-[3px] border-black ${index % 3 === 0 ? 'bg-black text-white' :
                                        index % 3 === 1 ? 'bg-[#FFFF00] text-black' : 'bg-white text-black'
                                        }`}
                                >
                                    <p className={`text-[10px] uppercase font-bold ${index % 3 === 0 ? 'text-gray-400' : 'text-gray-500'}`}>
                                        {key.toUpperCase().replace(/_/g, ' ')}
                                    </p>
                                    <p className="font-mono font-bold text-lg truncate" title={String(value)}>
                                        {value === null ? 'None' : String(value)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            <hr className="divider-brutal" />

            {/* Performance Metrics Section */}
            <div className="section-accented mb-8">
                <h2 className="text-h2 mb-4">PERFORMANCE METRICS</h2>

                {isClassification ? (
                    <>
                        {/* Primary Metrics Row */}
                        <div className="grid-brutal grid-brutal-4 mb-4">
                            <div className="p-5 border-[3px] border-black bg-[#FFFF00] text-center">
                                <p className="text-stat">{((modelStats.metrics.test_accuracy || 0) * 100).toFixed(1)}%</p>
                                <p className="text-label mt-1">ACCURACY</p>
                            </div>
                            <div className="p-5 border-[3px] border-black bg-white text-center">
                                <p className="text-stat">{((modelStats.metrics.precision || 0) * 100).toFixed(1)}%</p>
                                <p className="text-label mt-1">PRECISION</p>
                            </div>
                            <div className="p-5 border-[3px] border-black bg-white text-center">
                                <p className="text-stat">{((modelStats.metrics.recall || 0) * 100).toFixed(1)}%</p>
                                <p className="text-label mt-1">RECALL</p>
                            </div>
                            <div className="p-5 border-[3px] border-black bg-[#00AA00] text-white text-center">
                                <p className="text-stat">{((modelStats.metrics.f1_score || 0) * 100).toFixed(1)}%</p>
                                <p className="text-label mt-1">F1 SCORE</p>
                            </div>
                        </div>
                        {/* Secondary Info Row */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 border-[3px] border-black bg-[#7f7f7f] text-white text-center">
                                <p className="text-xl font-bold">{((modelStats.metrics.train_accuracy || 0) * 100).toFixed(1)}%</p>
                                <p className="text-label mt-1">TRAIN ACCURACY</p>
                            </div>
                            <div className="p-4 border-[3px] border-black bg-black text-white text-center">
                                <p className="text-xl font-bold">{modelStats.metrics.n_classes || 'N/A'}</p>
                                <p className="text-label mt-1">CLASSES</p>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="grid-brutal grid-brutal-4">
                        <div className="p-5 border-[3px] border-black bg-[#FFFF00] text-center">
                            <p className="text-stat">{(modelStats.metrics.test_r2 || 0).toFixed(4)}</p>
                            <p className="text-label mt-1">TEST R²</p>
                        </div>
                        <div className="p-5 border-[3px] border-black bg-[#7f7f7f] text-white text-center">
                            <p className="text-stat">{(modelStats.metrics.train_r2 || 0).toFixed(4)}</p>
                            <p className="text-label mt-1">TRAIN R²</p>
                        </div>
                        <div className="p-5 border-[3px] border-black bg-white text-center">
                            <p className="text-stat">{(modelStats.metrics.rmse || 0).toFixed(4)}</p>
                            <p className="text-label mt-1">RMSE</p>
                        </div>
                        <div className="p-5 border-[3px] border-black bg-black text-white text-center">
                            <p className="text-stat">{(modelStats.metrics.mae || 0).toFixed(4)}</p>
                            <p className="text-label mt-1">MAE</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Confusion Matrix Section (Classification only) */}
            {isClassification && modelStats.metrics.confusion_matrix && (
                <div className="section-accented mb-8">
                    <h2 className="text-h2 mb-4">CONFUSION MATRIX</h2>
                    <div className="card-brutal p-6">
                        <div className="grid grid-cols-[auto_1fr] gap-8 items-center">
                            {/* Matrix Grid - Left */}
                            <div className="flex flex-col items-center">
                                <div className="text-label text-center mb-2 text-gray-500">PREDICTED</div>
                                <div className="flex items-center">
                                    <div className="flex flex-col justify-center mr-3">
                                        <div className="text-label transform -rotate-90 origin-center whitespace-nowrap text-gray-500">ACTUAL</div>
                                    </div>
                                    <div className="inline-grid gap-0" style={{ gridTemplateColumns: `repeat(${modelStats.metrics.confusion_matrix[0]?.length || 2}, 1fr)` }}>
                                        {modelStats.metrics.confusion_matrix.flatMap((row, i) =>
                                            row.map((cell, j) => {
                                                const isDiagonal = i === j;
                                                return (
                                                    <div
                                                        key={`${i}-${j}`}
                                                        className={`w-20 h-20 flex items-center justify-center border-[3px] border-black font-mono font-bold text-xl ${isDiagonal
                                                            ? 'bg-[#00AA00] text-white'
                                                            : 'bg-[#DC2626] text-white'
                                                            }`}
                                                    >
                                                        {cell}
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                </div>
                                {/* Legend */}
                                <div className="flex gap-6 mt-4 justify-center">
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-4 bg-[#00AA00] border-2 border-black"></div>
                                        <span className="text-sm font-bold">Correct</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-4 bg-[#DC2626] border-2 border-black"></div>
                                        <span className="text-sm font-bold">Errors</span>
                                    </div>
                                </div>
                            </div>

                            {/* Matrix Info - Right */}
                            <div className="border-l-[3px] border-black pl-6 flex-1">
                                <h3 className="text-h3 mb-4">
                                    MATRIX INTERPRETATION
                                </h3>
                                {(() => {
                                    const cm = modelStats.metrics.confusion_matrix!;
                                    const tp = cm[0]?.[0] || 0;
                                    const fn = cm[0]?.[1] || 0;
                                    const fp = cm[1]?.[0] || 0;
                                    const tn = cm[1]?.[1] || 0;
                                    const total = tp + fn + fp + tn;
                                    const correct = tp + tn;
                                    const errors = fp + fn;
                                    const sensitivity = tp / (tp + fn) || 0;
                                    const specificity = tn / (tn + fp) || 0;

                                    return (
                                        <div className="flex gap-4 items-stretch">
                                            {/* Summary Stats - Vertical */}
                                            <div className="flex flex-col">
                                                <div className="flex-1 p-4 bg-[#00AA00] border-[3px] border-black text-white text-center min-w-[100px] flex flex-col justify-center">
                                                    <p className="text-2xl font-black">{correct}</p>
                                                    <p className="text-[10px] uppercase">CORRECT</p>
                                                </div>
                                                <div className="flex-1 p-4 bg-[#DC2626] border-[3px] border-black border-t-0 text-white text-center flex flex-col justify-center">
                                                    <p className="text-2xl font-black">{errors}</p>
                                                    <p className="text-[10px] uppercase">ERRORS</p>
                                                </div>
                                            </div>
                                            {/* Rates */}
                                            <div className="flex-1 flex flex-col border-[3px] border-black">
                                                <div className="flex-1 flex justify-between items-center p-3 bg-white border-b border-gray-200">
                                                    <span className="text-label text-gray-500">SENSITIVITY (TPR)</span>
                                                    <span className="font-mono font-bold">{(sensitivity * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="flex-1 flex justify-between items-center p-3 bg-white border-b border-gray-200">
                                                    <span className="text-label text-gray-500">SPECIFICITY (TNR)</span>
                                                    <span className="font-mono font-bold">{(specificity * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="flex-1 flex justify-between items-center p-3 bg-black text-white">
                                                    <span className="text-label">ERROR RATE</span>
                                                    <span className="font-mono font-bold">{((errors / total) * 100).toFixed(1)}%</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>
                        </div>
                    </div>
                </div>
            )}

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
            )
            }

            {/* Model Visualizations Section */}
            {
                modelCharts.length > 0 && (
                    <div className="section-accented mb-8">
                        <h2 className="text-h2 mb-4">MODEL VISUALIZATIONS</h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {modelCharts.map((chart) => (
                                <div
                                    key={chart.name}
                                    onClick={() => setSelectedChart(chart.name)}
                                    className="card-brutal cursor-pointer hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0_#000] transition-all"
                                >
                                    <img
                                        src={`${apiBaseUrl}/charts/${chart.name}`}
                                        alt={chart.name}
                                        className="w-full aspect-[4/3] object-cover border-b-[3px] border-black"
                                    />
                                    <div className="p-2">
                                        <p className="text-mono text-xs truncate">
                                            {chart.name.replace('.png', '').replace(/_/g, ' ').toUpperCase()}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            }

            {/* Chart Modal */}
            {
                selectedChart && (
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
                )
            }

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
        </div >
    );
}
