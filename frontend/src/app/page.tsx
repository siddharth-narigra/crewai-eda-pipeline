'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import FileUploader from '@/components/FileUploader';
import StatCard from '@/components/StatCard';
import ChartGallery from '@/components/ChartGallery';
import ProgressBar from '@/components/ProgressBar';
import BeforeAfterPanel from '@/components/BeforeAfterPanel';
import ReportViewer from '@/components/ReportViewer';
import {
  UploadResponse,
  startEDA,
  getEDAStatus,
  getCharts,
  getReport,
  getComparison,
  getDownloadUrl,
  ChartInfo,
  EDAStatusResponse,
  ComparisonData
} from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [edaStatus, setEdaStatus] = useState<EDAStatusResponse | null>(null);
  const [charts, setCharts] = useState<ChartInfo[]>([]);
  const [report, setReport] = useState<string>('');
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [activeTab, setActiveTab] = useState<string>('upload');
  const [selectedChart, setSelectedChart] = useState<string | null>(null);
  const [showAllColumns, setShowAllColumns] = useState<boolean>(false);

  const isAnalyzing = edaStatus?.status === 'running';

  // Poll for EDA status when running
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isAnalyzing) {
      interval = setInterval(async () => {
        const status = await getEDAStatus();
        setEdaStatus(status);

        if (status.status === 'completed') {
          // Fetch all results
          const chartsData = await getCharts();
          setCharts(chartsData.charts);

          const reportData = await getReport('md');
          setReport(reportData.content);

          // Fetch before/after comparison
          try {
            const comparisonData = await getComparison();
            setComparison(comparisonData);
          } catch (e) {
            console.log('Comparison data not available');
          }

          setActiveTab('dashboard');
        }
      }, 2000);
    }

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const handleUploadSuccess = (data: UploadResponse) => {
    setUploadData(data);
  };

  const handleStartAnalysis = async () => {
    try {
      await startEDA();
      setEdaStatus({ status: 'running', message: 'Starting...', progress: 0 });
    } catch (error) {
      console.error('Failed to start EDA:', error);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isAnalyzing={isAnalyzing}
      />

      <main className="container-brutal py-8">
        {/* ═══════════════════════════════════════════════════════════
            UPLOAD TAB
            ═══════════════════════════════════════════════════════════ */}
        {activeTab === 'upload' && (
          <div>
            {/* Hero */}
            <div className="mb-12">
              <h1 className="text-hero">
                ANALYZE<br />
                YOUR<br />
                <span className="bg-[#FFFF00] px-2">DATA</span>
              </h1>
              <p className="text-body mt-4 max-w-xl">
                Upload a dataset and let AI agents perform comprehensive exploratory
                data analysis with full transparency and explainability.
              </p>
            </div>

            {/* Upload Zone */}
            <div className="max-w-2xl">
              <FileUploader onUploadSuccess={handleUploadSuccess} />
            </div>

            {/* Data Preview */}
            {uploadData && (
              <div className="mt-8">
                <hr className="divider-brutal-thick" />

                <h2 className="text-h2 mb-6">DATA LOADED</h2>

                {/* Stats Grid */}
                <div className="grid-brutal grid-brutal-4 mb-6">
                  <StatCard value={uploadData.rows} label="ROWS" />
                  <StatCard value={uploadData.columns} label="COLUMNS" variant="filled" />
                  <StatCard value={`${uploadData.memory_mb}MB`} label="SIZE" />
                  <StatCard
                    value={uploadData.filename.split('.').pop()?.toUpperCase() || 'FILE'}
                    label="FORMAT"
                    variant="accent"
                  />
                </div>

                {/* Column Table */}
                <div
                  className="border-[4px] border-black bg-white p-6 mb-6"
                  style={{ boxShadow: '8px 8px 0px 0px #000000' }}
                >
                  <h3 className="text-xl font-black uppercase mb-4 pb-2 border-b-[4px] border-black">COLUMNS</h3>
                  <div className="border-[3px] border-black overflow-hidden">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-black text-white">
                          <th className="p-3 text-left font-bold uppercase text-sm w-16">#</th>
                          <th className="p-3 text-left font-bold uppercase text-sm">NAME</th>
                          <th className="p-3 text-left font-bold uppercase text-sm w-32">TYPE</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(showAllColumns ? uploadData.column_names : uploadData.column_names.slice(0, 10)).map((col, i) => (
                          <tr
                            key={col}
                            className={`border-b-2 border-black ${i % 2 === 0 ? 'bg-white' : 'bg-[#F5F5F5]'} hover:bg-[#FFFF00] transition-colors`}
                          >
                            <td className="p-3 font-mono font-bold">{i + 1}</td>
                            <td className="p-3 font-mono font-semibold">{col}</td>
                            <td className="p-3">
                              <span
                                className="inline-block px-3 py-1 text-xs font-bold uppercase border-[2px] border-black bg-white"
                                style={{ boxShadow: '2px 2px 0px 0px #000000' }}
                              >
                                {uploadData.dtypes[col]}
                              </span>
                            </td>
                          </tr>
                        ))}
                        {uploadData.column_names.length > 10 && (
                          <tr
                            onClick={() => setShowAllColumns(!showAllColumns)}
                            className="cursor-pointer bg-[#F0F0F0] hover:bg-[#FFFF00] transition-colors border-t-[3px] border-black"
                          >
                            <td colSpan={3} className="p-4 text-center font-bold uppercase text-sm">
                              {showAllColumns ? (
                                <span>▲ SHOW LESS</span>
                              ) : (
                                <span>▼ + {uploadData.column_names.length - 10} MORE COLUMNS</span>
                              )}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Start Button */}
                <button
                  onClick={handleStartAnalysis}
                  disabled={isAnalyzing}
                  className="btn-brutal btn-brutal-action text-lg px-12 py-4"
                >
                  {isAnalyzing ? (
                    <>
                      <span className="spinner-brutal" /> ANALYZING...
                    </>
                  ) : (
                    <>■ START ANALYSIS</>
                  )}
                </button>
              </div>
            )}

            {/* Progress */}
            {isAnalyzing && edaStatus && (
              <div className="mt-8">
                <ProgressBar
                  progress={edaStatus.progress}
                  status={edaStatus.message}
                  stages={edaStatus.stages}
                  activityLog={edaStatus.activity_log}
                />
              </div>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            DASHBOARD TAB
            ═══════════════════════════════════════════════════════════ */}
        {activeTab === 'dashboard' && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-h1">ANALYSIS DASHBOARD</h1>
              {charts.length > 0 && (
                <a
                  href={getDownloadUrl()}
                  className="btn-brutal btn-brutal-action"
                  download
                >
                  ■ DOWNLOAD CLEANED DATA
                </a>
              )}
            </div>

            {charts.length === 0 ? (
              <div className="card-brutal p-12 text-center">
                <p className="text-h3">NO DATA AVAILABLE</p>
                <p className="text-label mt-2">RUN AN ANALYSIS FIRST</p>
              </div>
            ) : (
              <>
                {/* Quick Stats */}
                {uploadData && (
                  <div className="grid-brutal grid-brutal-4 mb-8">
                    <StatCard value={uploadData.rows} label="TOTAL ROWS" />
                    <StatCard value={uploadData.columns} label="FEATURES" variant="filled" />
                    <StatCard value={charts.length} label="CHARTS GENERATED" />
                    <StatCard
                      value={comparison ? `${comparison.after.completeness}%` : '100%'}
                      label="COMPLETENESS"
                      variant="accent"
                    />
                  </div>
                )}

                {/* Before/After Comparison */}
                {comparison && (
                  <div className="mb-8">
                    <BeforeAfterPanel data={comparison} />
                  </div>
                )}

                {/* Key Charts Preview */}
                <div className="section-accented mb-8">
                  <h2 className="text-h2 mb-4">KEY VISUALIZATIONS</h2>
                  <div className="grid-brutal grid-brutal-3">
                    {charts.slice(0, 3).map((chart) => (
                      <div
                        key={chart.name}
                        onClick={() => {
                          setSelectedChart(chart.name);
                          setActiveTab('charts');
                        }}
                        className="card-brutal cursor-pointer hover:bg-[#F0F0F0]"
                      >
                        <img
                          src={`${API_BASE_URL}/charts/${chart.name}`}
                          alt={chart.name}
                          className="w-full aspect-video object-cover border-b-[3px] border-black"
                        />
                        <p className="text-mono text-sm p-3">{chart.name}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-4">
                  <button
                    onClick={() => setActiveTab('charts')}
                    className="btn-brutal"
                  >
                    VIEW ALL CHARTS →
                  </button>
                  <button
                    onClick={() => setActiveTab('report')}
                    className="btn-brutal btn-brutal-outline"
                  >
                    READ FULL REPORT →
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            CHARTS TAB
            ═══════════════════════════════════════════════════════════ */}
        {activeTab === 'charts' && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-h1">VISUALIZATIONS</h1>
              <span className="tag-brutal">{charts.length} CHARTS</span>
            </div>

            {charts.length === 0 ? (
              <div className="card-brutal p-12 text-center">
                <p className="text-h3">NO CHARTS YET</p>
                <p className="text-label mt-2">RUN AN ANALYSIS FIRST</p>
              </div>
            ) : (
              <ChartGallery
                charts={charts}
                onChartClick={setSelectedChart}
                apiBaseUrl={API_BASE_URL}
              />
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
                      src={`${API_BASE_URL}/charts/${selectedChart}`}
                      alt={selectedChart}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            REPORT TAB
            ═══════════════════════════════════════════════════════════ */}
        {activeTab === 'report' && (
          <div>
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-h1">ANALYSIS REPORT</h1>
              {report && (
                <a
                  href={`${API_BASE_URL}/api/report/download`}
                  download
                  className="btn-brutal btn-brutal-action"
                >
                  ■ DOWNLOAD REPORT
                </a>
              )}
            </div>

            {report ? (
              <div className="grid grid-cols-[220px_1fr] gap-6">
                {/* Table of Contents - Dynamic */}
                <aside className="sticky top-4 self-start">
                  <div className="card-brutal-filled">
                    <h3 className="text-h3 text-white mb-4">SECTIONS</h3>
                    <nav className="flex flex-col gap-2">
                      {/* Extract sections from report (## headings) */}
                      {report.split('\n')
                        .filter(line => line.startsWith('## ') || line.startsWith('# '))
                        .map((line) => {
                          const level = line.startsWith('## ') ? 2 : 1;
                          const text = line.replace(/^##?\s*\d*\.?\s*/, '').trim();
                          const id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-');
                          return (
                            <a
                              key={id}
                              href={`#${id}`}
                              className={`text-label text-white hover:text-[#FFFF00] transition-colors ${level === 1 ? 'font-bold' : 'pl-2 text-sm'}`}
                            >
                              {level === 1 ? '●' : '■'} {text.toUpperCase().slice(0, 20)}{text.length > 20 ? '...' : ''}
                            </a>
                          );
                        })}
                    </nav>
                  </div>
                </aside>

                {/* Report Content */}
                <div className="card-brutal p-8">
                  <ReportViewer content={report} apiBaseUrl={API_BASE_URL} />
                </div>
              </div>
            ) : (
              <div className="card-brutal p-12 text-center">
                <p className="text-h3">NO REPORT YET</p>
                <p className="text-label mt-2">RUN AN ANALYSIS FIRST</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t-[6px] border-black mt-12 py-6">
        <div className="container-brutal flex items-center justify-between">
          <span className="text-label">EXPLAINABLE EDA SYSTEM V2.0</span>
          <span className="text-label text-[#888]">BUILT WITH CREWAI + SHAP + LIME</span>
        </div>
      </footer>
    </div>
  );
}
