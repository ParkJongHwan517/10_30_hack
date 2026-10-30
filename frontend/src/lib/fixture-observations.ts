import cardboardTapeRaw from '../../../backend/tests/fixtures/cardboard_tape.json?raw'
import petClearLabelRaw from '../../../backend/tests/fixtures/pet_clear_label.json?raw'
import plasticPpCleanRaw from '../../../backend/tests/fixtures/plastic_pp_clean.json?raw'
import styrofoamCleanRaw from '../../../backend/tests/fixtures/styrofoam_clean.json?raw'
import styrofoamSauceRaw from '../../../backend/tests/fixtures/styrofoam_sauce.json?raw'
import type { components } from './api-types'
import type { ObserveResponse } from './api'

// 로컬 UI/통합 테스트 전용: 실제 API가 준비되기 전에는 backend/tests/fixtures 원본을 그대로 사용한다.
// fixture mode는 개발 서버에서만 ?fixture=<파일명>으로 명시적으로 활성화한다.
type Observation = components['schemas']['Observation']

const fixtureSources: Record<string, string> = {
  cardboard_tape: cardboardTapeRaw,
  pet_clear_label: petClearLabelRaw,
  plastic_pp_clean: plasticPpCleanRaw,
  styrofoam_clean: styrofoamCleanRaw,
  styrofoam_sauce: styrofoamSauceRaw,
}

function parseObservation(source: string): Observation {
  return JSON.parse(source) as Observation
}

export function getFixtureObserveResponse(isReshoot: boolean): ObserveResponse | null {
  if (!import.meta.env.DEV) return null
  const fixtureName = new URLSearchParams(window.location.search).get('fixture')
  if (!fixtureName) return null

  const selectedName = fixtureName === 'styrofoam_sauce' && isReshoot ? 'styrofoam_clean' : fixtureName
  const source = fixtureSources[selectedName]
  if (!source) return null

  return {
    observation: parseObservation(source),
    ok: true,
    demo_mode: true,
  }
}
