"use client";
import React, { useState, useMemo } from "react";
import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// --- UI Components (Assumes a Shadcn/UI-like setup) ---
// You would typically install these from a library like shadcn/ui
// or create them yourself. For brevity, their implementation is omitted.
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Users,
  Building,
  FileText,
  ClipboardCheck,
  Link as LinkIcon,
  Loader2,
  List,
} from "lucide-react";

// --- TYPE DEFINITIONS (from your original file) ---
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
  // CopilotKit provides the current step name from LangGraph
  step?: string;
};

// --- Reusable UI Components ---

const StatusCard = ({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) => (
  <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium text-gray-600">
        {title}
      </CardTitle>
      <Icon className="h-4 w-4 text-gray-400" />
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
);

const AgentStepper = ({ currentStep }: { currentStep?: string }) => {
  const steps = useMemo(
    () => [
      { name: "get_new_leads", label: "Fetch Leads", phase: "Initialization" },
      { name: "fetch_linkedin_profile_data", label: "Research Lead", phase: "Research" },
      { name: "review_company_website", label: "Scan Website", phase: "Research" },
      { name: "analyze_blog_content", label: "Analyze Blog", phase: "Research" },
      { name: "analyze_social_media_content", label: "Check Socials", phase: "Research" },
      { name: "analyze_recent_news", label: "Review News", phase: "Research" },
      { name: "generate_full_lead_research_report", label: "Consolidate Research", phase: "Reporting" },
      { name: "score_lead", label: "Score Lead", phase: "Qualification" },
      { name: "generate_custom_outreach_report", label: "Build Outreach", phase: "Outreach" },
      { name: "generate_personalized_email", label: "Draft Email", phase: "Outreach" },
      { name: "generate_interview_script", label: "Prep Interview", phase: "Outreach" },
      { name: "update_CRM", label: "Update CRM", phase: "Finalization" },
    ],
    []
  );

  const currentStepIndex = steps.findIndex((s) => s.name === currentStep);

  return (
    <Card className="bg-white shadow-md">
      <CardHeader>
        <CardTitle className="text-lg">Agent Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="relative border-l border-gray-200 dark:border-gray-700 ml-2">
          {steps.map((step, index) => (
            <li key={step.name} className="mb-6 ml-6">
              <span className={`absolute flex items-center justify-center w-6 h-6 rounded-full -left-3 ring-4 ring-white ${
                  index < currentStepIndex ? "bg-green-500" :
                  index === currentStepIndex ? "bg-blue-500 animate-pulse" : "bg-gray-300"
                }`}>
              </span>
              <h3 className="flex items-center mb-1 text-md font-semibold text-gray-900">
                {step.label}
                {index === currentStepIndex && <Badge variant="secondary" className="ml-2">In Progress</Badge>}
              </h3>
              <p className="block text-xs font-normal text-gray-500">{step.phase}</p>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
};

// --- Main Page Component ---

const SalesAgentPage: React.FC = () => {
  const { state } = useCoAgent<GraphState>({ name: "sample_agent" });
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  return (
    <div className="grid md:grid-cols-12 gap-4 h-screen bg-gray-50 p-4 font-sans text-gray-800">
      {/* Left Panel: Real-Time Status Dashboard */}
      <div className="md:col-span-5 lg:col-span-4 flex flex-col gap-4 overflow-y-auto pr-2">
        <h1 className="text-3xl font-bold text-gray-800">B2B Sales Agent</h1>
        
        {/* Agent Stepper - The star of the show! */}
        <AgentStepper currentStep={state?.step} />

        <div className="grid grid-cols-2 gap-4">
            <StatusCard title="Leads in Queue" icon={List}>
                <div className="text-2xl font-bold text-center text-gray-700">{state?.number_leads ?? 0}</div>
            </StatusCard>
            <StatusCard title="Lead Score" icon={ClipboardCheck}>
              {state?.lead_score ? (
                <div className="text-2xl font-bold text-center text-green-600">{state.lead_score} / 10</div>
              ) : (
                <div className="text-sm text-gray-500 text-center pt-2">Pending...</div>
              )}
            </StatusCard>
        </div>

        <StatusCard title="Current Lead" icon={Users}>
          {state?.current_lead ? (
            <div className="text-sm space-y-1">
              <p><strong>Name:</strong> {state.current_lead.name}</p>
              <p><strong>Company:</strong> {state.current_lead.company}</p>
              <p><strong>Email:</strong> {state.current_lead.email}</p>
            </div>
          ) : (
             <p className="text-sm text-gray-500">Waiting for a new lead...</p>
          )}
        </StatusCard>

        <StatusCard title="Generated Assets" icon={FileText}>
           <div className="space-y-3">
             {state?.custom_outreach_report_link && (
              <Button asChild className="w-full bg-indigo-600 hover:bg-indigo-700">
                <a href={state.custom_outreach_report_link} target="_blank" rel="noopener noreferrer">
                  <LinkIcon className="w-4 h-4 mr-2"/> View Outreach Report
                </a>
              </Button>
            )}
             {state?.reports_folder_link && (
              <Button asChild variant="outline" className="w-full">
                <a href={state.reports_folder_link} target="_blank" rel="noopener noreferrer">
                  <LinkIcon className="w-4 h-4 mr-2"/> Open All Reports
                </a>
              </Button>
            )}
            <h3 className="text-md font-semibold pt-2 border-t mt-3">Reports Log:</h3>
            <ul className="text-sm space-y-1">
              {state?.reports && state.reports.length > 0 ? (
                state.reports.map((report, index) => report && (
                  <li key={index}>
                    <button onClick={() => setSelectedReport(report)} className="text-blue-600 hover:underline text-left">
                      {report.title}
                    </button>
                  </li>
                ))
              ) : (
                <li className="text-gray-500">No reports generated yet.</li>
              )}
            </ul>
           </div>
        </StatusCard>
      </div>

      {/* Right Panel: Pre-built Chat Interface */}
      <div className="md:col-span-7 lg:col-span-8 flex flex-col h-full">
          <CopilotChat
            className="w-full h-full flex flex-col"
            labels={{
              initial: "Hello! I'm your B2B Sales Automation Agent. Type a command to begin.",
              placeholder: "e.g., 'Start processing new leads'",
            }}
            suggestions={[
              "Start processing new leads.",
              "Begin the outreach automation for all leads.",
            ]}
          />
      </div>

      {/* Report Viewer Modal */}
      <Dialog open={!!selectedReport} onOpenChange={() => setSelectedReport(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>{selectedReport?.title}</DialogTitle>
          </DialogHeader>
          <div className="prose max-w-none overflow-y-auto">
            {selectedReport?.is_markdown ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedReport.content}</ReactMarkdown>
            ) : (
                <pre className="whitespace-pre-wrap">{selectedReport?.content}</pre>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default function Page() {
  return <SalesAgentPage />;
}
