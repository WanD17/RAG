import client from './client';
import type { QueryResponse } from '../types';

export async function query(question: string): Promise<QueryResponse> {
  const { data } = await client.post<QueryResponse>('/rag/query', { question });
  return data;
}

export function buildStreamUrl(question: string, conversationId?: string): string {
  const base = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
  const token = localStorage.getItem('token') ?? '';
  const params = new URLSearchParams({ question, token });
  if (conversationId) params.set('conversation_id', conversationId);
  return `${base}/rag/query-stream?${params.toString()}`;
}
