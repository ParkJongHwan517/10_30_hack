const MAX_EDGE = 1280
const MAX_BYTES = 3 * 1024 * 1024

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
 * 업로드 전에 긴 변을 1280px로 줄이고 JPEG로 다시 인코딩한다.
 * Canvas 재인코딩으로 EXIF 메타데이터를 제거하며, 원본 파일은 저장하지 않는다.
 */
export async function resizeImage(file: File): Promise<Blob> {
  if (!file.type.startsWith('image/')) {
    throw new Error('이미지 파일만 업로드할 수 있습니다.')
  }

  const image = await loadImage(file)
  const scale = Math.min(1, MAX_EDGE / Math.max(image.naturalWidth, image.naturalHeight))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale))
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale))

  const context = canvas.getContext('2d')
  if (!context) throw new Error('사진을 처리할 수 없습니다.')
  context.drawImage(image, 0, 0, canvas.width, canvas.height)

  let quality = 0.88
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
