'use client';

import { ComparisonData } from '@/lib/api';

interface BeforeAfterPanelProps {
    data: ComparisonData;
}

export default function BeforeAfterPanel({ data }: BeforeAfterPanelProps) {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="w-2 h-8 bg-black" />
                <h2 className="text-h2">BEFORE → AFTER</h2>
            </div>

            {/* Comparison Grid */}
            <div className="grid grid-cols-3 gap-4">
                {/* Before Column */}
                <div className="card-brutal">
                    <div className="bg-[#888] text-white p-3 -m-[24px] mb-4 -mt-[24px] border-b-[3px] border-black">
                        <span className="text-label">BEFORE CLEANING</span>
                    </div>
                    <div className="space-y-4 mt-8">
                        <div>
                            <div className="text-stat">{data.before.missing_total}</div>
                            <div className="text-label">MISSING VALUES</div>
                        </div>
                        <div>
                            <div className="text-mono text-2xl font-bold">{data.before.completeness}%</div>
                            <div className="text-label">COMPLETENESS</div>
                        </div>
                    </div>
                </div>

                {/* Improvement Column */}
                <div className="card-brutal-filled">
                    <div className="bg-[#00AA00] text-white p-3 -m-[24px] mb-4 -mt-[24px]">
                        <span className="text-label">IMPROVEMENT</span>
                    </div>
                    <div className="space-y-4 mt-8">
                        <div>
                            <div className="text-stat text-white">+{data.improvement.missing_fixed}</div>
                            <div className="text-label text-white/70">VALUES FIXED</div>
                        </div>
                        <div>
                            <div className="text-mono text-2xl font-bold text-[#00FF00]">
                                +{data.improvement.completeness_gain}%
                            </div>
                            <div className="text-label text-white/70">COMPLETENESS GAIN</div>
                        </div>
                    </div>
                </div>

                {/* After Column */}
                <div className="card-brutal" style={{ background: '#FFFF00' }}>
                    <div className="bg-black text-white p-3 -m-[24px] mb-4 -mt-[24px]">
                        <span className="text-label">AFTER CLEANING</span>
                    </div>
                    <div className="space-y-4 mt-8">
                        <div>
                            <div className="text-stat">{data.after.missing_total}</div>
                            <div className="text-label">MISSING VALUES</div>
                        </div>
                        <div>
                            <div className="text-mono text-2xl font-bold">{data.after.completeness}%</div>
                            <div className="text-label">COMPLETENESS</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Column-Level Changes */}
            {data.column_changes.length > 0 && (
                <div className="card-brutal">
                    <h3 className="text-h3 mb-4">COLUMNS FIXED</h3>
                    <table className="table-brutal">
                        <thead>
                            <tr>
                                <th>COLUMN</th>
                                <th>BEFORE</th>
                                <th>AFTER</th>
                                <th>FIXED</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.column_changes.map((change) => (
                                <tr key={change.column}>
                                    <td className="text-mono font-semibold">{change.column}</td>
                                    <td className="text-mono">{change.before_missing} missing</td>
                                    <td className="text-mono">{change.after_missing} missing</td>
                                    <td>
                                        <span className="tag-brutal-success">+{change.fixed}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Cleaning Operations Log */}
            {data.cleaning_operations.length > 0 && (
                <div className="section-accented">
                    <h3 className="text-h3 mb-4">OPERATIONS PERFORMED</h3>
                    <div className="space-y-2">
                        {data.cleaning_operations.map((op, i) => (
                            <div key={i} className="flex items-start gap-3 p-3 bg-[#F0F0F0] border-l-[4px] border-black">
                                <span className="text-mono font-bold">■</span>
                                <div>
                                    <span className="text-mono text-sm">
                                        {op.column && <strong>{op.column}:</strong>} {op.strategy || op.message || JSON.stringify(op)}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
