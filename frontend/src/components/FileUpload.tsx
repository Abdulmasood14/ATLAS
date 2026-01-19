import React, { useState } from 'react';
import { apiClient } from '../services/api';
import UploadStatusWidget from './UploadStatusWidget_v2';

interface FileUploadProps {
    onUploadSuccess: (companyId: string, companyName: string) => void;
}

interface UploadStatus {
    status: 'uploading' | 'processing' | 'completed' | 'failed';
    progress: number;
    upload_id?: number;
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

            // Switch to processing status - now we use the real upload_id for WS
            setUploadStatus({
                status: 'processing',
                progress: 0,
                upload_id: uploadResult.upload_id,
                fileName: file.name
            });

            // LOGIC REMOVED: No more simulated processingInterval or setTimeout.
            // The UploadStatusWidget will now handle the WebSocket connection 
            // and update itself based on real backend logs.

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
            const currentCompanyId = companyId;
            const currentCompanyName = companyName;
            setCompanyName('');
            setCompanyId('');
            setFiscalYear('');
            setUploadStatus(null);

            // Notify parent with company info
            onUploadSuccess(currentCompanyId, currentCompanyName);
        } else {
            setUploadStatus(null);
        }
    };

    return (
        <>
            <div className="bg-white rounded-lg p-4 border border-[#1762C7]/20 shadow-sm">
                <h3 className="text-lg font-semibold text-[#1762C7] mb-4">Upload Annual Report</h3>

                <form onSubmit={handleUpload} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-600 mb-1">
                            PDF File <span className="text-red-600">*</span>
                        </label>
                        <input
                            type="file"
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="w-full text-sm text-gray-600
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-[#1762C7]/20 file:text-[#1762C7]
              hover:file:bg-[#1762C7]/30
              cursor-pointer"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-600 mb-1">
                                Company Name <span className="text-red-600">*</span>
                            </label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="e.g. Acme Corp"
                                className="w-full bg-white border border-[#1762C7]/20 rounded-xl px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-[#1762C7]/50 focus:ring-2 focus:ring-[#1762C7]/20 transition-all duration-200 shadow-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-600 mb-1">
                                Company ID <span className="text-red-600">*</span>
                            </label>
                            <input
                                type="text"
                                value={companyId}
                                onChange={(e) => setCompanyId(e.target.value)}
                                placeholder="e.g. ACME_2024"
                                className="w-full bg-white border border-[#1762C7]/20 rounded-xl px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-[#1762C7]/50 focus:ring-2 focus:ring-[#1762C7]/20 transition-all duration-200 shadow-sm"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-600 mb-1">
                            Fiscal Year (Optional)
                        </label>
                        <input
                            type="text"
                            value={fiscalYear}
                            onChange={(e) => setFiscalYear(e.target.value)}
                            placeholder="e.g. 2024"
                            className="w-full bg-white border border-[#1762C7]/20 rounded-xl px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-[#1762C7]/50 focus:ring-2 focus:ring-[#1762C7]/20 transition-all duration-200 shadow-sm"
                        />
                    </div>

                    {error && <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded-lg">{error}</div>}

                    <button
                        type="submit"
                        disabled={uploadStatus !== null}
                        className={`w-full py-4 px-6 rounded-xl font-bold transition-all duration-300 ${uploadStatus !== null
                            ? 'bg-gray-200 text-gray-500 cursor-not-allowed border border-gray-300'
                            : 'text-white shadow-lg hover:shadow-xl hover:-translate-y-0.5'
                            }`}
                        style={uploadStatus === null ? {background: 'linear-gradient(135deg, rgb(31, 168, 166) 0%, rgb(23, 98, 199) 100%)'} : {}}
                    >
                        {uploadStatus !== null ? (
                            <div className="flex items-center justify-center gap-2">
                                <span className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-gray-600 rounded-full" />
                                <span>Processing Pipeline...</span>
                            </div>
                        ) : 'Upload & Start Analysis'}
                    </button>
                </form>
            </div>

            {/* Upload Status Widget */}
            {uploadStatus && uploadStatus.upload_id && (
                <UploadStatusWidget
                    uploadId={uploadStatus.upload_id}
                    fileName={uploadStatus.fileName || file?.name || 'document.pdf'}
                    onClose={handleCloseStatus}
                />
            )}
        </>
    );
}
