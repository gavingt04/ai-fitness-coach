<template>
  <div class="p-4 md:p-6 space-y-6 bg-[#0f1115] min-h-screen text-[#e6e1e5] font-sans antialiased">
    
    <section 
      class="relative rounded-3xl overflow-hidden bg-[#1d1b20] border border-white/5 p-6 shadow-2xl min-h-40 flex flex-col justify-center animate-in fade-in slide-in-from-top-4 duration-700"
    >
      <div 
        class="absolute inset-0 z-0 opacity-10 bg-cover bg-center" 
        style="background-image: url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&q=80&w=1000')"
      ></div>
      
      <div class="relative z-10 space-y-1">
        <h1 class="text-2xl font-bold text-white">欢迎回来, {{ username }}!</h1>
        <p class="text-xl font-black text-[#22c55e] tracking-tight">今日训练引擎已就绪</p>
      </div>
    </section>

    <section class="grid grid-cols-2 gap-4">
      
      <button 
        @click="router.push('/workout')" 
        class="col-span-2 relative overflow-hidden bg-[#22c55e] text-white rounded-3xl p-6 flex items-center justify-between shadow-lg shadow-[#22c55e]/20 active:scale-[0.98] transition-all group"
      >
        <div class="space-y-1 text-left relative z-10">
          <span class="text-xl font-black block uppercase tracking-tighter">开始新训练</span>
          <span class="text-white/80 text-xs font-bold tracking-widest">START SESSION</span>
        </div>
        <div class="relative z-10 bg-black/10 p-3 rounded-2xl backdrop-blur-md group-hover:scale-110 transition-transform">
          <PlayCircle :size="32" fill="currentColor" />
        </div>
        <div class="absolute -right-4 -top-4 w-24 h-24 bg-white/20 rounded-full blur-2xl"></div>
      </button>

      <button 
        @click="router.push('/plan')" 
        class="bg-[#1d1b20] rounded-3xl border border-white/5 p-6 flex flex-col items-center justify-center gap-3 hover:bg-[#2b2930] transition-all active:scale-95"
      >
        <div class="w-12 h-12 rounded-2xl bg-[#2b2930] flex items-center justify-center">
          <Sparkles :size="28" class="text-[#22c55e]" />
        </div>
        <span class="text-sm font-bold">计划生成</span>
      </button>

      <button 
        @click="router.push('/history')" 
        class="bg-[#1d1b20] rounded-3xl border border-white/5 p-6 flex flex-col items-center justify-center gap-3 hover:bg-[#2b2930] transition-all active:scale-95"
      >
        <div class="w-12 h-12 rounded-2xl bg-[#2b2930] flex items-center justify-center">
          <Activity :size="28" class="text-[#cac4d0]" />
        </div>
        <span class="text-sm font-bold">数据概览</span>
      </button>
    </section>

    <button 
      @click="handleLogout" 
      class="w-full py-4 bg-[#1d1b20] border border-red-500/10 rounded-2xl text-[#cac4d0] text-sm font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-all hover:text-red-400 hover:bg-red-500/5"
    >
      <LogOut :size="18" />
      断开系统连接
    </button>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showSuccessToast } from 'vant';
import axios from 'axios';
import { 
  PlayCircle, 
  Sparkles, 
  Activity, 
  LogOut 
} from 'lucide-vue-next';

const router = useRouter();
const authStore = useAuthStore();

// 定义动态用户名，默认给个 fallback 防止闪烁
const username = ref('训练者');

// 页面加载时请求用户信息
onMounted(async () => {
  try {
    const res = await axios.get('/api/users/me', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    // 获取成功后替换动态名称
    if (res.data && res.data.username) {
      username.value = res.data.username;
    }
  } catch (error) {
    console.error("加载用户信息失败:", error);
    // 如果 token 失效，可以在这里直接让用户跳回登录页
    // router.replace('/login');
  }
});

/**
 * 登出逻辑
 */
const handleLogout = () => {
  if (typeof authStore.logout === 'function') {
    authStore.logout();
  }
  localStorage.clear();
  sessionStorage.clear();
  
  showSuccessToast('系统已断开');
  router.replace('/login');
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700;900&display=swap');

.font-sans {
  font-family: 'Lexend', system-ui, -apple-system, sans-serif;
}

.animate-in {
  animation-duration: 0.7s;
  animation-fill-mode: both;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInFromTop {
  from { transform: translateY(-1rem); }
  to { transform: translateY(0); }
}

.fade-in { animation-name: fadeIn; }
.slide-in-from-top-4 { animation-name: slideInFromTop; }
</style>