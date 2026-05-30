import { NavLink } from 'react-router-dom';
import { BarChart3, TrendingUp, Briefcase, History, ShieldAlert, Bot } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { to: '/trades', label: 'Trades', icon: History },
  { to: '/analytics', label: 'Analytics', icon: TrendingUp },
  { to: '/risk', label: 'Risk', icon: ShieldAlert },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-800">
        <Bot className="w-8 h-8 text-blue-400" />
        <div>
          <h1 className="text-sm font-bold text-white">AI Trading Agent</h1>
          <p className="text-xs text-gray-400">Platform v0.1.0</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Status indicator */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-gray-400">System Online</span>
        </div>
      </div>
    </aside>
  );
}
