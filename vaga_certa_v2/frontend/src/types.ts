
export interface UserInput {
  cv: string;
  jobUrl: string;
  tone: string;
  language: string;
  customContext: string;
}

export interface GroundingSource {
  uri: string;
  title: string;
}

export interface CompatibilityInsights {
  score: number;
  label: string;
  strengths: string[];
  gaps: string[];
  coverageRatio: number;
}

export interface GeneratedContent {
  optimizedCv: string;
  coverLetter: string;
  networkingMessage: string;
  interviewTips: string;
  sources: GroundingSource[];
  compatibility?: CompatibilityInsights;
}

export interface HistoryItem {
  id: string;
  title: string;
  userInput: UserInput;
  generatedContent: GeneratedContent | null;
  isLoading?: boolean;
  error?: string | null;
  jobDetails?: JobDetails; // Detalhes da vaga (com score e warning)
}

export interface JobDetails {
  jobTitle: string;
  company: string;
  jobDescription: string;
  contentScore?: number; // Score de validação 0-100
  validationWarning?: string; // Mensagem de warning quando score 30-70
}

// Types for the CV Formatting "Agent"
export interface ExperienceEntry {
  role: string;
  company: string;
  period: string;
  responsibilities: string[];
}

export interface EducationEntry {
  degree: string;
  institution: string;
  period: string;
}

export interface ParsedCv {
  name: string;
  contact: {
    address?: string;
    phone?: string;
    email?: string;
    linkedin?: string;
    [key: string]: string | undefined;
  };
  summary: string;
  experience: ExperienceEntry[];
  education: EducationEntry[];
  skills: string[];
}
