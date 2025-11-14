import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1000, // 청크 크기 경고 제한을 1000KB로 증가
    rollupOptions: {
      output: {
        manualChunks: {
          // React 라이브러리들을 별도 청크로 분리
          'react-vendor': ['react', 'react-dom'],
          'router': ['react-router-dom'],
          // 차트 라이브러리 (큰 라이브러리)
          'charts': ['recharts'],
          // 날짜 관련 라이브러리
          'date': ['date-fns', 'react-datepicker'],
          // HTTP 클라이언트
          'axios': ['axios'],
          // 아이콘
          'icons': ['lucide-react'],
        },
      },
    },
  },
})
