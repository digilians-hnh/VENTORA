import { NavLink } from 'react-router-dom'

import { LogoIcon, Wordmark } from '@/components/layout/Logo'
import {
  ChevronLeftIcon,
  CloseIcon,
  ExplorerIcon,
  HomeIcon,
  ImpactIcon,
  OverviewIcon,
  RecommendationsIcon,
} from '@/components/ui/icons'

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: HomeIcon, end: true },
  { to: '/overview', label: 'Overview', icon: OverviewIcon, end: false },
  { to: '/risk-explorer', label: 'Risk Explorer', icon: ExplorerIcon, end: false },
  { to: '/recommendations', label: 'Recommendations', icon: RecommendationsIcon, end: false },
  { to: '/business-impact', label: 'Business Impact', icon: ImpactIcon, end: false },
]

interface SidebarProps {
  collapsed: boolean
  onToggleCollapsed: () => void
  mobileOpen: boolean
  onCloseMobile: () => void
}

function NavList({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1 px-3" aria-label="Primary">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] font-medium transition-colors ${
              isActive
                ? 'bg-[color:var(--color-sidebar-active)] text-white'
                : 'text-text-on-dark-muted hover:bg-[color:var(--color-sidebar-hover)] hover:text-white'
            }`
          }
          title={collapsed ? label : undefined}
        >
          <Icon className="shrink-0" />
          {!collapsed && <span className="truncate">{label}</span>}
        </NavLink>
      ))}
    </nav>
  )
}

export function Sidebar({ collapsed, onToggleCollapsed, mobileOpen, onCloseMobile }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-[color:var(--color-sidebar-border)] bg-[color:var(--color-sidebar)] transition-[width] duration-200 lg:flex ${
          collapsed ? 'w-[76px]' : 'w-[248px]'
        }`}
      >
        <div className={`flex h-16 items-center border-b border-[color:var(--color-sidebar-border)] ${collapsed ? 'justify-center px-2' : 'px-5'}`}>
          {collapsed ? (
            <LogoIcon size={28} />
          ) : (
            <Wordmark tagline />
          )}
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <NavList collapsed={collapsed} />
        </div>

        <div className="border-t border-[color:var(--color-sidebar-border)] p-3">
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex w-full items-center justify-center gap-2 rounded-lg py-2 text-[12px] font-medium text-text-on-dark-muted transition-colors hover:bg-[color:var(--color-sidebar-hover)] hover:text-white"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeftIcon className={`transition-transform ${collapsed ? 'rotate-180' : ''}`} />
            {!collapsed && 'Collapse'}
          </button>
          {!collapsed && (
            <p className="mt-3 px-1 text-[10.5px] leading-snug text-text-on-dark-muted/70">
              AI-Driven Inventory Intelligence
            </p>
          )}
        </div>
      </aside>

      {/* Mobile off-canvas drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute inset-0 bg-black/40"
            onClick={onCloseMobile}
          />
          <aside className="absolute left-0 top-0 flex h-dvh w-[80%] max-w-[280px] flex-col bg-[color:var(--color-sidebar)] shadow-xl">
            <div className="flex h-16 items-center justify-between border-b border-[color:var(--color-sidebar-border)] px-4">
              <Wordmark tagline />
              <button
                type="button"
                onClick={onCloseMobile}
                aria-label="Close navigation"
                className="rounded-lg p-1.5 text-text-on-dark-muted hover:bg-[color:var(--color-sidebar-hover)] hover:text-white"
              >
                <CloseIcon />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto py-4">
              <NavList collapsed={false} onNavigate={onCloseMobile} />
            </div>
            <div className="border-t border-[color:var(--color-sidebar-border)] p-4">
              <p className="text-[10.5px] leading-snug text-text-on-dark-muted/70">
                AI-Driven Inventory Intelligence
              </p>
            </div>
          </aside>
        </div>
      )}
    </>
  )
}
