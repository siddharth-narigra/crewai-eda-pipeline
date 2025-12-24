/**
 * API utility functions for communicating with the FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UploadResponse {
    status: string;
    filename: string;
    file_path: string;
    rows: number;
    columns: number;
    column_names: string[];
    dtypes: Record<string, string>;
    memory_mb: number;
}

export interface EDAStatusResponse {
    status: 'idle' | 'running' | 'completed' | 'error';
    message: string;
    progress: number;
    report_path?: string;
    html_path?: string;
}

export interface ChartInfo {
    name: string;
    url: string;
    type: string;
}

export interface ChartsResponse {
    charts: ChartInfo[];
    count: number;
}

export interface ReportResponse {
    format: string;
    content: string;
}

/**
 * Upload a CSV file for analysis.
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
}

/**
 * Start the EDA pipeline.
 */
export async function startEDA(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/eda/run`, {
        method: 'POST',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start EDA');
    }

    return response.json();
}

/**
 * Get the current EDA status.
 */
export async function getEDAStatus(): Promise<EDAStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/eda/status`);
    return response.json();
}

/**
 * Get the generated report.
 */
export async function getReport(format: 'md' | 'html' = 'md'): Promise<ReportResponse> {
    const response = await fetch(`${API_BASE_URL}/api/eda/report?format=${format}`);

    if (!response.ok) {
        throw new Error('Report not found');
    }

    return response.json();
}

/**
 * Get list of generated charts.
 */
export async function getCharts(): Promise<ChartsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/eda/charts`);
    return response.json();
}

/**
 * Get SHAP summary data.
 */
export async function getSHAPSummary(): Promise<{
    status: string;
    plot_url: string;
    feature_importance: Record<string, number>;
}> {
    const response = await fetch(`${API_BASE_URL}/api/xai/shap`);

    if (!response.ok) {
        throw new Error('SHAP data not available');
    }

    return response.json();
}

/**
 * Get model info.
 */
export async function getModelInfo(): Promise<{
    status: string;
    model_type: string;
    target_column: string;
    features: string[];
    metrics: Record<string, any>;
}> {
    const response = await fetch(`${API_BASE_URL}/api/xai/model`);

    if (!response.ok) {
        throw new Error('Model info not available');
    }

    return response.json();
}

/**
 * Get full chart URL.
 */
export function getChartUrl(chartName: string): string {
    return `${API_BASE_URL}/charts/${chartName}`;
}

/**
 * Get download URL for cleaned dataset.
 */
export function getDownloadUrl(): string {
    return `${API_BASE_URL}/api/data/download`;
}

/**
 * Before/After comparison data.
 */
export interface ComparisonData {
    before: {
        rows: number;
        columns: number;
        missing_total: number;
        missing_percent: number;
        completeness: number;
    };
    after: {
        rows: number;
        columns: number;
        missing_total: number;
        missing_percent: number;
        completeness: number;
    };
    improvement: {
        missing_fixed: number;
        completeness_gain: number;
    };
    column_changes: Array<{
        column: string;
        before_missing: number;
        after_missing: number;
        fixed: number;
    }>;
    cleaning_operations: Array<Record<string, any>>;
}

/**
 * Get before/after comparison stats.
 */
export async function getComparison(): Promise<ComparisonData> {
    const response = await fetch(`${API_BASE_URL}/api/data/comparison`);

    if (!response.ok) {
        throw new Error('Comparison data not available');
    }

    return response.json();
}

/**
 * Get model recommendations.
 */
export async function getModelRecommendations(): Promise<{
    status: string;
    recommendations: {
        target_analysis: Record<string, any>;
        data_characteristics: Record<string, any>;
        recommended_models: Array<{
            model: string;
            priority: number;
            reason: string;
        }>;
        reasoning: string[];
    };
}> {
    const response = await fetch(`${API_BASE_URL}/api/model/recommendations`);

    if (!response.ok) {
        throw new Error('Recommendations not available');
    }

    return response.json();
}
