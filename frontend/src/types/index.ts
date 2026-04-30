export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
  timestamp: Date;
}

export interface SourceDocument {
  document_id: string;
  filename: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDocument[];
  conversation_id: string;
}
