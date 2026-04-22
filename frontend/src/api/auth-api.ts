import client from './client';
import type { AuthResponse } from '../types';

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>('/auth/login', { email, password });
  return data;
}

export async function register(
  full_name: string,
  email: string,
  password: string
): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>('/auth/register', {
    full_name,
    email,
    password,
  });
  return data;
}
