"use client";
import React from "react";
import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

// --- TYPE DEFINITIONS ---
// These interfaces must match the Pydantic models in your Python agent's state.

interface SocialMediaLinks {
  blog: string;
  facebook: string;
  twitter: string;
  youtube: string;
}

interface Report {
  title: string;
  content: string;
  is_markdown: boolean;
}

interface LeadData {
  id: string;
  name: string;
  address: string;
  email: string;
  phone: string;
  company: string;
  profile: string;
}

interface CompanyData {
  name: string;
  profile: string;
  website: string;
  social_media_links: SocialMediaLinks;
}

// This is the core interface that mirrors your LangGraph `AgentState`.
type GraphState = {
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
};


/**
 * The main component for the B2B Sales Agent UI.
 * It combines a pre-built chat interface with a custom real-time status dashboard.
 */
const SalesAgentPage: React.FC = () => {

  // This is the core hook for Generative UI. It subscribes to the agent's
  // internal state updates and makes them available to your component.
  // The 'state' object will be of type 'GraphState | undefined'.
  const { state } = useCoAgent<GraphState>({
    name: "sample_agent", // Must match your NEXT_PUBLIC_COPILOTKIT_AGENT_NAME
  });

  return (
    <div className="flex h-screen bg-gray-100 font-sans text-gray-800">
      
      {/* Left Panel: Real-Time Status Dashboard */}
      <div className="w-2/5 p-6 bg-white shadow-lg overflow-y-auto flex flex-col gap-6 border-r">
        <h1 className="text-2xl font-bold text-gray-700 border-b pb-2">Live Agent Status</h1>
        
        {/* Number of Leads */}
        <div className="p-4 bg-gray-50 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800">Leads in Queue</h2>
          <p className="mt-1 text-3xl font-bold text-center text-gray-600">
            {state?.number_leads ?? 0}
          </p>
        </div>
        
        {/* Current Lead Card */}
        <div className="p-4 bg-blue-50 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold text-blue-800">Current Lead</h2>
          {state?.current_lead ? (
            <div className="mt-2 text-sm">
              <p><strong>Name:</strong> {state.current_lead.name}</p>
              <p><strong>Company:</strong> {state.current_lead.company}</p>
              <p><strong>Email:</strong> {state.current_lead.email}</p>
            </div>
          ) : (
            <p className="mt-2 text-sm text-gray-500">Waiting for a new lead...</p>
          )}
        </div>

        {/* Lead Score Card */}
        <div className="p-4 bg-green-50 rounded-lg shadow-sm">
          <h2 className="text-lg font-semibold text-green-800">Lead Score</h2>
          {state?.lead_score ? (
            <p className="mt-2 text-3xl font-bold text-center text-green-600">{state.lead_score} / 10</p>
          ) : (
            <p className="mt-2 text-sm text-gray-500">Not yet calculated.</p>
          )}
        </div>

        {/* Generated Reports & Links */}
        <div className="p-4 bg-purple-50 rounded-lg shadow-sm flex-grow">
          <h2 className="text-lg font-semibold text-purple-800">Generated Assets</h2>
          <div className="mt-2 space-y-3">
             {state?.custom_outreach_report_link && (
              <a href={state.custom_outreach_report_link} target="_blank" rel="noopener noreferrer" className="block w-full text-center bg-purple-600 text-white font-bold py-2 px-4 rounded hover:bg-purple-700 transition-colors">
                View Custom Outreach Report
              </a>
            )}
             {state?.reports_folder_link && (
              <a href={state.reports_folder_link} target="_blank" rel="noopener noreferrer" className="block w-full text-center bg-gray-600 text-white font-bold py-2 px-4 rounded hover:bg-gray-700 transition-colors">
                Open All Reports Folder
              </a>
            )}
            <h3 className="text-md font-semibold pt-2">Reports Generated:</h3>
            <ul className="list-disc list-inside text-sm space-y-1">
              {state?.reports && state.reports.length > 0 ? (
                state.reports.map((report, index) => report && <li key={index}>{report.title}</li>)
              ) : (
                <li className="text-gray-500">No reports generated yet.</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Right Panel: Pre-built Chat Interface */}
      <div className="w-3/5 flex flex-col p-6">
        <div className="flex-grow flex flex-col bg-white rounded-lg shadow-md">
          {/* 
            The CopilotChat component handles all user input, message display,
            and communication with the agent backend.
          */}
          <CopilotChat
            className="w-full h-full"
            labels={{
              initial: "Hello! I'm your B2B Sales Automation Agent. Type a command to begin.",
              placeholder: "e.g., 'Start processing new leads'",
            }}
            suggestions={[
              "Start processing new leads.",
              "Begin the outreach automation.",
              "Draft a structured Outreach Report for all the Leads from the CRM"
            ]}
          />
        </div>
      </div>
    </div>
  );
};

// Your page.tsx simply renders the main component.
// It assumes the <CopilotKit> provider is in layout.tsx.
export default function Page() {
  return <SalesAgentPage />;
}