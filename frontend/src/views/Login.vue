<template>
  <div class="bg-[#0f1115] text-[#e6e1e5] min-h-screen flex flex-col items-center justify-center p-6 antialiased font-sans">
    <main class="w-full max-w-md flex flex-col h-full animate-in fade-in duration-700">
      
      <div class="shrink-0 mt-8 mb-12 text-center flex flex-col items-center">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-[#1d1b20] mb-4 shadow-lg ring-1 ring-white/5 border border-[#22c55e]/20">
          <Bolt class="text-[#22c55e]" :size="40" fill="currentColor" />
        </div>
        <h1 class="text-2xl font-bold mb-2 tracking-tight">智动AI教练</h1>
        <p class="text-sm text-[#cac4d0]">精准训练，即刻开启</p>
      </div>

      <div class="flex mb-8 border-b border-[#49454f] relative">
        <button
          @click="isLogin = true; form.password = ''"
          :class="['flex-1 pb-3 text-lg font-bold relative transition-colors z-10', isLogin ? 'text-[#22c55e]' : 'text-[#cac4d0] hover:text-white']"
        >
          登录
        </button>
        <button
          @click="isLogin = false; form.password = ''"
          :class="['flex-1 pb-3 text-lg font-bold relative transition-colors z-10', !isLogin ? 'text-[#22c55e]' : 'text-[#cac4d0] hover:text-white']"
        >
          注册
        </button>
        <div 
          class="absolute -bottom-px left-0 w-1/2 h-0.75 bg-[#22c55e] transition-transform duration-300 ease-in-out"
          :style="{ transform: isLogin ? 'translateX(0)' : 'translateX(100%)' }"
        ></div>
      </div>

      <form @submit.prevent="handleSubmit" class="flex-1 flex flex-col gap-4">
        
        <div class="bg-[#1d1b20] rounded-xl px-4 py-3 ring-1 ring-transparent focus-within:ring-[#22c55e] focus-within:bg-[#2b2930] transition-all">
          <label class="block text-[10px] text-[#cac4d0] mb-1 uppercase tracking-wider font-bold">手机号/用户名</label>
          <div class="flex items-center">
            <User :size="20" class="text-[#cac4d0] mr-3" />
            <input
              v-model="form.username"
              required
              class="w-full bg-transparent border-none p-0 text-base font-medium focus:ring-0 outline-none text-[#e6e1e5] placeholder-[#cac4d0]/50"
              placeholder="请输入您的账号"
              type="text"
            />
          </div>
        </div>

        <Transition name="expand">
          <div v-if="!isLogin" class="overflow-hidden">
            <div class="bg-[#1d1b20] rounded-xl px-4 py-3 ring-1 ring-transparent focus-within:ring-[#22c55e] focus-within:bg-[#2b2930] transition-all">
              <label class="block text-[10px] text-[#cac4d0] mb-1 uppercase tracking-wider font-bold">电子邮箱</label>
              <div class="flex items-center">
                <Mail :size="20" class="text-[#cac4d0] mr-3" />
                <input
                  v-model="form.email"
                  class="w-full bg-transparent border-none p-0 text-base font-medium focus:ring-0 outline-none text-[#e6e1e5] placeholder-[#cac4d0]/50"
                  placeholder="请输入电子邮箱 (选填)"
                  type="email"
                />
              </div>
            </div>
          </div>
        </Transition>

        <div>
          <div class="bg-[#1d1b20] rounded-xl px-4 py-3 ring-1 ring-transparent focus-within:ring-[#22c55e] focus-within:bg-[#2b2930] transition-all relative">
            <label class="block text-[10px] text-[#cac4d0] mb-1 uppercase tracking-wider font-bold">密码</label>
            <div class="flex items-center">
              <Lock :size="20" class="text-[#cac4d0] mr-3" />
              <input
                v-model="form.password"
                required
                class="w-full bg-transparent border-none p-0 text-base font-medium focus:ring-0 outline-none pr-10 text-[#e6e1e5] placeholder-[#cac4d0]/50"
                placeholder="请输入密码"
                :type="showPassword ? 'text' : 'password'"
              />
            </div>
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-4 top-1/2 -translate-y-1/2 mt-2 text-[#cac4d0] hover:text-white"
            >
              <component :is="showPassword ? EyeOff : Eye" :size="18" />
            </button>
          </div>
          
          <Transition name="expand">
            <p v-if="!isLogin && form.password && !isPasswordFormatValid" class="text-red-500 text-xs mt-2 pl-2">
              ⚠️ 密码必须包含至少 8 位，且同时包含字母和数字
            </p>
          </Transition>
        </div>

        <div v-if="isLogin" class="flex justify-end">
          <button type="button" class="text-sm font-bold text-[#22c55e] hover:opacity-80 transition-colors">忘记密码？</button>
        </div>

        <div class="mt-8 flex flex-col gap-4">
          <button
            type="submit"
            :disabled="isLoading || !isFormValid"
            class="w-full h-14 bg-[#22c55e] text-white rounded-xl font-bold text-lg flex items-center justify-center transition-all hover:brightness-110 active:scale-[0.98] shadow-lg shadow-[#22c55e]/20 disabled:opacity-50 disabled:grayscale disabled:scale-100"
          >
            <span v-if="isLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></span>
            {{ isLogin ? '登录' : '注册并登录' }}
          </button>
          <button
            type="button"
            @click="isLogin = !isLogin; form.password = ''"
            class="w-full h-14 bg-transparent text-[#22c55e] border border-[#2b2930] rounded-xl font-bold text-lg flex items-center justify-center transition-all hover:bg-[#22c55e]/10 active:scale-[0.98]"
          >
            {{ isLogin ? '创建新账号' : '已有账号？登录' }}
          </button>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';
import { showToast, showFailToast } from 'vant';
import { Bolt, User, Lock, Eye, EyeOff, Mail } from 'lucide-vue-next';

const router = useRouter();
const authStore = useAuthStore();

const isLogin = ref(true);
const showPassword = ref(false);
const isLoading = ref(false);

const form = reactive({
  username: '',
  password: '',
  email: ''
});

// --- 新增：密码正则校验逻辑 ---
// 至少8个字符，包含至少一个字母和一个数字
const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;

const isPasswordFormatValid = computed(() => {
  return passwordRegex.test(form.password);
});

// 动态判断表单是否可以提交
const isFormValid = computed(() => {
  if (isLogin.value) {
    // 登录模式：只要账号密码填了就行
    return form.username.length > 0 && form.password.length > 0;
  } else {
    // 注册模式：必须满足账号不为空，且密码符合正则校验
    return form.username.length > 0 && isPasswordFormatValid.value;
  }
});
// -----------------------------

const handleSubmit = async () => {
  // 如果不满足校验条件（比如绕过了按钮禁用），直接拦截
  if (!isFormValid.value) return;

  isLoading.value = true;
  try {
    // 1. 注册逻辑
    if (!isLogin.value) {
      await axios.post('/api/register', { 
        username: form.username, 
        password: form.password, 
        email: form.email 
      });
      showToast('注册成功');
    }
    
    // 2. 登录逻辑
    const formData = new URLSearchParams();
    formData.append('username', form.username);
    formData.append('password', form.password);
    
    const res = await axios.post('/api/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    
    authStore.setToken(res.data.access_token);
    router.push('/');
  } catch (error) {
    showFailToast(error.response?.data?.detail || '操作失败');
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.expand-enter-active, .expand-leave-active { transition: all 0.3s ease-in-out; max-height: 100px; opacity: 1; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; transform: translateY(-10px); }

@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700;900&display=swap');
.font-sans { font-family: 'Lexend', sans-serif; }
</style>