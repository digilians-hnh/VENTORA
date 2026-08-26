import { useRef, useState } from 'react'

import { DownloadIcon } from '@/components/ui/icons'

interface FileDropzoneProps {
  label: string
  hint: string
  file: File | null
  onFileSelected: (file: File | null) => void
  disabled?: boolean
}

export function FileDropzone({ label, hint, file, onFileSelected, disabled }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)

  function handleFiles(fileList: FileList | null) {
    const f = fileList?.[0]
    if (!f) return
    onFileSelected(f)
  }

  return (
    <div>
      <p className="mb-1.5 text-[13px] font-semibold text-text">{label}</p>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragActive(false)
          if (!disabled) handleFiles(e.dataTransfer.files)
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-6 text-center transition-colors ${
          disabled ? 'cursor-not-allowed opacity-50' : ''
        } ${
          dragActive
            ? 'border-[color:var(--color-brand-green)] bg-[color:var(--color-brand-green)]/5'
            : file
              ? 'border-[color:var(--color-success)]/50 bg-[color:var(--color-success)]/5'
              : 'border-border-strong bg-surface-sunken/40 hover:border-border-strong'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
        />
        <DownloadIcon className="mb-2 rotate-180 text-text-muted" width={20} height={20} />
        {file ? (
          <>
            <p className="text-[13px] font-medium text-text">{file.name}</p>
            <p className="text-[11.5px] text-text-muted">{(file.size / 1024).toFixed(1)} KB · click to replace</p>
          </>
        ) : (
          <>
            <p className="text-[13px] font-medium text-text">Drop CSV here, or click to browse</p>
            <p className="mt-0.5 text-[11.5px] text-text-muted">{hint}</p>
          </>
        )}
      </div>
    </div>
  )
}
