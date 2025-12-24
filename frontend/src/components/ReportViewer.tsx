'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Components } from 'react-markdown';
import React from 'react';

interface ReportViewerProps {
    content: string;
    apiBaseUrl?: string;
}

export default function ReportViewer({ content, apiBaseUrl = 'http://localhost:8000' }: ReportViewerProps) {
    // Preprocess content - strip wrapping code fences and embed chart references
    let processedContent = content
        .replace(/^```\s*\n?/, '')  // Remove leading ```
        .replace(/\n?```\s*$/, ''); // Remove trailing ```

    // Convert chart file references to markdown images
    // Pattern: charts/filename.png or output/charts/filename.png
    processedContent = processedContent.replace(
        /(?:output\/)?charts\/([a-zA-Z0-9_-]+\.png)/g,
        (match, filename) => {
            // Handle the lime_explanation.png -> lime_explanation_row_0.png mapping
            const correctedFilename = filename === 'lime_explanation.png'
                ? 'lime_explanation_row_0.png'
                : filename;
            return `![Chart: ${filename}](${apiBaseUrl}/charts/${correctedFilename})`;
        }
    );

    // Helper to generate ID from heading text
    const generateId = (children: React.ReactNode): string => {
        const text = String(children).replace(/^\d+\.\s*/, '').trim();
        return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-');
    };

    // Check if heading is an executive summary
    const isExecutiveSummary = (text: string): boolean => {
        return text.toLowerCase().includes('executive summary') ||
            text.toLowerCase().includes('summary');
    };

    // Custom components for markdown rendering with brutalist styling
    const components: Components = {
        // Main title (h1) - Large, prominent
        h1: ({ children }) => {
            const id = generateId(children);
            const text = String(children);
            return (
                <div className="mb-10">
                    <h1
                        id={id}
                        className="text-4xl font-black uppercase tracking-tight pb-4 mb-2 scroll-mt-4"
                        style={{ borderBottom: '6px solid #000000' }}
                    >
                        {children}
                    </h1>
                    {isExecutiveSummary(text) && (
                        <div className="inline-block px-3 py-1 bg-black text-white text-xs font-bold uppercase">
                            KEY INSIGHTS
                        </div>
                    )}
                </div>
            );
        },

        // Section headers (h2) - Clear separation with accent
        h2: ({ children }) => {
            const id = generateId(children);
            const text = String(children);
            const isSummary = isExecutiveSummary(text);
            return (
                <div className="mt-12 mb-6">
                    <div
                        className={`flex items-center gap-4 pb-3 border-b-[4px] border-black`}
                    >
                        <div
                            className="w-3 h-8"
                            style={{ backgroundColor: '#000000' }}
                        />
                        <h2 id={id} className="text-2xl font-black uppercase tracking-tight scroll-mt-4">
                            {children}
                        </h2>
                    </div>
                </div>
            );
        },

        // Subsections (h3)
        h3: ({ children }) => {
            const id = generateId(children);
            return (
                <h3
                    id={id}
                    className="text-xl font-bold uppercase tracking-tight mb-4 mt-8 scroll-mt-4 pl-4"
                    style={{ borderLeft: '4px solid #000000' }}
                >
                    {children}
                </h3>
            );
        },

        h4: ({ children }) => (
            <h4 className="text-lg font-bold uppercase mb-3 mt-6 text-gray-800">
                {children}
            </h4>
        ),
        h5: ({ children }) => (
            <h5 className="text-base font-bold uppercase mb-2 mt-4 text-gray-700">
                {children}
            </h5>
        ),
        h6: ({ children }) => (
            <h6 className="text-sm font-bold uppercase mb-2 mt-3 text-gray-600">
                {children}
            </h6>
        ),

        // Paragraphs - Better spacing
        p: ({ children }) => (
            <p className="mb-5 leading-relaxed text-gray-800">
                {children}
            </p>
        ),

        // Tables - Enhanced styling
        table: ({ children }) => (
            <div className="my-8">
                <div className="overflow-x-auto border-[3px] border-black shadow-[4px_4px_0px_0px_#000000]">
                    <table className="w-full border-collapse">
                        {children}
                    </table>
                </div>
            </div>
        ),
        thead: ({ children }) => (
            <thead className="bg-black text-white">
                {children}
            </thead>
        ),
        tbody: ({ children }) => (
            <tbody className="[&>tr]:hover:bg-[#FFFF00] [&>tr]:transition-colors [&>tr]:cursor-default">
                {children}
            </tbody>
        ),
        tr: ({ children }) => (
            <tr className="border-b-2 border-black even:bg-gray-50">
                {children}
            </tr>
        ),
        th: ({ children }) => (
            <th className="p-4 text-left font-bold uppercase text-sm border-r border-gray-600 last:border-r-0">
                {children}
            </th>
        ),
        td: ({ children }) => (
            <td className="p-4 text-sm border-r border-gray-100 last:border-r-0">
                {children}
            </td>
        ),

        // Lists - Better styling
        ul: ({ children }) => (
            <ul className="mb-6 ml-0 space-y-2">
                {children}
            </ul>
        ),
        ol: ({ children }) => (
            <ol className="list-decimal mb-6 ml-6 space-y-2">
                {children}
            </ol>
        ),
        li: ({ children }) => (
            <li className="pl-6 relative before:content-['▸'] before:absolute before:left-0 before:text-black before:font-bold">
                {children}
            </li>
        ),

        // Code - Better contrast
        code: ({ className, children }) => {
            const isBlock = className?.includes('language-');
            if (isBlock) {
                return (
                    <code className="block bg-[#1a1a2e] text-[#00FF00] p-5 font-mono text-sm overflow-x-auto border-[3px] border-black rounded-none">
                        {children}
                    </code>
                );
            }
            return (
                <code className="bg-[#FFFF00] px-2 py-1 font-mono text-sm font-bold">
                    {children}
                </code>
            );
        },
        pre: ({ children }) => (
            <pre className="my-6 overflow-x-auto">
                {children}
            </pre>
        ),

        // Blockquote - Blue accent for insights
        blockquote: ({ children }) => (
            <blockquote
                className="my-6 p-5 bg-gray-100 italic"
                style={{ borderLeft: '6px solid #000000' }}
            >
                {children}
            </blockquote>
        ),

        // Links
        a: ({ href, children }) => (
            <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-black underline font-bold hover:bg-[#FFFF00] transition-colors px-1"
            >
                {children}
            </a>
        ),

        // Images - Charts with proper styling
        img: ({ src, alt }) => (
            <figure className="my-8">
                <div className="border-[3px] border-black p-2 bg-white shadow-[4px_4px_0px_0px_#000000]">
                    <img
                        src={src}
                        alt={alt || 'Chart'}
                        className="w-full max-h-[500px] object-contain"
                        onError={(e) => {
                            // Hide broken images
                            (e.target as HTMLImageElement).style.display = 'none';
                        }}
                    />
                </div>
                {alt && (
                    <figcaption className="text-sm text-gray-600 mt-3 font-mono uppercase text-center">
                        📊 {alt.replace('Chart: ', '')}
                    </figcaption>
                )}
            </figure>
        ),

        // Horizontal rule - Section divider
        hr: () => (
            <div className="my-12 flex items-center gap-4">
                <div className="flex-1 h-[3px] bg-gray-300" />
                <div className="w-3 h-3 bg-black rotate-45" />
                <div className="flex-1 h-[3px] bg-gray-300" />
            </div>
        ),

        // Strong/Bold
        strong: ({ children }) => (
            <strong className="font-black text-black">
                {children}
            </strong>
        ),

        // Emphasis/Italic
        em: ({ children }) => (
            <em className="italic text-gray-700">
                {children}
            </em>
        ),

        // Strikethrough
        del: ({ children }) => (
            <del className="line-through text-gray-400">
                {children}
            </del>
        ),
    };

    return (
        <div className="report-viewer max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
                {processedContent}
            </ReactMarkdown>
        </div>
    );
}
