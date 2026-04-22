import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { MessageSquare, FileText, LogOut, Menu, X, Sparkles } from 'lucide-react';
import { useAuth } from '../hooks/use-auth';

const navItems = [
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/documents', icon: FileText, label: 'Documents' },
];

export function Layout() {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const initials = (user?.full_name || user?.email || '?')
    .split(' ')
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="flex h-screen overflow-hidden relative">
      <div className="pointer-events-none fixed -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[120px] animate-float-slow" />
      <div className="pointer-events-none fixed top-1/3 -right-40 w-[400px] h-[400px] rounded-full bg-fuchsia-600/15 blur-[120px] animate-float-slow" style={{ animationDelay: '3s' }} />
      <div className="pointer-events-none fixed -bottom-40 left-1/3 w-[450px] h-[450px] rounded-full bg-pink-500/10 blur-[120px] animate-float-slow" style={{ animationDelay: '6s' }} />

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-72 glass-strong flex flex-col transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="flex items-center gap-3 px-6 py-6 border-b border-white/5">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 flex items-center justify-center shadow-lg shadow-violet-500/40">
              <Sparkles className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-500 to-pink-500 blur-lg opacity-50 animate-pulse-glow -z-10" />
          </div>
          <div>
            <div className="font-bold text-white text-lg tracking-tight">KnowledgeRAG</div>
            <div className="text-[10px] text-zinc-500 uppercase tracking-widest font-medium">Internal AI</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-5 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Workspace</div>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                ${isActive
                  ? 'bg-gradient-to-r from-violet-500/20 to-fuchsia-500/10 text-white shadow-inner'
                  : 'text-zinc-400 hover:bg-white/5 hover:text-white'}`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-gradient-to-b from-violet-400 to-fuchsia-400" />
                  )}
                  <Icon className={`w-4 h-4 transition-colors ${isActive ? 'text-violet-300' : 'group-hover:text-violet-300'}`} />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-3 py-2.5 mb-1 rounded-xl bg-white/[0.03]">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-white text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-zinc-500 text-xs truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-zinc-400 hover:bg-red-500/10 hover:text-red-300 transition-all"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 relative">
        <header className="lg:hidden flex items-center gap-4 px-4 py-3 glass-strong border-b border-white/5">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1.5 rounded-lg text-zinc-300 hover:bg-white/10 transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="font-semibold text-white">KnowledgeRAG</span>
        </header>

        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
