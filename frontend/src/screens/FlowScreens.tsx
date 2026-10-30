import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import type { components } from '../lib/api-types'
import type { Decision } from '../lib/api'
import { isNotRecyclable } from '../lib/result'
import { DistrictGuide } from '../components/DistrictGuide'

const GU_LIST: components['schemas']['Region']['gu'][] = [
  '강서구', '금정구', '기장군', '남구', '동구', '동래구', '부산진구', '북구',
  '사상구', '사하구', '서구', '수영구', '연제구', '영도구', '중구', '해운대구',
]

interface RegionScreenProps {
  gu: components['schemas']['Region']['gu']
  onChange: (gu: components['schemas']['Region']['gu']) => void
  onNext: () => void
}

export function RegionScreen({ gu, onChange, onNext }: RegionScreenProps) {
  return (
    <section className="screen-content">
      <p className="eyebrow">STEP 01 · REGION</p>
      <h1>지역을 선택해주세요</h1>
      <p className="screen-lead">거주하는 부산광역시 구·군을 선택하면 해당 지역 기준으로 안내를 시작합니다.</p>
      <div className="field-group">
        <label htmlFor="sido">시·도</label>
        <div className="select-wrap"><select id="sido" value="부산광역시" disabled><option>부산광역시</option></select><span>⌄</span></div>
      </div>
      <div className="field-group">
        <label htmlFor="gu">구·군</label>
        <div className="select-wrap"><select id="gu" value={gu} onChange={(event: ChangeEvent<HTMLSelectElement>) => onChange(event.target.value as components['schemas']['Region']['gu'])}>{GU_LIST.map((item) => <option key={item}>{item}</option>)}</select><span>⌄</span></div>
      </div>
      <div className="helper-panel"><span className="helper-icon">i</span><p>현재 MVP는 부산광역시 공통 규칙을 사용하며, 선택한 구·군 정보는 지역 표시와 익명 통계에 사용됩니다.</p></div>
      <button className="button button-primary button-wide" onClick={onNext}>다음 <span>→</span></button>
    </section>
  )
}

interface CameraScreenProps {
  previewUrl: string | null
  loading: boolean
  error: string | null
  isReshoot: boolean
  onFile: (file: File) => void
  onAnalyze: () => void
  onBack: () => void
  onClear: () => void
}

export function CameraScreen({ previewUrl, loading, error, isReshoot, onFile, onAnalyze, onBack, onClear }: CameraScreenProps) {
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const galleryInputRef = useRef<HTMLInputElement>(null)
  const [pickerOpen, setPickerOpen] = useState(false)

  useEffect(() => {
    if (!pickerOpen) return
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setPickerOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pickerOpen])

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) onFile(file)
    event.target.value = ''
  }
  // 파일 입력은 사용자의 탭 안에서 바로 click()해야 브라우저가 막지 않는다
  const openCamera = () => { setPickerOpen(false); cameraInputRef.current?.click() }
  const openGallery = () => { setPickerOpen(false); galleryInputRef.current?.click() }

  return (
    <section className="screen-content">
      <p className="eyebrow">STEP 02 · PHOTO</p>
      <h1>{isReshoot ? '세척한 상태를 다시 촬영해주세요' : '버릴 물건을 촬영해주세요'}</h1>
      <p className="screen-lead">버릴 쓰레기가 잘 보이게 찍어주세요. 컵·뚜껑·빨대처럼 붙어 있는 구성품은 각각 안내해 드려요. 사람 얼굴이나 택배 송장의 이름·주소·전화번호가 보이지 않게 해주세요.</p>
      <input ref={cameraInputRef} className="visually-hidden" type="file" accept="image/*" capture="environment" onChange={handleFileChange} />
      <input ref={galleryInputRef} className="visually-hidden" type="file" accept="image/*" onChange={handleFileChange} />
      {previewUrl ? (
        <div className="preview-card">
          <img src={previewUrl} alt="업로드한 쓰레기 사진 미리보기" />
          <div className="preview-actions"><span className="file-status"><span className="status-dot" /> 사진이 준비되었습니다.</span><button className="text-button" onClick={onClear}>사진 삭제</button></div>
        </div>
      ) : (
        <button className="upload-zone" onClick={() => setPickerOpen(true)} type="button">
          <span className="upload-icon"><svg viewBox="0 0 48 48" fill="none"><path d="M8 32V38a3 3 0 0 0 3 3h26a3 3 0 0 0 3-3v-6M24 32V7m0 0-9 9m9-9 9 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M7 25h8l4-6h10l4 6h8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity=".55"/></svg></span>
          <strong>사진을 촬영하거나 업로드하세요</strong>
          <span>JPG, PNG · 긴 변 1280px로 자동 조정</span>
          <span className="button button-secondary">사진 선택하기</span>
        </button>
      )}
      <div className="privacy-note"><span>🔒</span><p>사진은 분석을 위해 Google Gemini API로 전송되며, 본 서비스는 사진을 저장하지 않습니다. 개인정보가 담긴 사진은 올리지 마세요.</p></div>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <div className="button-row">
        <button className="button button-ghost" onClick={onBack}>이전</button>
        <button className="button button-primary" disabled={!previewUrl || loading} onClick={onAnalyze}>{loading ? '사진 처리 중...' : 'AI 분석 시작하기'} <span>→</span></button>
      </div>

      {pickerOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-label="사진 가져오는 방법 선택">
          <button type="button" aria-label="닫기" className="absolute inset-0 bg-black/40" onClick={() => setPickerOpen(false)} />
          <div className="relative w-full max-w-md rounded-t-3xl bg-white p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-xl sm:rounded-3xl">
            <p className="mb-3 text-center text-sm font-bold text-[#112d50]">사진을 어떻게 가져올까요?</p>
            <div className="grid gap-2">
              <button type="button" className="button button-primary button-wide" onClick={openCamera}>📷 사진 찍기</button>
              <button type="button" className="button button-secondary button-wide" onClick={openGallery}>🖼️ 갤러리에서 선택하기</button>
              <button type="button" className="button button-ghost button-wide" onClick={() => setPickerOpen(false)}>취소</button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}


export function ObservingScreen({ previewUrl }: { previewUrl: string | null }) {
  const checks = ['물체 인식 중', '오염 상태 확인 중', '부착물 확인 중']
  return (
    <section className="screen-content centered-screen">
      <p className="eyebrow">STEP 03 · AI OBSERVATION</p>
      <div className="scan-visual">
        {previewUrl ? <img src={previewUrl} alt="분석 중인 쓰레기 사진" /> : <span className="scan-placeholder">▧</span>}
        <span className="scan-line" />
        <span className="scan-corner corner-tl" /><span className="scan-corner corner-tr" /><span className="scan-corner corner-bl" /><span className="scan-corner corner-br" />
      </div>
      <h1>AI가 사진을 분석하고 있습니다...</h1>
      <p className="screen-lead">사진에서 확인되는 종류와 상태를 살펴보고 있어요.</p>
      <div className="progress-check-list">{checks.map((label) => <div className="progress-check" key={label}><span className="mini-spinner" />{label}</div>)}</div>
    </section>
  )
}

interface QuestionScreenProps {
  decision: Decision
  answer: 'yes' | 'no' | 'unknown' | null
  onAnswer: (value: 'yes' | 'no' | 'unknown') => void
  onSubmit: () => void
  loading: boolean
}

export function QuestionScreen({ decision, answer, onAnswer, onSubmit, loading }: QuestionScreenProps) {
  const question = decision.question
  return (
    <section className="screen-content">
      <p className="eyebrow">STEP 04 · EXTRA CHECK</p>
      <h1>조금 더 확인할게요</h1>
      <p className="screen-lead">사진만으로 판단하기 어려운 내용이 있어요. 아래 질문에 답해주세요.</p>
      <div className="question-box"><span className="question-icon">?</span><strong>{question?.text ?? '이물질을 제거할 수 있나요?'}</strong></div>
      <div className="radio-list">
        {(question?.options ?? [
          { v: 'yes' as const, l: '네, 제거할 수 있어요' },
          { v: 'no' as const, l: '아니요, 제거할 수 없어요' },
          { v: 'unknown' as const, l: '잘 모르겠어요' },
        ]).map((option) => (
          <label className={`radio-option ${answer === option.v ? 'selected' : ''}`} key={option.v}>
            <input type="radio" name="contamination" value={option.v} checked={answer === option.v} onChange={() => onAnswer(option.v)} />
            <span className="radio-indicator" />
            <span>{option.l}</span>
          </label>
        ))}
      </div>
      <button className="button button-primary button-wide" disabled={!answer || loading} onClick={onSubmit}>{loading ? '확인 중...' : '답변 제출하기'} <span>→</span></button>
    </section>
  )
}

export function RuleLookupScreen({ gu }: { gu: string }) {
  const checks = ['품목 분류 매칭 중', '부산시·구·군 규칙 조회 중', '최종 판단 생성 중']
  return (
    <section className="screen-content centered-screen">
      <p className="eyebrow">STEP 04 · RULE CHECK</p>
      <div className="lookup-icon"><span>⌖</span></div>
      <h1>부산광역시 기준으로 판단하고 있어요...</h1>
      <p className="screen-lead">선택 지역: 부산광역시 {gu}</p>
      <div className="progress-check-list">{checks.map((label) => <div className="progress-check" key={label}><span className="mini-spinner" />{label}</div>)}</div>
    </section>
  )
}

export function WashGuideScreen({ decision, onRetake }: { decision: Decision; onRetake: () => void }) {
  const checklist = decision.wash_checklist ?? ['남은 음식물 제거', '물로 깨끗이 헹구기', '이물질이 남지 않도록 세척하기']
  return (
    <section className="screen-content">
      <p className="eyebrow">CHECK · WASH & RESHOOT</p>
      <div className="status-heading status-warning"><span>!</span><div><h1>{decision.headline}</h1><p>이물질을 제거할 수 있다고 답변했어요.</p></div></div>
      <div className="checklist-card">{checklist.map((item) => <div className="checklist-row" key={item}><span className="checkmark">✓</span>{item}</div>)}</div>
      <p className="screen-lead">세척을 마친 뒤 같은 물건을 다시 촬영해주세요. 재촬영은 한 번만 진행됩니다.</p>
      <button className="button button-primary button-wide" onClick={onRetake}>세척 후 다시 촬영하기 <span>→</span></button>
    </section>
  )
}

export function ResultScreen({ decision, demoMode, previewUrl, onRestart }: { decision: Decision; demoMode: boolean; previewUrl: string | null; onRestart: () => void }) {
  const isGeneral = isNotRecyclable(decision)
  return (
    <section className="screen-content result-screen">
      <p className="eyebrow">ANALYSIS COMPLETE</p>
      {(!decision.rules_verified || demoMode) && <div className="result-badges">{!decision.rules_verified && <span className="badge badge-demo">시연용 규칙 · 부산시 공식 기준 대조 전</span>}{demoMode && <span className="badge badge-info">데모 모드</span>}</div>}
      {previewUrl && (
        <div className="multi-summary">
          <img src={previewUrl} alt="분석한 쓰레기 사진" />
          <div>
            <h2 className="summary-title">사진에서 1개 항목을 찾았어요</h2>
            <p className="screen-lead">분석한 사진 기준으로 배출 방법을 안내해요.</p>
          </div>
        </div>
      )}
      <div className={`result-hero ${isGeneral ? 'result-general' : 'result-recycle'}`}>
        <span className="result-icon">{isGeneral ? '×' : '✓'}</span>
        <div><p>{decision.basis_label}</p><h1>{decision.headline}</h1></div>
      </div>
      <section className="result-section">
        <h2><span className="section-symbol">▤</span> AI 분석 결과</h2>
        {decision.analysis_bullets.length ? <ul className="analysis-list">{decision.analysis_bullets.map((bullet, index) => <li key={`${bullet}-${index}`}>{bullet}</li>)}</ul> : <p className="muted-text">표시할 분석 항목이 없습니다.</p>}
      </section>
      <section className="result-section">
        <h2><span className="section-symbol">☷</span> 배출 방법</h2>
        {decision.steps.length ? <ol className="disposal-steps">{decision.steps.map((step, index) => <li key={`${step}-${index}`}><span>{index + 1}</span><p>{step}</p></li>)}</ol> : <p className="muted-text">표시할 배출 방법이 없습니다.</p>}
      </section>
      <DistrictGuide info={decision.district_info} />
      <section className="source-panel">
        <h2><span className="section-symbol">↗</span> 근거 자료</h2>
        {decision.source.url && decision.rules_verified ? <a href={decision.source.url} target="_blank" rel="noreferrer">{decision.source.label} <span>↗</span></a> : <p>{decision.source.label}</p>}
      </section>
      {isGeneral && <p className="result-footnote">이물질이 제거되지 않은 경우 재촬영 단계로 진행하지 않습니다.</p>}
      <button className="button button-primary button-wide" onClick={onRestart}>처음으로 돌아가기</button>
    </section>
  )
}

export function ReshootNoticeScreen({ reason, canRetake, onRetake, onRestart }: { reason: 'quality' | 'privacy' | null; canRetake: boolean; onRetake: () => void; onRestart: () => void }) {
  return (
    <section className="screen-content centered-screen notice-screen">
      <div className="notice-icon">!</div>
      <p className="eyebrow">PHOTO CHECK</p>
      <h1>{canRetake ? '사진이 불명확해요.' : '정확히 판단하기 어려워요.'}</h1>
      <p className="screen-lead">{canRetake ? (reason === 'privacy' ? '얼굴이나 택배 송장 정보가 보여요. 보이지 않게 가리고 다시 찍어주세요.' : '밝은 곳에서 쓰레기 하나만 크게 다시 찍어주세요.') : '한 번 다시 촬영했지만 사진을 확인하기 어렵습니다. 처음부터 다시 시작해주세요.'}</p>
      {canRetake ? <button className="button button-primary button-wide" onClick={onRetake}>다시 촬영하기</button> : <button className="button button-primary button-wide" onClick={onRestart}>처음으로 돌아가기</button>}
    </section>
  )
}

export function UnknownNoticeScreen({ onRestart }: { onRestart: () => void }) {
  return (
    <section className="screen-content centered-screen notice-screen">
      <div className="notice-icon notice-blue">?</div>
      <p className="eyebrow">MORE INFORMATION NEEDED</p>
      <h1>정확히 판단하기 어려워요.</h1>
      <p className="screen-lead">거주 지역(구·군)의 최신 공식 분리배출 안내를 확인해주세요.</p>
      <button className="button button-primary button-wide" onClick={onRestart}>처음으로</button>
    </section>
  )
}

export function ErrorScreen({ message, onRetry, onRestart }: { message: string; onRetry: () => void; onRestart: () => void }) {
  return (
    <section className="screen-content centered-screen notice-screen">
      <div className="notice-icon notice-red">!</div>
      <p className="eyebrow">TEMPORARY ERROR</p>
      <h1>잠시 후 다시 시도해주세요.</h1>
      <p className="screen-lead">{message}</p>
      <div className="button-row"><button className="button button-ghost" onClick={onRestart}>처음으로</button><button className="button button-primary" onClick={onRetry}>다시 시도</button></div>
    </section>
  )
}
