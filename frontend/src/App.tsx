import { useCallback, useMemo, useReducer, useRef, useState } from 'react'
import type { components } from './lib/api-types'
import { ApiError, decideWaste, observeImage } from './lib/api'
import type { Decision } from './lib/api'
import { getFixtureObserveResponse } from './lib/fixture-observations'
import { resizeImage } from './lib/image'
import { BrandHeader } from './components/BrandHeader'
import { ProgressSteps } from './components/ProgressSteps'
import { Disclaimer } from './components/Disclaimer'
import { MultiResultScreen } from './screens/MultiResultScreen'
import type { ItemResult } from './screens/MultiResultScreen'
import {
  CameraScreen,
  ErrorScreen,
  ObservingScreen,
  QuestionScreen,
  RegionScreen,
  ReshootNoticeScreen,
  ResultScreen,
  RuleLookupScreen,
  UnknownNoticeScreen,
  WashGuideScreen,
} from './screens/FlowScreens'

 type Gu = components['schemas']['Region']['gu']
 type Screen = 'REGION' | 'CAMERA' | 'OBSERVING' | 'NOTICE_RESHOOT' | 'QUESTION' | 'RULE_LOOKUP' | 'WASH_GUIDE' | 'RESULT' | 'MULTI_RESULT' | 'NOTICE_UNKNOWN' | 'ERROR'
 type Answer = 'yes' | 'no' | 'unknown'

interface AppState {
  screen: Screen
  gu: Gu
  image: Blob | null
  previewUrl: string | null
  observation: components['schemas']['Observation'] | null
  decision: Decision | null
  answer: Answer | null
  attempt: 1 | 2
  demoMode: boolean
  reshootReason: 'quality' | 'privacy' | null
  errorMessage: string
  // 사진 1장에서 항목이 여러 개일 때 항목별 결과 (1개면 비어 있고 기존 단일 흐름을 쓴다)
  multiItems: ItemResult[]
}

type Action =
  | { type: 'SET_GU'; gu: Gu }
  | { type: 'SET_IMAGE'; image: Blob; previewUrl: string }
  | { type: 'CLEAR_IMAGE' }
  | { type: 'SCREEN'; screen: Screen }
  | { type: 'OBSERVED'; observation: components['schemas']['Observation']; demoMode: boolean }
  | { type: 'DECIDED'; decision: Decision }
  | { type: 'SET_ANSWER'; answer: Answer }
  | { type: 'SET_ATTEMPT'; attempt: 1 | 2 }
  | { type: 'RESHOOT_REASON'; reason: 'quality' | 'privacy' | null }
  | { type: 'ERROR'; message: string }
  | { type: 'MULTI_SET'; items: ItemResult[] }
  | { type: 'MULTI_UPDATE'; index: number; item: ItemResult }
  | { type: 'RESET' }

const initialState: AppState = {
  screen: 'REGION', gu: '해운대구', image: null, previewUrl: null, observation: null,
  decision: null, answer: null, attempt: 1, demoMode: false, reshootReason: null, errorMessage: '',
  multiItems: [],
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_GU': return { ...state, gu: action.gu }
    case 'SET_IMAGE': return { ...state, image: action.image, previewUrl: action.previewUrl, errorMessage: '' }
    case 'CLEAR_IMAGE': return { ...state, image: null, previewUrl: null }
    case 'SCREEN': return { ...state, screen: action.screen }
    case 'OBSERVED': return { ...state, observation: action.observation, demoMode: action.demoMode, reshootReason: null }
    case 'DECIDED': return { ...state, decision: action.decision }
    case 'SET_ANSWER': return { ...state, answer: action.answer }
    case 'SET_ATTEMPT': return { ...state, attempt: action.attempt, answer: null, decision: null }
    case 'RESHOOT_REASON': return { ...state, reshootReason: action.reason }
    case 'ERROR': return { ...state, screen: 'ERROR', errorMessage: action.message }
    case 'MULTI_SET': return { ...state, multiItems: action.items }
    case 'MULTI_UPDATE': return { ...state, multiItems: state.multiItems.map((item, i) => (i === action.index ? action.item : item)) }
    case 'RESET': return { ...initialState, gu: state.gu }
    default: return state
  }
}

const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'AI_BUSY') return 'AI 분석 요청이 많아 잠시 대기해야 합니다.'
    if (error.code === 'AI_UNAVAILABLE') return 'AI 응답을 받을 수 없습니다. 잠시 후 다시 시도해주세요.'
    return error.message
  }
  return error instanceof Error ? error.message : '요청 중 알 수 없는 오류가 발생했습니다.'
}

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const [busy, setBusy] = useState(false)
  const retryRef = useRef<(() => Promise<void>) | null>(null)

  const region = useMemo(() => ({ sido: '부산광역시' as const, gu: state.gu }), [state.gu])

  const setFile = useCallback(async (file: File) => {
    try {
      const blob = await resizeImage(file)
      const preview = URL.createObjectURL(blob)
      if (state.previewUrl) URL.revokeObjectURL(state.previewUrl)
      dispatch({ type: 'SET_IMAGE', image: blob, previewUrl: preview })
    } catch (error) {
      dispatch({ type: 'ERROR', message: errorMessage(error) })
    }
  }, [state.previewUrl])

  const submitDecision = useCallback(async (answer: Answer | null, observationOverride?: components['schemas']['Observation'], demoModeOverride?: boolean) => {
    const observation = observationOverride ?? state.observation
    if (!observation) throw new Error('분석 결과가 없습니다. 사진을 다시 촬영해주세요.')
    const startedAt = Date.now()
    const shouldShowRuleLookup = answer !== null || state.attempt === 2
    if (shouldShowRuleLookup) dispatch({ type: 'SCREEN', screen: 'RULE_LOOKUP' })
    const payload: components['schemas']['DecideRequest'] = {
      region,
      observation,
      answers: answer ? { contamination_removable: answer } : null,
      attempt: state.attempt,
      demo_mode: demoModeOverride ?? state.demoMode,
    }
    const decision = await decideWaste(payload)
    if (!shouldShowRuleLookup && decision.kind === 'ASK_QUESTION') {
      dispatch({ type: 'DECIDED', decision })
      dispatch({ type: 'SCREEN', screen: 'QUESTION' })
      return
    }
    if (decision.kind === 'UNKNOWN' || decision.kind === 'RESHOOT_QUALITY') {
      dispatch({ type: 'DECIDED', decision })
      if (decision.kind === 'UNKNOWN') dispatch({ type: 'SCREEN', screen: 'NOTICE_UNKNOWN' })
      else {
        dispatch({ type: 'RESHOOT_REASON', reason: decision.reshoot_reason ?? 'quality' })
        dispatch({ type: 'SCREEN', screen: 'NOTICE_RESHOOT' })
      }
      return
    }
    if (!shouldShowRuleLookup) dispatch({ type: 'SCREEN', screen: 'RULE_LOOKUP' })
    await delay(Math.max(0, 1200 - (Date.now() - startedAt)))
    dispatch({ type: 'DECIDED', decision })

    switch (decision.kind) {
      case 'ASK_QUESTION':
        dispatch({ type: 'SCREEN', screen: 'QUESTION' })
        break
      case 'WASH_AND_RESHOOT':
        dispatch({ type: 'SCREEN', screen: 'WASH_GUIDE' })
        break
      case 'FINAL':
        dispatch({ type: 'SCREEN', screen: 'RESULT' })
        break
      default:
        dispatch({ type: 'ERROR', message: '판정 결과를 처리할 수 없습니다.' })
    }
  }, [region, state.attempt, state.demoMode, state.observation])

  // 여러 항목: 항목마다 /api/decide를 동시에 호출해 카드로 모은다. 규칙 판단 연출(최소 1.2초)은 단일 흐름과 같게
  const decideItems = useCallback(async (items: components['schemas']['Observation'][], demoMode: boolean) => {
    const startedAt = Date.now()
    dispatch({ type: 'SCREEN', screen: 'RULE_LOOKUP' })
    const decisions = await Promise.all(items.map((observation) => decideWaste({
      region, observation, answers: null, attempt: state.attempt, demo_mode: demoMode,
    })))
    await delay(Math.max(0, 1200 - (Date.now() - startedAt)))
    dispatch({ type: 'MULTI_SET', items: items.map((observation, i) => ({ observation, decision: decisions[i] })) })
    dispatch({ type: 'SCREEN', screen: 'MULTI_RESULT' })
  }, [region, state.attempt])

  // 카드 안에서 질문에 답하면 그 항목만 다시 판단한다
  const answerItem = useCallback(async (index: number, answer: Answer) => {
    const item = state.multiItems[index]
    if (!item) return
    dispatch({ type: 'MULTI_UPDATE', index, item: { ...item, loading: true } })
    try {
      const decision = await decideWaste({
        region, observation: item.observation, answers: { contamination_removable: answer }, attempt: state.attempt, demo_mode: state.demoMode,
      })
      dispatch({ type: 'MULTI_UPDATE', index, item: { ...item, decision, loading: false } })
    } catch (error) {
      dispatch({ type: 'ERROR', message: errorMessage(error) })
    }
  }, [region, state.attempt, state.demoMode, state.multiItems])

  const runObserve = useCallback(async () => {
    if (!state.image) return
    dispatch({ type: 'SCREEN', screen: 'OBSERVING' })
    const response = getFixtureObserveResponse(state.attempt === 2) ?? await observeImage(state.image, state.attempt === 2)
    if (!response.ok) {
      dispatch({ type: 'RESHOOT_REASON', reason: response.reason ?? 'quality' })
      dispatch({ type: 'SCREEN', screen: 'NOTICE_RESHOOT' })
      return
    }
    dispatch({ type: 'OBSERVED', observation: response.observation, demoMode: response.demo_mode })
    const items = response.items ?? []
    if (items.length > 1) {
      await decideItems(items, response.demo_mode)
      return
    }
    await submitDecision(null, response.observation, response.demo_mode)
  }, [state.image, state.attempt, submitDecision, decideItems])

  const handleAnalyze = useCallback(async () => {
    if (busy || !state.image) return
    setBusy(true)
    retryRef.current = runObserve
    try { await runObserve() }
    catch (error) { dispatch({ type: 'ERROR', message: errorMessage(error) }) }
    finally { setBusy(false) }
  }, [busy, runObserve, state.image])

  const handleQuestionSubmit = useCallback(async () => {
    if (busy || !state.answer) return
    setBusy(true)
    const submit = () => submitDecision(state.answer)
    retryRef.current = submit
    try { await submit() }
    catch (error) { dispatch({ type: 'ERROR', message: errorMessage(error) }) }
    finally { setBusy(false) }
  }, [busy, state.answer, submitDecision])

  const handleRetake = useCallback(() => {
    dispatch({ type: 'SET_ATTEMPT', attempt: 2 })
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl)
    dispatch({ type: 'CLEAR_IMAGE' })
    dispatch({ type: 'SCREEN', screen: 'CAMERA' })
  }, [state.previewUrl])

  const handleNoticeRetake = useCallback(() => {
    if (state.attempt === 2) return
    dispatch({ type: 'SET_ATTEMPT', attempt: 2 })
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl)
    dispatch({ type: 'CLEAR_IMAGE' })
    dispatch({ type: 'SCREEN', screen: 'CAMERA' })
  }, [state.attempt, state.previewUrl])

  const clearImage = useCallback(() => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl)
    dispatch({ type: 'CLEAR_IMAGE' })
  }, [state.previewUrl])

  const restart = useCallback(() => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl)
    dispatch({ type: 'RESET' })
    retryRef.current = null
  }, [state.previewUrl])

  const retry = useCallback(async () => {
    if (busy) return
    if (!retryRef.current) {
      dispatch({ type: 'SCREEN', screen: 'CAMERA' })
      return
    }
    setBusy(true)
    try { await retryRef.current() }
    catch (error) { dispatch({ type: 'ERROR', message: errorMessage(error) }) }
    finally { setBusy(false) }
  }, [busy])

  const goHome = useCallback(() => {
   // 요청 진행 중에 홈으로 가면 늦게 온 응답이 화면을 덮어쓸 수 있어 막는다
    if (busy) return
    restart()
    window.scrollTo({ top: 0 })
  }, [busy, restart])

  return (
    <div className="app-shell" id="top">
      <BrandHeader demoMode={state.demoMode} onHome={goHome} gu={state.screen === 'REGION' ? undefined : state.gu} />
      <main className="page-main">
        <div className="page-intro">
          <div><span className="intro-kicker">SMART RECYCLING GUIDE</span><h2>지금 이 상태, 어떻게 버려야 할까요?</h2><p>사진 한 장으로 쓰레기의 상태를 분석하고 부산광역시 기준 배출 방법을 안내합니다.</p></div>
          <span className="intro-location"><span className="pin-dot" /> 부산광역시</span>
        </div>
        <div className="workspace-card">
          <ProgressSteps screen={state.screen} />
          <div className="workspace-inner">
            {state.screen === 'REGION' && <RegionScreen gu={state.gu} onChange={(gu) => dispatch({ type: 'SET_GU', gu })} onNext={() => dispatch({ type: 'SCREEN', screen: 'CAMERA' })} />}
            {state.screen === 'CAMERA' && <CameraScreen previewUrl={state.previewUrl} loading={busy} error={null} isReshoot={state.attempt === 2} onFile={(file) => void setFile(file)} onAnalyze={() => void handleAnalyze()} onBack={() => dispatch({ type: 'SCREEN', screen: 'REGION' })} onClear={clearImage} />}
            {state.screen === 'OBSERVING' && <ObservingScreen previewUrl={state.previewUrl} />}
            {state.screen === 'QUESTION' && state.decision && <QuestionScreen decision={state.decision} answer={state.answer} onAnswer={(answer) => dispatch({ type: 'SET_ANSWER', answer })} onSubmit={() => void handleQuestionSubmit()} loading={busy} />}
            {state.screen === 'RULE_LOOKUP' && <RuleLookupScreen gu={state.gu} />}
            {state.screen === 'WASH_GUIDE' && state.decision && <WashGuideScreen decision={state.decision} onRetake={handleRetake} />}
            {state.screen === 'RESULT' && state.decision && <ResultScreen decision={state.decision} demoMode={state.demoMode} onRestart={restart} />}
            {state.screen === 'MULTI_RESULT' && <MultiResultScreen items={state.multiItems} previewUrl={state.previewUrl} demoMode={state.demoMode} onAnswer={(index, answer) => void answerItem(index, answer)} onRetakeItem={handleRetake} onRestart={restart} />}
            {state.screen === 'NOTICE_RESHOOT' && <ReshootNoticeScreen reason={state.reshootReason} canRetake={state.attempt === 1} onRetake={handleNoticeRetake} onRestart={restart} />}
            {state.screen === 'NOTICE_UNKNOWN' && <UnknownNoticeScreen onRestart={restart} />}
            {state.screen === 'ERROR' && <ErrorScreen message={state.errorMessage} onRetry={() => void retry()} onRestart={restart} />}
          </div>
        </div>
        <div className="below-note"><span className="info-circle">i</span><p>AI는 사진에서 보이는 상태를 관찰하고, 최종 배출 판단은 부산 기준 규칙 엔진이 수행합니다.</p></div>
      </main>
      <Disclaimer />
    </div>
  )
}
