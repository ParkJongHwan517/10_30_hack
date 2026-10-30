const MAX_EDGE = 1280
const MAX_BYTES = 3 * 1024 * 1024
const START_QUALITY = 0.8

// TODO(front): 임시 문구 — PROJECT_SPEC §12 문구가 있으면 교체
const HEIC_MESSAGE = '이 사진 형식(HEIC)은 읽을 수 없습니다. 카메라로 직접 촬영하거나 JPG 사진을 선택해주세요.'

function isHeic(file: File): boolean {
  return /image\/hei[cf]/i.test(file.type) || /\.hei[cf]$/i.test(file.name)
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(url)
      resolve(image)
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('사진을 읽을 수 없습니다. 다른 사진을 선택해주세요.'))
    }
    image.src = url
  })
}

function canvasToJpeg(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('사진을 변환하지 못했습니다.'))),
      'image/jpeg',
      quality,
    )
  })
}

/**
 * 업로드 전에 긴 변을 1280px로 줄이고 JPEG(품질 0.8)로 다시 인코딩한다.
 * Canvas 재인코딩으로 EXIF 메타데이터를 제거하며, 원본 파일은 저장하지 않는다.
 */
export async function resizeImage(file: File): Promise<Blob> {
  // HEIC는 브라우저가 type을 비워 보내는 경우가 있어 먼저 걸러내지 않고 디코딩을 시도한다
  if (!file.type.startsWith('image/') && !isHeic(file)) {
    throw new Error('이미지 파일만 업로드할 수 있습니다.')
  }

  let image: HTMLImageElement
  try {
    image = await loadImage(file)
  } catch (error) {
    if (isHeic(file)) throw new Error(HEIC_MESSAGE)
    throw error
  }

  const scale = Math.min(1, MAX_EDGE / Math.max(image.naturalWidth, image.naturalHeight))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale))
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale))

  const context = canvas.getContext('2d')
  if (!context) throw new Error('사진을 처리할 수 없습니다.')
  // PNG 투명 배경은 JPEG 변환 시 검은색이 되므로 흰색으로 먼저 채운다
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  context.drawImage(image, 0, 0, canvas.width, canvas.height)

  let quality = START_QUALITY
  let blob = await canvasToJpeg(canvas, quality)
  while (blob.size > MAX_BYTES && quality > 0.5) {
    quality -= 0.1
    blob = await canvasToJpeg(canvas, quality)
  }
  if (blob.size > MAX_BYTES) {
    throw new Error('사진 용량이 너무 큽니다. 다른 사진을 선택해주세요.')
  }
  return blob
}