import { useState } from 'react'
import type { ReactNode } from 'react'

import { LogoIcon } from '@/components/layout/Logo'
import { Sidebar } from '@/components/layout/Sidebar'
import { MenuIcon } from '@/components/ui/icons'

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-dvh bg-bg">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapsed={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="flex min-h-dvh flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-surface/90 px-4 backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
            className="rounded-lg p-1.5 text-text hover:bg-surface-sunken"
          >
            <MenuIcon />
          </button>
          <span className="flex items-center gap-2">
            <LogoIcon size={26} />
            <span className="text-[15px] font-bold tracking-tight text-[color:var(--color-deep-forest)]">
              VENTORA
            </span>
          </span>
        </header>

        <main className="mx-auto w-full max-w-[1280px] flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {children}
        </main>

        <footer className="border-t border-border px-4 py-4 sm:px-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-[1280px] flex-col items-center justify-between gap-2 text-[12px] text-text-muted sm:flex-row">
            <span>AI-Driven Inventory Intelligence</span>
            <span className="flex items-center gap-1.5">
              <LogoIcon size={16} />
              VENTORA
            </span>
          </div>
        </footer>
      </div>
    </div>
  )
}
