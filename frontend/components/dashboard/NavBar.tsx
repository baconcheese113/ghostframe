'use client';

interface NavBarProps {
  onTogglePanel: () => void;
}

export default function NavBar({ onTogglePanel }: NavBarProps) {
  return (
    <nav
      className="glass-strong sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 py-3"
      style={{ minHeight: '52px' }}
    >
      {/* Logo */}
      <span
        className="font-display text-lg sm:text-xl font-bold tracking-widest"
        style={{ color: '#22d3ee', letterSpacing: '0.2em' }}
      >
        GHOSTFRAME
      </span>

      {/* Dataset chip */}
      <div
        className="hidden sm:flex items-center gap-2 rounded-full px-3 py-1 text-xs font-data"
        style={{
          background: 'rgba(34,211,238,0.08)',
          border: '1px solid rgba(34,211,238,0.2)',
          color: '#94a3b8',
        }}
      >
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{ background: '#4ade80', boxShadow: '0 0 6px #4ade80' }}
        />
        HPV16 / K02718.1
      </div>

      {/* New Analysis button */}
      <button
        onClick={onTogglePanel}
        className="flex items-center gap-2 rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium transition-all"
        style={{
          background: 'rgba(34,211,238,0.1)',
          border: '1px solid rgba(34,211,238,0.25)',
          color: '#22d3ee',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLButtonElement).style.background = 'rgba(34,211,238,0.18)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLButtonElement).style.background = 'rgba(34,211,238,0.1)';
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path
            d="M7 1v12M1 7h12"
            stroke="#22d3ee"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
        <span className="hidden sm:inline">New Analysis</span>
      </button>
    </nav>
  );
}
