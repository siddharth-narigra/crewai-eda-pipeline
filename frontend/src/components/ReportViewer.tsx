'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Components } from 'react-markdown';

interface ReportViewerProps {
    content: string;
}

export default function ReportViewer({ content }: ReportViewerProps) {
    // Preprocess content - strip wrapping code fences if present
    const processedContent = content
        .replace(/^```\s*\n?/, '')  // Remove leading ```
        .replace(/\n?```\s*$/, ''); // Remove trailing ```

    // Helper to generate ID from heading text
    const generateId = (children: React.ReactNode): string => {
        const text = String(children).replace(/^\d+\.\s*/, '').trim();
        return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-');
    };

    // Custom components for markdown rendering with brutalist styling
    const components: Components = {
        // Headings with IDs for anchor navigation
        h1: ({ children }) => {
            const id = generateId(children);
            return (
                <h1 id={id} className="text-3xl font-black uppercase tracking-tight border-b-[4px] border-black pb-3 mb-6 mt-8 scroll-mt-4">
                    {children}
                </h1>
            );
        },
        h2: ({ children }) => {
            const id = generateId(children);
            return (
                <h2 id={id} className="text-2xl font-black uppercase tracking-tight border-b-[3px] border-black pb-2 mb-4 mt-8 scroll-mt-4">
                    {children}
                </h2>
            );
        },
        h3: ({ children }) => {
            const id = generateId(children);
            return (
                <h3 id={id} className="text-xl font-bold uppercase tracking-tight mb-3 mt-6 scroll-mt-4">
                    {children}
                </h3>
            );
        },
        h4: ({ children }) => (
            <h4 className="text-lg font-bold uppercase mb-2 mt-4">
                {children}
            </h4>
        ),
        h5: ({ children }) => (
            <h5 className="text-base font-bold uppercase mb-2 mt-3">
                {children}
            </h5>
        ),
        h6: ({ children }) => (
            <h6 className="text-sm font-bold uppercase mb-2 mt-3 text-gray-600">
                {children}
            </h6>
        ),

        // Paragraphs
        p: ({ children }) => (
            <p className="mb-4 leading-relaxed">
                {children}
            </p>
        ),

        // Tables
        table: ({ children }) => (
            <div className="overflow-x-auto mb-6 border-[3px] border-black">
                <table className="w-full border-collapse">
                    {children}
                </table>
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
            <tr className="border-b-2 border-black even:bg-gray-100">
                {children}
            </tr>
        ),
        th: ({ children }) => (
            <th className="p-3 text-left font-bold uppercase text-sm border-r border-gray-600 last:border-r-0">
                {children}
            </th>
        ),
        td: ({ children }) => (
            <td className="p-3 text-sm border-r border-gray-200 last:border-r-0">
                {children}
            </td>
        ),

        // Lists
        ul: ({ children }) => (
            <ul className="list-none mb-4 ml-0">
                {children}
            </ul>
        ),
        ol: ({ children }) => (
            <ol className="list-decimal mb-4 ml-6">
                {children}
            </ol>
        ),
        li: ({ children }) => (
            <li className="mb-2 pl-4 relative before:content-['■'] before:absolute before:left-0 before:text-black before:text-xs before:top-1">
                {children}
            </li>
        ),

        // Code
        code: ({ className, children }) => {
            const isBlock = className?.includes('language-');
            if (isBlock) {
                return (
                    <code className="block bg-black text-[#00FF00] p-4 font-mono text-sm overflow-x-auto border-[3px] border-black">
                        {children}
                    </code>
                );
            }
            return (
                <code className="bg-[#FFFF00] px-2 py-0.5 font-mono text-sm border border-black">
                    {children}
                </code>
            );
        },
        pre: ({ children }) => (
            <pre className="mb-4 overflow-x-auto">
                {children}
            </pre>
        ),

        // Blockquote
        blockquote: ({ children }) => (
            <blockquote className="border-l-[4px] border-black bg-gray-100 p-4 mb-4 italic">
                {children}
            </blockquote>
        ),

        // Links
        a: ({ href, children }) => (
            <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#0000FF] underline font-bold hover:bg-[#FFFF00] transition-colors"
            >
                {children}
            </a>
        ),

        // Images
        img: ({ src, alt }) => (
            <figure className="mb-6">
                <img
                    src={src}
                    alt={alt || ''}
                    className="max-w-full border-[3px] border-black"
                />
                {alt && (
                    <figcaption className="text-sm text-gray-600 mt-2 font-mono uppercase">
                        {alt}
                    </figcaption>
                )}
            </figure>
        ),

        // Horizontal rule
        hr: () => (
            <hr className="border-0 border-t-[4px] border-black my-8" />
        ),

        // Strong/Bold
        strong: ({ children }) => (
            <strong className="font-black">
                {children}
            </strong>
        ),

        // Emphasis/Italic
        em: ({ children }) => (
            <em className="italic">
                {children}
            </em>
        ),

        // Strikethrough
        del: ({ children }) => (
            <del className="line-through text-gray-500">
                {children}
            </del>
        ),
    };

    return (
        <div className="report-viewer prose max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
                {processedContent}
            </ReactMarkdown>
        </div>
    );
}
