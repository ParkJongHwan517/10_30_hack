import type { components } from './api-types'

export type Observation = components['schemas']['Observation']
export type ObserveResponse = components['schemas']['ObserveResponse']
export type Decision = components['schemas']['Decision']
export type Region = components['schemas']['Region']
export type Answers = components['schemas']['Answers']
export type DecideRequest = components['schemas']['DecideRequest']

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  code: string
  status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let code = 'REQUEST_FAILED'
    let message = '요청을 처리하지 못했습니다.'

    try {
      const body: unknown = await response.json()
      if (body && typeof body === 'object') {
        const payload = body as { code?: unknown; message?: unknown; detail?: unknown }
        if (typeof payload.code === 'string') code = payload.code
        if (typeof payload.message === 'string') message = payload.message
        else if (typeof payload.detail === 'string') message = payload.detail
      }
    } catch {
      // 서버가 JSON이 아닌 오류를 반환해도 빈 화면이 되지 않도록 기본 문구를 유지한다.
    }

    throw new ApiError(message, code, response.status)
  }

  return (await response.json()) as T
}

export async function observeImage(image: Blob, isReshoot: boolean): Promise<ObserveResponse> {
  const form = new FormData()
  form.append('image', image, 'waste.jpg')
  form.append('is_reshoot', String(isReshoot))

  const response = await fetch(`${API_BASE}/api/observe`, {
    method: 'POST',
    body: form,
  })
  return readResponse<ObserveResponse>(response)
}

export async function decideWaste(payload: DecideRequest): Promise<Decision> {
  const response = await fetch(`${API_BASE}/api/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return readResponse<Decision>(response)
}
