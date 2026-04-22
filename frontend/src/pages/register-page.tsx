import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Mail, Lock, User, ArrowRight } from 'lucide-react';
import { useAuth } from '../hooks/use-auth';

export function RegisterPage() {
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    try {
      await register(fullName, email, password);
      navigate('/login');
    } catch {
      setError('Registration failed. Email may already be in use.');
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10 relative overflow-hidden">
      <div className="pointer-events-none absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-violet-600/20 blur-[120px] animate-float-slow" />
      <div className="pointer-events-none absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full bg-fuchsia-600/15 blur-[120px] animate-float-slow" style={{ animationDelay: '4s' }} />

      <div className="w-full max-w-md relative animate-fade-up">
        <div className="flex flex-col items-center mb-8">
          <div className="relative mb-5">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 flex items-center justify-center shadow-xl shadow-violet-500/50">
              <Sparkles className="w-7 h-7 text-white" strokeWidth={2.5} />
            </div>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-violet-500 to-pink-500 blur-xl opacity-60 -z-10" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Create account</h1>
          <p className="text-zinc-400 text-sm mt-2">Start using <span className="gradient-text font-semibold">KnowledgeRAG</span> today</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-strong gradient-border rounded-2xl p-7 space-y-5 shadow-2xl shadow-black/40">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-300 text-sm rounded-xl px-4 py-3 animate-fade-up">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider">Full name</label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="input-dark w-full rounded-xl pl-10 pr-3 py-3 text-sm"
                placeholder="Jane Doe"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider">Email</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="input-dark w-full rounded-xl pl-10 pr-3 py-3 text-sm"
                placeholder="you@example.com"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                className="input-dark w-full rounded-xl pl-10 pr-3 py-3 text-sm"
                placeholder="Min. 8 characters"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider">Confirm password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                autoComplete="new-password"
                className="input-dark w-full rounded-xl pl-10 pr-3 py-3 text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary group w-full flex items-center justify-center gap-2 text-white font-semibold py-3 rounded-xl text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Creating account...' : <>Create account <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" /></>}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-violet-300 hover:text-violet-200 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
