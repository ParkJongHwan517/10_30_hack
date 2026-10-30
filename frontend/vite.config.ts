import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // 로컬 개발: /api 요청을 FastAPI(uvicorn :8000)로 넘긴다. 배포(Vercel)에서는 같은 도메인이라 불필요
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
