'use client';

import { useState, useCallback } from 'react';
import { uploadFile, UploadResponse } from '@/lib/api';

interface FileUploaderProps {
  onUploadSuccess: (data: UploadResponse) => void;
}

export default function FileUploader({ onUploadSuccess }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await handleFileUpload(files[0]);
    }
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
      setError('ONLY CSV OR XLSX FILES ACCEPTED');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await uploadFile(file);
      onUploadSuccess(result);
    } catch (err) {
      setError(err instanceof Error ? err.message.toUpperCase() : 'UPLOAD FAILED');
    } finally {
      setIsUploading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  return (
    <div className="w-full">
      <input
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={handleInputChange}
        className="hidden"
        id="file-upload"
        disabled={isUploading}
      />

      <label htmlFor="file-upload">
        <div
          className={`
            dropzone-brutal
            ${isDragging ? 'dropzone-brutal-active' : ''}
            ${isUploading ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-3">
              <span className="spinner-brutal text-2xl" />
              <span className="text-label">UPLOADING...</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              {/* Upload Icon - Geometric */}
              <div className="w-16 h-16 bg-black flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={3}
                >
                  <path strokeLinecap="square" d="M12 4v12M4 12l8-8 8 8" />
                </svg>
              </div>

              <div>
                <p className="text-h3 mb-1">DROP YOUR DATA HERE</p>
                <p className="text-label text-gray">OR CLICK TO BROWSE</p>
              </div>

              <div className="flex gap-2 mt-2">
                <span className="tag-brutal">.CSV</span>
                <span className="tag-brutal">.XLSX</span>
              </div>
            </div>
          )}
        </div>
      </label>

      {error && (
        <div className="mt-3 p-3 bg-warning text-white">
          <span className="text-label">■ ERROR: {error}</span>
        </div>
      )}
    </div>
  );
}
