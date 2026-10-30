interface BrandHeaderProps {
   demoMode?: boolean
   onHome?: () => void
  gu?: string
 }

export function BrandHeader({ demoMode = false, onHome, gu }: BrandHeaderProps) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="brand text-left rounded-2xl focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#2588ee]"
        onClick={onHome}
        aria-label="어디 버려 처음으로"
      >
        <span className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 40 40" fill="none">
            <path d="M12 12h16l-1.4 19H13.4L12 12Z" fill="currentColor" opacity=".16" />
            <path d="M10 11h20M15 11V8.5A2.5 2.5 0 0 1 17.5 6h5A2.5 2.5 0 0 1 25 8.5V11M14 16l1 11m11-11-1 11" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
            <path d="m16 21 3 3 6-7" stroke="#15A477" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <span className="brand-copy">
          <strong>어디 버려</strong>
          <small>AI 기반 상태 분석형 분리배출 도우미</small>
        </span>
      </button>
      <div className="header-badges">
        {demoMode && <span className="badge badge-demo">데모 모드</span>}
        <span className="region-badge">
          <span className="pin-dot" aria-hidden="true" />
          <span><b>{gu ? `부산광역시 ${gu} 기준` : '부산광역시 기준'}</b><small>부산시·구·군 공식 안내 기반</small></span>
        </span>
      </div>
    </header>
  )
}