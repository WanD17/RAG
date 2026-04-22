import client from './client';
import type { Document } from '../types';

export async function listDocuments(): Promise<Document[]> {
  const { data } = await client.get<{ documents: Document[]; total: number }>('/documents');
  return data.documents;
}

export async function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await client.post<{ document: Document }>('/documents/upload', form);
  return data.document;
}

export async function deleteDocument(id: string): Promise<void> {
  await client.delete(`/documents/${id}`);
}
