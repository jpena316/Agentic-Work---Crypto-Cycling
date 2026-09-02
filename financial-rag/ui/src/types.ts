export interface Citation {
  marker: string
  company: string
  doc_type: string
  fiscal_period: string
  section: string
}

export interface GroundedAnswer {
  answer: string
  citations: Citation[]
}

export type CompanyFilter = 'ALL' | 'VRT' | 'SNOW'

export const COMPANY_NAMES: Record<Exclude<CompanyFilter, 'ALL'>, string> = {
  VRT: 'Vertiv Holdings Co',
  SNOW: 'Snowflake Inc.',
}
