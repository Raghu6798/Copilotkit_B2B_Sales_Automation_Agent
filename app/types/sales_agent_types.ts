export interface SocialMediaLinks {
  blog: string;
  facebook: string;
  twitter: string;
  youtube: string;
}

export interface Report {
  title: string;
  content: string;
  is_markdown: boolean;
}

export interface LeadData {
  id: string;
  name: string;
  address: string;
  email: string;
  phone: string;
  company: string;
  profile: string;
}

export interface CompanyData {
  name: string;
  profile: string;
  website: string;
  social_media_links: SocialMediaLinks;
}

// This is the core interface that mirrors your LangGraph `AgentState`.
export interface SalesAgentState {
  // CopilotKitState properties (messages, etc.) will be here implicitly
  leads_data: LeadData[];
  current_lead: LeadData | null;
  number_leads: number;
  company_data: CompanyData | null;
  reports: Report[];
  lead_score: string;
  reports_folder_link: string;
  custom_outreach_report_link: string;
  personalized_email: string;
  interview_script: string;
}