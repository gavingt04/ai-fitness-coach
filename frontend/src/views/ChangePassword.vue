<template>
  <div class="min-h-screen bg-[#0f1115] text-[#e6e1e5] p-4 md:p-6 max-w-md mx-auto font-sans antialiased">
    <template v-if="isSuccess">
      <div class="min-h-[80vh] flex flex-col items-center justify-center text-center animate-in zoom-in duration-300">
        <div class="bg-[#1d1b20] p-8 rounded-3xl border border-[#22c55e]/20 shadow-xl flex flex-col items-center gap-4">
          <div class="w-16 h-16 bg-[#22c55e]/10 rounded-full flex items-center justify-center text-[#22c55e] mb-2">
            <CheckCircle2 :size="40" />
          </div>
          <h1 class="text-2xl font-bold text-[#e6e1e5]">密码修改成功</h1>
          <p class="text-[#cac4d0] text-sm">正在为您跳转回个人中心...</p>
        </div>
      </div>
    </template>

    <template v-else>
      <header class="flex items-center gap-4 mb-8 pt-2">
        <button 
          @click="router.back()"
          class="w-10 h-10 rounded-full bg-[#1d1b20] flex items-center justify-center text-[#e6e1e5] hover:bg-[#2b2930] transition-colors"
        >
          <ArrowLeft :size="20" />
        </button>
        <h1 class="text-xl font-bold">修改密码</h1>
      </header>

      <form @submit.prevent="handleSubmit" class="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
        <div class="space-y-4">
          <div class="bg-[#1d1b20] rounded-2xl px-4 py-3 ring-1 ring-transparent focus-within:ring-[#22c55e] focus-within:bg-[#2b2930] transition-all relative">
            <label class="block text-[10px] text-[#cac4d0] mb-1 uppercase tracking-wider font-medium">当前密码</label>
            <div class="flex items-center">
              <Lock :size="20" class="text-[#cac4d0] mr-3" />
              <input
                v-model="oldPassword"
                required
                class="w-full bg-transparent border-none p-0 text-base text-[#e6e1e5] placeholder-[#cac4d0]/40 focus:ring-0 outline-none pr-10"
                placeholder="请输入当前密码"
                :type="showOld ? 'text' : 'password'"
              />
            </div>
            <button type="button" @click="showOld = !showOld" class="absolute right-4 top-1/2 -translate-y-1/2 mt-2 text-[#cac4d0]">
              <component :is="showOld ? EyeOff : Eye" :size="18" />
            </button>
          </div>

          <div class="bg-[#1d1b20] rounded-2xl px-4 py-3 ring-1 ring-transparent focus-within:ring-[#22c55e] focus-within:bg-[#2b2930] transition-all relative">
            <label class="block text-[10px] text-[#cac4d0] mb-1 uppercase tracking-wider font-medium">新密码</label>
            <div class="flex items-center">
              <Lock :size="20" class="text-[#cac4d0] mr-3" />
              <input
                v-model="newPassword"
                required
                class="w-full bg-transparent border-none p-0 text-base text-[#e6e1e5] placeholder-[#cac4d0]/40 focus:ring-0 outline-none pr-10"
                placeholder="请输入新密码"
                :type="showNew ? 'text' : 'password'"
              />
            </div>
            <button type="button" @click="showNew = !showNew" class="absolute right-4 top-1/2 -translate-y-1/2 mt-2 text-[#cac4d0]">
              <component :is="showNew ? EyeOff : Eye" :size="18" />
            </button>
          </div>

          <div class="bg-[#1d1b20] rounded-2xl px-4 py-3 ring-1 ring-transparent focus-within:ring-[#22c55e] focus-within:bg-[#2b2930] transition-all">
            <label class="block text-[10px] text-[#cac4d0] mb-1 uppercase tracking-wider font-medium">确认新密码</label>
            <div class="flex items-center">
              <Lock :size="20" class="text-[#cac4d0] mr-3" />
              <input
                v-model="confirmPassword"
                required
                class="w-full bg-transparent border-none p-0 text-base text-[#e6e1e5] placeholder-[#cac4d0]/40 focus:ring-0 outline-none"
                placeholder="请再次输入新密码"
                type="password"
              />
            </div>
          </div>
        </div>

        <div class="pt-4">
          <button
            type="submit"
            :disabled="!isValid || isPending"
            class="w-full h-14 bg-[#22c55e] text-white rounded-2xl font-bold text-lg flex items-center justify-center transition-all hover:brightness-110 active:scale-[0.98] shadow-lg shadow-[#22c55e]/20 disabled:opacity-50 disabled:grayscale disabled:scale-100"
          >
            <span v-if="isPending" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></span>
            {{ isPending ? '保存中...' : '保存新密码' }}
          </button>
          <p v-if="newPassword && confirmPassword && newPassword !== confirmPassword" class="text-red-500 text-center text-xs mt-3">
            两次输入的新密码不一致
          </p>
        </div>

        <div class="bg-[#1a1c22] p-4 rounded-2xl border border-white/5">
          <h3 class="text-xs font-bold text-[#cac4d0] mb-2 uppercase tracking-widest">安全提示</h3>
          <ul class="text-[10px] text-[#cac4d0] space-y-1 ml-4 list-disc">
            <li>请使用至少 8 位包含字母和数字的组合。</li>
            <li>不要在多个网站使用相同的密码。</li>
            <li>修改后所有已登录设备可能需要重新登录。</li>
          </ul>
        </div>
      </form>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
// 重点修复：导入缺失的库和状态仓库
import { useAuthStore } from '../stores/auth';
import axios from 'axios';
import { showFailToast } from 'vant';
import { ArrowLeft, Lock, Eye, EyeOff, CheckCircle2 } from 'lucide-vue-next';

const router = useRouter();
const authStore = useAuthStore(); // 重点修复：实例化 store

const oldPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const showOld = ref(false);
const showNew = ref(false);
const isSuccess = ref(false);
const isPending = ref(false); // 重点修复：定义 isPending

const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;

const isPasswordFormatValid = computed(() => {
  return passwordRegex.test(newPassword.value);
});

// 按钮是否可点击的最终判断
const isValid = computed(() => {
  return oldPassword.value && 
         isPasswordFormatValid.value && 
         newPassword.value === confirmPassword.value;
});

const handleSubmit = async () => {
  if (!isValid.value) return;
  
  isPending.value = true;
  try {
    await axios.put('/api/users/password', {
      old_password: oldPassword.value,
      new_password: newPassword.value
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    
    isSuccess.value = true;
    setTimeout(() => {
      router.push('/profile');
    }, 2000);
  } catch (error) {
    showFailToast(error.response?.data?.detail || '密码修改失败');
  } finally {
    isPending.value = false;
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700;900&display=swap');
.font-sans { font-family: 'Lexend', sans-serif; }
</style>