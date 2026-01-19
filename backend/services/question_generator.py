"""
AI-Powered Question Generator for Deep Dive Tab

Generates 3 categories of questions:
1. General - Universal questions for all companies
2. Sector-Specific - Questions based on AI-detected sector using Phi-4
3. Business-Specific - AI-generated questions from document context
"""
import asyncio
from typing import List, Dict
from database.connection import get_db_manager
from datetime import datetime
import logging
import requests
import json

logger = logging.getLogger(__name__)

# Phi-4 LLM Configuration (Same as RAG service)
PHI4_API_URL = "http://10.100.20.76:11434/v1/chat/completions"
PHI4_MODEL = "phi4:latest"


class QuestionGenerator:
    """Generates insightful questions based on company documents"""

    def __init__(self):
        self.db = get_db_manager()

    async def detect_sector(self, company_id: str, company_name: str) -> str:
        """
        Detect company sector using Phi-4 LLM analysis of document chunks

        Returns: Sector name from predefined list of 15+ sectors
        """
        try:
            # Get sample chunks from database
            chunks = await self.get_sample_chunks(company_id, limit=20)

            if not chunks:
                logger.warning(f"No chunks found for company {company_id}")
                return "General"

            # Combine chunks for analysis (max 3000 chars for efficiency)
            combined_text = " ".join([chunk.get('chunk_text', '') for chunk in chunks])
            combined_text = combined_text[:3000]

            # Define all supported sectors
            available_sectors = [
                "Pharmaceuticals & Biotechnology",
                "Information Technology & Software",
                "Healthcare Services",
                "Banking & Financial Services",
                "Manufacturing & Industrial",
                "FMCG & Consumer Goods",
                "Telecommunications",
                "Energy & Utilities",
                "Real Estate & Construction",
                "Automotive & Transportation",
                "Textiles & Apparel",
                "Food & Beverage",
                "E-commerce & Retail",
                "Insurance",
                "Media & Entertainment",
                "Chemicals & Petrochemicals",
                "Agriculture & Agribusiness",
                "Logistics & Supply Chain"
            ]

            # Create LLM prompt for sector detection
            prompt = f"""Analyze this company annual report excerpt and classify it into ONE of the following sectors.

Company Name: {company_name}

Report Excerpt:
{combined_text}

Available Sectors:
{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(available_sectors)])}

Instructions:
- Read the report excerpt carefully
- Identify the primary business nature
- Return ONLY the sector name from the list above
- Return exactly as written (including "&" and capitalization)
- Do not add explanations or additional text
- If unclear, choose the closest match

Sector:"""

            # Call Phi-4 LLM (using same format as suggestions.py)
            try:
                response = requests.post(
                    PHI4_API_URL,
                    json={
                        "model": PHI4_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a business sector classification expert."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,  # Low temperature for deterministic output
                        "max_tokens": 50,
                        "stream": False
                    },
                    timeout=180
                )

                if response.status_code == 200:
                    result = response.json()
                    # Extract response from chat/completions format
                    detected_sector = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

                    # Validate detected sector
                    if detected_sector in available_sectors:
                        logger.info(f"✓ LLM detected sector for {company_name}: {detected_sector}")
                        return detected_sector
                    else:
                        # Try fuzzy matching
                        for sector in available_sectors:
                            if sector.lower() in detected_sector.lower() or detected_sector.lower() in sector.lower():
                                logger.info(f"✓ LLM detected sector (fuzzy match) for {company_name}: {sector}")
                                return sector

                        logger.warning(f"LLM returned invalid sector '{detected_sector}', using General")
                        return "General"
                else:
                    logger.error(f"LLM API error: {response.status_code}")
                    return "General"

            except requests.exceptions.RequestException as e:
                logger.error(f"LLM request failed: {e}")
                return "General"

        except Exception as e:
            logger.error(f"Error detecting sector: {e}")
            return "General"

    async def get_sample_chunks(self, company_id: str, limit: int = 15) -> List[Dict]:
        """Fetch sample chunks from database for sector detection"""
        try:
            async with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT chunk_id, chunk_text, page_numbers
                    FROM document_chunks_v2
                    WHERE company_id = %s
                    ORDER BY chunk_id
                    LIMIT %s
                """, (company_id, limit))

                rows = cursor.fetchall()
                return [
                    {
                        'chunk_id': row['chunk_id'],
                        'chunk_text': row['chunk_text'],
                        'page_numbers': row['page_numbers']
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error fetching sample chunks: {e}")
            return []

    def get_general_questions(self) -> List[str]:
        """Universal questions applicable to all companies"""
        return [
            "What is the company's total revenue for the fiscal year?",
            "What are the main products or services offered by the company?",
            "What is the company's net profit margin?",
            "What are the key financial highlights from the annual report?",
            "What is the company's current market position?",
            "What is the company's debt-to-equity ratio?",
            "What are the major sources of revenue?",
            "How many employees does the company have?",
            "What is the dividend payout ratio?",
            "What are the future growth plans mentioned in the report?"
        ]

    def get_sector_questions(self, sector: str) -> List[str]:
        """Sector-specific pre-defined questions (6 questions per sector)"""

        sector_questions = {
            "Pharmaceuticals & Biotechnology": [
                "What USFDA and regulatory approvals were received this year?",
                "What is the current drug pipeline and ANDA filing status?",
                "What are the key therapeutic areas and API manufacturing capabilities?",
                "What R&D investments and formulation development initiatives exist?",
                "What contract manufacturing (CDMO) partnerships exist?",
                "What quality certifications (WHO-GMP, USFDA, EMA) does the company hold?"
            ],
            "Information Technology & Software": [
                "What is the annual recurring revenue (ARR) and customer growth metrics?",
                "What cloud infrastructure and SaaS product offerings exist?",
                "What AI/ML and emerging technology initiatives are underway?",
                "What cybersecurity measures and data protection protocols are in place?",
                "What strategic technology partnerships and acquisitions occurred?",
                "What is the R&D investment as percentage of revenue?"
            ],
            "Healthcare Services": [
                "What is the bed occupancy rate across all facilities?",
                "What are the Average Revenue Per Occupied Bed (ARPOB) metrics?",
                "What medical specialties and Centers of Excellence does the company operate?",
                "What hospital accreditations (NABH, JCI, NABL) are held?",
                "What expansion plans for new hospitals or bed additions exist?",
                "What telemedicine and digital health initiatives exist?"
            ],
            "Banking & Financial Services": [
                "What is the net interest margin (NIM) and NPA ratio?",
                "What is the capital adequacy ratio and loan-to-deposit ratio?",
                "What digital banking and fintech initiatives were launched?",
                "What is the CASA ratio and deposit growth trend?",
                "What regulatory compliance measures and risk management frameworks exist?",
                "What branch network expansion or consolidation plans exist?"
            ],
            "Manufacturing & Industrial": [
                "What is the production capacity utilization rate?",
                "What automation and Industry 4.0 initiatives are in place?",
                "What is the supply chain efficiency and inventory turnover ratio?",
                "What quality certifications (ISO, Six Sigma) does the company hold?",
                "What sustainability and emission reduction measures are implemented?",
                "What are the major capital expenditures and expansion plans?"
            ],
            "FMCG & Consumer Goods": [
                "What is the distribution network coverage (urban vs rural)?",
                "What new product launches and brand extensions occurred?",
                "What is the market share in key product categories?",
                "What e-commerce and direct-to-consumer revenue contribution exists?",
                "What advertising and brand marketing spend was allocated?",
                "What sustainability initiatives in packaging and sourcing exist?"
            ],
            "Telecommunications": [
                "What is the subscriber base growth and market share?",
                "What is the average revenue per user (ARPU) trend?",
                "What 5G rollout plans and network coverage expansion exist?",
                "What spectrum holdings and auction participation occurred?",
                "What is the churn rate and customer retention metrics?",
                "What digital services beyond telecom are offered?"
            ],
            "Energy & Utilities": [
                "What is the installed capacity and plant load factor (PLF)?",
                "What renewable energy investments and green transition plans exist?",
                "What is the coal/gas linkage status and fuel cost trends?",
                "What transmission and distribution loss reduction measures exist?",
                "What environmental compliance and carbon emission targets are set?",
                "What future capacity expansion and project pipeline exists?"
            ],
            "Real Estate & Construction": [
                "What is the current project pipeline value and order book?",
                "What is the land bank available for future development?",
                "What types of projects (residential, commercial, infrastructure) dominate?",
                "What is the project completion rate and delivery timelines?",
                "What debt levels and project financing methods are used?",
                "What green building certifications (LEED, GRIHA) are targeted?"
            ],
            "Automotive & Transportation": [
                "What is the production volume and capacity utilization?",
                "What electric vehicle (EV) and hybrid vehicle plans exist?",
                "What is the market share across different vehicle segments?",
                "What R&D investments in autonomous driving and connected vehicles occurred?",
                "What export markets and international presence does the company have?",
                "What dealer network coverage and after-sales service infrastructure exists?"
            ],
            "Textiles & Apparel": [
                "What is the spinning/weaving capacity and production volume?",
                "What is the export vs domestic sales revenue ratio?",
                "What sustainability certifications (GOTS, Fair Trade) are held?",
                "What value-added products and vertical integration exist?",
                "What key export markets and international brand partnerships exist?",
                "What automation in manufacturing and digital transformation occurred?"
            ],
            "Food & Beverage": [
                "What raw material sourcing strategies and farmer partnerships exist?",
                "What food safety certifications (FSSAI, HACCP, ISO 22000) are held?",
                "What new product innovations and portfolio expansion occurred?",
                "What is the retail vs institutional sales channel mix?",
                "What cold chain infrastructure and distribution capabilities exist?",
                "What sustainability initiatives in agriculture and packaging exist?"
            ],
            "E-commerce & Retail": [
                "What is the gross merchandise value (GMV) and active user base growth?",
                "What customer acquisition cost (CAC) and lifetime value (LTV) metrics exist?",
                "What logistics and last-mile delivery infrastructure is deployed?",
                "What private label and exclusive brand offerings exist?",
                "What technology investments in AI-driven recommendations and personalization occurred?",
                "What omnichannel integration between online and offline exists?"
            ],
            "Insurance": [
                "What is the gross written premium (GWP) growth and market share?",
                "What is the combined ratio and loss ratio performance?",
                "What digital distribution and insurtech partnerships exist?",
                "What new product launches and niche segment focus occurred?",
                "What claims settlement ratio and customer satisfaction metrics exist?",
                "What solvency ratio and regulatory capital requirements are maintained?"
            ],
            "Media & Entertainment": [
                "What is the subscriber base and content consumption metrics?",
                "What original content production and IP creation occurred?",
                "What digital streaming and OTT platform strategy exists?",
                "What advertising revenue vs subscription revenue mix exists?",
                "What international market expansion and content licensing deals occurred?",
                "What technology investments in AI-driven content recommendations exist?"
            ],
            "Chemicals & Petrochemicals": [
                "What is the production capacity and capacity utilization?",
                "What specialty chemicals vs commodity chemicals revenue mix exists?",
                "What R&D investments in green chemistry and sustainable products occurred?",
                "What backward integration and feedstock sourcing strategies exist?",
                "What environmental compliance and waste management measures are implemented?",
                "What export markets and international presence does the company have?"
            ],
            "Agriculture & Agribusiness": [
                "What crop production volumes and yield improvements occurred?",
                "What farmer engagement programs and contract farming exist?",
                "What agri-tech and precision farming initiatives are deployed?",
                "What value-added processing and brand development occurred?",
                "What export markets and international trade presence exists?",
                "What sustainability practices and organic farming initiatives exist?"
            ],
            "Logistics & Supply Chain": [
                "What is the network coverage and warehouse infrastructure?",
                "What technology investments in route optimization and tracking exist?",
                "What last-mile delivery capabilities and service level agreements exist?",
                "What cold chain and specialized logistics services are offered?",
                "What automation in warehouses and fulfillment centers occurred?",
                "What sustainability initiatives in fleet management and emissions exist?"
            ]
        }

        # Return sector-specific questions or default to general if sector not found
        return sector_questions.get(sector, self.get_general_questions()[:6])

    def get_business_questions(self) -> List[str]:
        """
        Business-specific questions (pre-defined, can be enhanced with LLM later)

        These questions focus on strategic business aspects that apply to most companies
        """
        return [
            "What are the key competitive advantages of the company?",
            "What is the market share compared to competitors?",
            "What strategic partnerships or collaborations exist?",
            "What expansion plans does the company have?",
            "What are the major risk factors mentioned?",
            "What innovation and R&D initiatives are ongoing?",
            "What operational challenges is the company facing?",
            "What is the company's sustainability and ESG strategy?",
            "What are the key growth drivers for the business?",
            "What digital transformation initiatives exist?"
        ]

    async def generate_all_questions(self, company_id: str, company_name: str) -> Dict:
        """
        Generate all 3 categories of questions

        Returns:
            {
                'company_id': str,
                'company_name': str,
                'detected_sector': str,
                'questions': {
                    'general': List[str],
                    'sector_specific': List[str],
                    'business_specific': List[str]
                },
                'generated_at': str
            }
        """
        try:
            # Detect sector using LLM
            sector = await self.detect_sector(company_id, company_name)

            # Generate questions
            general_questions = self.get_general_questions()
            sector_questions = self.get_sector_questions(sector)
            business_questions = self.get_business_questions()

            result = {
                'company_id': company_id,
                'company_name': company_name,
                'detected_sector': sector,
                'questions': {
                    'general': general_questions,
                    'sector_specific': sector_questions,
                    'business_specific': business_questions
                },
                'generated_at': datetime.now().isoformat()
            }

            logger.info(f"Generated questions for {company_name}: {sector} sector")
            return result

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            # Return fallback questions
            return {
                'company_id': company_id,
                'company_name': company_name,
                'detected_sector': 'General',
                'questions': {
                    'general': self.get_general_questions(),
                    'sector_specific': self.get_general_questions()[:8],
                    'business_specific': self.get_business_questions()
                },
                'generated_at': datetime.now().isoformat()
            }
