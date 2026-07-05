export interface Notebook {
  id: string;
  name: string;
}

export interface DocumentInfo {
  id: string;
  name: string;
  media_type: string;
  page_count: number;
  chunk_count: number;
  source_url?: string | null;
}

export interface Citation {
  n: number;
  document_id: string;
  document_name: string;
  chunk_index: number;
  page: number;
  text: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
}

export interface AudioOverviewData {
  summary: string;
  media_type: string;
  audio_base64: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations: Citation[];
}

// Studio: StudioSource ist strukturgleich zu Citation — Zitat-Chips
// funktionieren in Chat und Studio identisch.
export type StudioSource = Citation;

export interface ReportSection {
  heading: string;
  content: string;
  citations: number[];
}

export interface ReportData {
  title: string;
  sections: ReportSection[];
  sources: StudioSource[];
}

export interface Flashcard {
  front: string;
  back: string;
  citation: number | null;
}

export interface FlashcardsData {
  cards: Flashcard[];
  sources: StudioSource[];
}

export interface QuizQuestion {
  question: string;
  options: string[];
  answer_index: number;
  citation: number | null;
}

export interface QuizData {
  questions: QuizQuestion[];
  sources: StudioSource[];
}

export interface MindmapData {
  mermaid: string;
}
