const steps = ['지역 선택', '사진 촬영', 'AI 분석', '배출 판단']

const stepByScreen: Record<string, number> = {
  REGION: 0,
  CAMERA: 1,
  OBSERVING: 2,
  NOTICE_RESHOOT: 1,
  QUESTION: 3,
  RULE_LOOKUP: 3,
  WASH_GUIDE: 3,
  RESULT: 3,
  NOTICE_UNKNOWN: 3,
  ERROR: 2,
}

export function ProgressSteps({ screen }: { screen: string }) {
  const active = stepByScreen[screen] ?? 0
  return (
    <nav className="progress-steps" aria-label="분리배출 진행 단계">
      {steps.map((step, index) => (
        <div className={`progress-step ${index < active ? 'is-done' : ''} ${index === active ? 'is-active' : ''}`} key={step}>
          <span className="step-number">{index < active ? '✓' : index + 1}</span>
          <span className="step-label">{step}</span>
        </div>
      ))}
    </nav>
  )
}
