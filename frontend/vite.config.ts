import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl' // 【新增】引入 HTTPS 插件
import tailwindcss from '@tailwindcss/vite' // 【新增】引入 Tailwind v4 插件

export default defineConfig({
  plugins: [
    vue(),
    basicSsl(), // 【新增】启用本地 HTTPS
    tailwindcss() // 【新增】将 Tailwind 注入编译流程
  ],
  server: {
    host: '0.0.0.0', // 【关键】允许局域网内的手机访问
    port: 5173,
    proxy: {
      // 1. 代理普通接口 (登录、获取历史等)
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') 
        // 注意：如果你后端的路由没有加 /api 前缀，这行 rewrite 是必须的
      },
      // 2. 代理 WebSocket (AI 视频流)
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true // 【关键】开启 WebSocket 代理
      }
    }
  }
})