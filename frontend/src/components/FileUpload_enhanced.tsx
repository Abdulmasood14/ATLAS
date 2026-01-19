import React, { useState } from 'react';
import { apiClient } from '../services/api';
import UploadStatusWidget from './UploadStatusWidget';

interface FileUploadProps {
    onUploadSuccess: (companyId: string, companyName: string) => void;
}

interface UploadStatus {
    status: 'uploading' | 'processing' | 'completed' | 'failed';
    progress: number;
    fileName?: string;
    chunksCreated?: number;
    chunksStored?: number;
    error?: string;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [companyName, setCompanyName] = useState('');
    const [companyId, setCompanyId] = useState('');
    const [fiscalYear, setFiscalYear] = useState('');
    const [error, setError] = useState<string | null>(null);

    const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            if (selectedFile.type !== 'application/pdf') {
                setError('Please select a valid PDF file.');
                setFile(null);
                return;
            }
            setFile(selectedFile);
            setError(null);

            // Auto-suggest company ID from filename if empty
            if (!companyId) {
                const name = selectedFile.name.replace('.pdf', '').toUpperCase().replace(/[^A-Z0-9]/g, '_');
                setCompanyId(name);
            }
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !companyName || !companyId) {
            setError('Please fill in all required fields.');
            return;
        }

        // Show upload status widget
        setUploadStatus({
            status: 'uploading',
            progress: 0,
            fileName: file.name
        });
        setError(null);

        try {
            // Upload PDF with progress tracking
            const uploadResult = await apiClient.uploadPDF(
                file,
                companyId,
                companyName,
                fiscalYear || undefined,
                undefined,
                (progress) => {
                    setUploadStatus(prev => prev ? { ...prev, progress } : null);
                }
            );

            // Switch to processing status
            setUploadStatus({
                status: 'processing',
                progress: 0,
                fileName: file.name
            });

            // Simulate processing progress (you can poll backend for real status)
            const processingInterval = setInterval(() => {
                setUploadStatus(prev => {
                    if (!prev || prev.progress >= 100) {
                        clearInterval(processingInterval);
                        return prev;
                    }
                    return { ...prev, progress: Math.min(prev.progress + 10, 100) };
                });
            }, 500);

            // Wait a bit for processing to complete
            await new Promise(resolve => setTimeout(resolve, 6000));
            clearInterval(processingInterval);

            // Mark as completed
            setUploadStatus({
                status: 'completed',
                progress: 100,
                fileName: file.name,
                chunksCreated: uploadResult.chunks_created || 0,
                chunksStored: uploadResult.chunks_stored || 0
            });

        } catch (err: any) {
            console.error('Upload failed:', err);
            setUploadStatus({
                status: 'failed',
                progress: 0,
                fileName: file.name,
                error: err.response?.data?.detail || 'Upload failed. Please try again.'
            });
        }
    };

    const handleCloseStatus = () => {
        if (uploadStatus?.status === 'completed') {
            // Clear form
            setFile(null);
            setCompanyName('');
            setCompanyId('');
            setFiscalYear('');
            setUploadStatus(null);

            // Notify parent with company info
            onUploadSuccess(companyId, companyName);
        } else {
            setUploadStatus(null);
        }
    };

    return (
        <>
            <div className="bg-background-secondary rounded-lg p-4 border border-primary/20">
                <h3 className="text-lg font-semibold text-primary mb-4">Upload Annual Report</h3>

                <form onSubmit={handleUpload} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">
                            PDF File <span className="text-error">*</span>
                        </label>
                        <input
                            type="file"
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="w-full text-sm text-text-muted
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-primary/20 file:text-primary
              hover:file:bg-primary/30
              cursor-pointer"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                Company Name <span className="text-error">*</span>
                            </label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="e.g. Acme Corp"
                                className="w-full bg-background-input border border-primary/20 rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">
                                Company ID <span className="text-error">*</span>
                            </label>
                            <input
                                type="text"
                                value={companyId}
                                onChange={(e) => setCompanyId(e.target.value)}
                                placeholder="e.g. ACME_2024"
                                className="w-full bg-background-input border border-primary/20 rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">
                            Fiscal Year (Optional)
                        </label>
                        <input
                            type="text"
                            value={fiscalYear}
                            onChange={(e) => setFiscalYear(e.target.value)}
                            placeholder="e.g. 2024"
                            className="w-full bg-background-input border border-primary/20 rounded px-3 py-2 text-text-primary focus:outline-none focus:border-primary"
                        />
                    </div>

                    {error && <div className="text-sm text-error bg-error/10 p-2 rounded">{error}</div>}

                    <button
                        type="submit"
                        disabled={uploadStatus !== null}
                        className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${uploadStatus !== null
                            ? 'bg-background-input text-text-muted cursor-not-allowed'
                            : 'bg-primary text-text-inverse hover:bg-primary/90'
                            }`}
                    >
                        {uploadStatus !== null ? 'Processing...' : 'Upload & Process'}
                    </button>
                </form>
            </div>

            {/* Upload Status Widget */}
            {uploadStatus && (
                <UploadStatusWidget
                    uploadStatus={uploadStatus}
                    onClose={handleCloseStatus}
                />
            )}
        </>
    );
}
