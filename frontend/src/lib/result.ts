import type { Decision } from './api'

// 재활용 불가(빨강) 결과. 나머지 결과 코드는 재활용 대상(초록)
const NOT_RECYCLABLE = new Set<Decision['result_code']>(['GENERAL', 'NONCOMBUSTIBLE'])

export function isNotRecyclable(decision: Decision): boolean {
  return NOT_RECYCLABLE.has(decision.result_code)
}
