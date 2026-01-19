import React, { useState } from 'react';
import { apiClient } from '../services/api';
import { Download } from 'lucide-react';

interface ExportButtonProps {
    sessionId: string;
    isDisabled?: boolean;
}

export default function ExportButton({ sessionId, isDisabled = false }: ExportButtonProps) {
    const [isExporting, setIsExporting] = useState(false);

    const handleExport = async () => {
        try {
            setIsExporting(true);

            // 1. Request export creation
            const response = await apiClient.exportSession({
                session_id: sessionId,
                export_format: 'xlsx',
                include_feedback: true,
                include_sources: true
            });

            // 2. Download the file
            const blob = await apiClient.downloadExport(response.export_id);

            // 3. Trigger browser download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `session_export_${sessionId.slice(0, 8)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (err) {
            console.error('Export failed:', err);
            alert('Failed to export session. Please try again.');
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <button
            onClick={handleExport}
            disabled={isDisabled || isExporting}
            className={`
        flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors
        ${isDisabled
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200'
                    : 'bg-[#1762C7]/10 text-[#1762C7] hover:bg-[#1762C7]/20 border border-[#1762C7]/20'}
      `}
            title="Export chat history to Excel"
        >
            <Download size={14} />
            {isExporting ? 'Exporting...' : 'Export to Excel'}
        </button>
    );
}
