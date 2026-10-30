import type { Decision, Observation } from '../lib/api'
import { isNotRecyclable } from '../lib/result'
import { DistrictGuide } from '../components/DistrictGuide'

type Answer = 'yes' | 'no' | 'unknown'

export interface ItemResult {
  observation: Observation
  decision: Decision
  loading?: boolean
}

interface MultiResultScreenProps {
  items: ItemResult[]
  previewUrl: string | null
  demoMode: boolean
  onAnswer: (index: number, answer: Answer) => void
  onRetakeItem: (index: number) => void
  onRestart: () => void
}

/** 사진 1장에서 찾은 항목(구성품)별 결과 카드. 항목마다 /api/decide 결과를 그대로 보여준다. */
export function MultiResultScreen({ items, previewUrl, demoMode, onAnswer, onRetakeItem, onRestart }: MultiResultScreenProps) {
  const first = items[0]?.decision
  const groups = groupItems(items)
  return (
    <section className="screen-content result-screen">
      <p className="eyebrow">ANALYSIS COMPLETE · {items.length} ITEMS</p>
      {first && (!first.rules_verified || demoMode) && (
        <div className="result-badges">
          {!first.rules_verified && <span className="badge badge-demo">시연용 규칙 · 부산시 공식 기준 대조 전</span>}
          {demoMode && <span className="badge badge-info">데모 모드</span>}
        </div>
      )}
      <div className="multi-summary">
        {previewUrl && <img src={previewUrl} alt="분석한 쓰레기 사진" />}
        <div>
          <h1>사진에서 {items.length}개 항목을 찾았어요</h1>
          <p className="screen-lead">따로 버려야 하는 구성품마다 배출 방법을 안내해요.</p>
        </div>
      </div>
      <div className="multi-cards">
        {groups.map((group, index) => (
          <ItemCard key={group.indices[0]} index={index} item={group.item} count={group.indices.length}
            onAnswer={(_, answer) => group.indices.forEach((i) => onAnswer(i, answer))}
            onRetakeItem={() => onRetakeItem(group.indices[0])} />
        ))}
      </div>
      <button className="button button-primary button-wide" onClick={onRestart}>처음으로 돌아가기</button>
    </section>
  )
}

interface ItemGroup {
  item: ItemResult
  indices: number[]
}

/** 카드 제목(label_ko)과 판정 결과(decision)가 같은 항목만 한 카드로 묶는다. 판정이 다르면(예: 하나만 오염) 따로 남는다. */
function groupItems(items: ItemResult[]): ItemGroup[] {
  const groups: ItemGroup[] = []
  const byKey = new Map<string, ItemGroup>()
  items.forEach((item, index) => {
    const key = JSON.stringify([item.observation.label_ko, item.decision])
    const found = byKey.get(key)
    if (found) { found.indices.push(index); return }
    const group = { item, indices: [index] }
    byKey.set(key, group)
    groups.push(group)
  })
  return groups
}

function ItemCard({ index, item, count, onAnswer, onRetakeItem }: { index: number; item: ItemResult; count: number; onAnswer: MultiResultScreenProps['onAnswer']; onRetakeItem: MultiResultScreenProps['onRetakeItem'] }) {
  const { decision, observation, loading } = item
  const baseTitle = observation.label_ko || `항목 ${index + 1}`
  const title = count > 1 ? `${baseTitle} ×${count}` : baseTitle

  if (decision.kind === 'ASK_QUESTION' && decision.question) {
    return (
      <article className="item-card item-warning">
        <header><span className="item-index">{index + 1}</span><strong>{title}</strong></header>
        <p className="item-headline">{decision.question.text}</p>
        <div className="item-options">
          {decision.question.options.map((option) => (
            <button key={option.v} type="button" className="button button-secondary" disabled={loading} onClick={() => onAnswer(index, option.v)}>{option.l}</button>
          ))}
        </div>
      </article>
    )
  }

  if (decision.kind === 'WASH_AND_RESHOOT') {
    return (
      <article className="item-card item-warning">
        <header><span className="item-index">{index + 1}</span><strong>{title}</strong></header>
        <p className="item-headline">{decision.headline}</p>
        <ul className="analysis-list">{(decision.wash_checklist ?? []).map((step) => <li key={step}>{step}</li>)}</ul>
        <button type="button" className="button button-secondary button-wide" onClick={() => onRetakeItem(index)}>세척 후 이 물건만 다시 촬영하기</button>
      </article>
    )
  }

  if (decision.kind === 'RESHOOT_QUALITY' || decision.kind === 'UNKNOWN') {
    const text = decision.kind === 'UNKNOWN'
      ? '정확히 판단하기 어려워요. 거주 지역의 최신 공식 분리배출 안내를 확인해주세요.'
      : '사진에서 잘 보이지 않아요. 이 물건만 따로 크게 찍어 확인해주세요.'
    return (
      <article className="item-card item-muted">
        <header><span className="item-index">{index + 1}</span><strong>{title}</strong></header>
        <p className="item-headline">{text}</p>
      </article>
    )
  }

  const bad = isNotRecyclable(decision)
  return (
    <article className={`item-card ${bad ? 'item-general' : 'item-recycle'}`}>
      <header><span className="item-index">{bad ? '×' : '✓'}</span><strong>{title}</strong></header>
      <p className="item-headline">{decision.headline}</p>
      {decision.analysis_bullets.length > 0 && <ul className="analysis-list">{decision.analysis_bullets.map((b, i) => <li key={`${b}-${i}`}>{b}</li>)}</ul>}
      <ol className="disposal-steps">{decision.steps.map((step, i) => <li key={`${step}-${i}`}><span>{i + 1}</span><p>{step}</p></li>)}</ol>
      <DistrictGuide info={decision.district_info} />
      <p className="item-source">
        근거:{' '}
        {decision.source.url && decision.rules_verified
          ? <a href={decision.source.url} target="_blank" rel="noreferrer">{decision.source.label} ↗</a>
          : decision.source.label}
      </p>
    </article>
  )
}
