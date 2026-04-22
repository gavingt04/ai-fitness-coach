import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// --- 【核心修复：激活 Tailwind 样式】 ---
// 这一行告诉 Vite 去加载并编译 src/assets/main.css 里的 Tailwind 指令
import './assets/main.css' 

// --- 【Vant 视觉组件库与样式】 ---
// 由于你的 axios 拦截器中使用了 Vant 的 showToast，我们保留 Vant 的注册
import Vant, { showToast } from 'vant'
import 'vant/lib/index.css'

import { useAuthStore } from './stores/auth'

const app = createApp(App)

// 1. 初始化并注册 Pinia (必须在 router 之前，方便拦截器调用 store)
const pinia = createPinia()
app.use(pinia)

// 2. 注册路由
app.use(router)

// 3. 注册 Vant 组件库
app.use(Vant) 

// --- 【Axios 拦截器：全局状态保安】 ---
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 处理 401 认证失效
    if (error.response && error.response.status === 401) {
      showToast('登录已过期，请重新登录');
      const authStore = useAuthStore();
      authStore.logout(); 
      router.push('/'); // 认证失败强制跳转回登录页
    }
    return Promise.reject(error);
  }
);
// --------------------------------

// 4. 挂载应用
app.mount('#app')