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
