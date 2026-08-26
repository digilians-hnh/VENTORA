import ventoraFull from '@/assets/ventora-full.png'
import ventoraMark from '@/assets/ventora-mark.png'

/**
 * Compact icon-only mark, cropped from the official VENTORA logo asset.
 * Used anywhere space is tight: collapsed sidebar, mobile header, favicons.
 */
export function LogoIcon({ size = 28, className = '' }: { size?: number; className?: string }) {
  return (
    <img
      src={ventoraMark}
      alt="VENTORA"
      width={size}
      height={size}
      className={className}
      style={{ width: size, height: size, objectFit: 'contain' }}
      draggable={false}
    />
  )
}

/**
 * Icon + wordmark lockup for header/navbar contexts. The icon is the real
 * logo asset; the wordmark is set in the app's own display type so it stays
 * legible at small sizes (a flattened raster wordmark turns unreadable once
 * scaled down to header height).
 */
export function Wordmark({ dark = true, tagline = false }: { dark?: boolean; tagline?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <LogoIcon size={32} />
      <div className="leading-tight">
        <div
          className="font-display text-[17px] font-extrabold tracking-tight"
          style={{
            fontFamily: 'var(--font-display)',
            color: dark ? 'var(--color-off-white)' : 'var(--color-deep-forest)',
          }}
        >
          VENTORA
        </div>
        {tagline && (
          <div
            className="text-[10.5px] font-medium tracking-wide"
            style={{ color: dark ? 'var(--color-text-on-dark-muted)' : 'var(--color-text-muted)' }}
          >
            Predict. Optimize. Preserve.
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Full official lockup (mark + wordmark + tagline) for larger, standalone
 * brand moments — e.g. the homepage hero. Not for cramped spaces.
 */
export function LogoFull({ width = 220, className = '' }: { width?: number; className?: string }) {
  return (
    <img
      src={ventoraFull}
      alt="VENTORA — Predict. Optimize. Preserve."
      width={width}
      className={className}
      style={{ width, height: 'auto', objectFit: 'contain' }}
      draggable={false}
    />
  )
}
