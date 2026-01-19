import React, { useEffect, useState } from 'react';
import { apiClient } from '../services/api';
import type { Company } from '../types';

interface CompanySelectorProps {
  onSelectCompany: (company: Company) => void;
  selectedCompanyId?: string;
}

export default function CompanySelector({ onSelectCompany, selectedCompanyId }: CompanySelectorProps) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getCompanies();
      setCompanies(data.companies);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch companies:', err);
      setError('Failed to load companies');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="text-sm text-text-muted animate-pulse">Loading companies...</div>;
  }

  if (error) {
    return (
      <div className="text-sm text-error flex items-center gap-2">
        <span>{error}</span>
        <button onClick={fetchCompanies} className="text-primary hover:underline">
          Retry
        </button>
      </div>
    );
  }

  if (companies.length === 0) {
    return <div className="text-sm text-text-muted">No companies found. Upload a PDF to get started.</div>;
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-600">Select Company</label>
      <select
        className="w-full bg-white border border-[#1762C7]/20 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:border-[#1762C7]/50 focus:ring-2 focus:ring-[#1762C7]/20 transition-all appearance-none cursor-pointer shadow-sm hover:border-[#1762C7]/40"
        value={selectedCompanyId || ''}
        onChange={(e) => {
          const company = companies.find((c) => c.company_id === e.target.value);
          if (company) {
            onSelectCompany(company);
          }
        }}
      >
        <option value="" disabled className="bg-white text-gray-500">
          Select a company...
        </option>
        {companies.map((company) => (
          <option key={company.company_id} value={company.company_id} className="bg-white text-gray-900">
            {company.company_name} ({company.chunk_count} chunks)
          </option>
        ))}
      </select>
    </div>
  );
}
