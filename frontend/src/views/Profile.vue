<template>
  <div class="p-4 md:p-6 space-y-6 bg-[#0f1115] min-h-screen text-[#e6e1e5] font-sans antialiased">
    
    <section class="bg-[#1d1b20] p-6 rounded-2xl border border-[#2b2930] flex items-center gap-4 shadow-sm">
      <div class="w-20 h-20 rounded-full overflow-hidden shrink-0 border-2 border-[#22c55e]/30 shadow-lg">
        <img 
          alt="User Avatar" 
          class="w-full h-full object-cover" 
          src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&q=80&w=200" 
        />
      </div>
      <div class="flex-1 space-y-1">
        <div class="flex items-center gap-2">
          <template v-if="isEditingNickname">
            <input 
              v-model="tempUsername"
              autoFocus
              class="bg-transparent border-b border-[#22c55e] text-xl font-bold text-[#e6e1e5] focus:outline-none w-full"
              @blur="saveProfile('username')"
              @keyup.enter="saveProfile('username')"
            />
          </template>
          <template v-else>
            <h1 class="text-xl font-bold text-[#e6e1e5]">{{ username }}</h1>
          </template>
          <button 
            @click="isEditingNickname = !isEditingNickname; tempUsername = username"
            class="text-[#22c55e] hover:opacity-80 p-1"
          >
            <Check v-if="isEditingNickname" :size="16" />
            <Edit3 v-else :size="16" />
          </button>
        </div>
        <p class="text-xs text-[#cac4d0] font-lexend">ID: {{ userId }}</p>
      </div>
    </section>

    <section class="bg-[#1d1b20] rounded-2xl border border-[#2b2930] overflow-hidden shadow-sm">
      <h2 class="text-[10px] text-[#cac4d0] px-4 py-3 bg-[#2b2930]/50 uppercase tracking-widest font-bold">资料与安全设置</h2>
      
      <div class="divide-y divide-[#2b2930]">
        
        <div class="group relative">
          <button 
            @click="isEditingWeight = !isEditingWeight; tempWeight = weight"
            class="w-full flex items-center justify-between px-4 py-4 hover:bg-[#2b2930]/50 transition-colors text-left"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-[#2b2930] flex items-center justify-center text-[#cac4d0]">
                <Scale :size="18" />
              </div>
              <span class="font-medium text-sm text-[#e6e1e5]">当前体重</span>
            </div>
            <div class="flex items-center text-[#22c55e]">
              <span class="text-xs mr-2 font-bold">{{ weight }} kg</span>
              <ChevronRight :size="18" :class="['transition-transform', isEditingWeight && 'rotate-90']" />
            </div>
          </button>
          
          <Transition name="slide-down">
            <div v-if="isEditingWeight" class="px-4 pb-4">
              <div class="flex gap-2">
                <input 
                  v-model="tempWeight"
                  type="number"
                  class="flex-1 bg-[#0f1115] border border-[#2b2930] rounded-lg px-3 py-2 text-sm text-[#e6e1e5] focus:outline-none focus:border-[#22c55e]"
                />
                <button 
                  @click="saveProfile('weight')"
                  class="bg-[#22c55e] text-white px-4 py-2 rounded-lg text-sm font-bold shadow-lg shadow-[#22c55e]/20"
                >
                  保存
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <div class="group relative">
          <button 
            @click="isEditingEmail = !isEditingEmail; tempEmail = email"
            class="w-full flex items-center justify-between px-4 py-4 hover:bg-[#2b2930]/50 transition-colors text-left"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-[#2b2930] flex items-center justify-center text-[#cac4d0]">
                <Mail :size="18" />
              </div>
              <span class="font-medium text-sm text-[#e6e1e5]">绑定邮箱</span>
            </div>
            <div class="flex items-center text-[#cac4d0]">
              <span class="text-xs mr-2">{{ email || '未绑定' }}</span>
              <ChevronRight :size="18" :class="['transition-transform', isEditingEmail && 'rotate-90']" />
            </div>
          </button>
          
          <Transition name="slide-down">
            <div v-if="isEditingEmail" class="px-4 pb-4">
              <div class="flex gap-2">
                <input 
                  v-model="tempEmail"
                  type="email"
                  placeholder="输入邮箱地址"
                  class="flex-1 bg-[#0f1115] border border-[#2b2930] rounded-lg px-3 py-2 text-sm text-[#e6e1e5] focus:outline-none focus:border-[#22c55e]"
                />
                <button 
                  @click="saveProfile('email')"
                  class="bg-[#22c55e] text-white px-4 py-2 rounded-lg text-sm font-bold shadow-lg shadow-[#22c55e]/20"
                >
                  保存
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <button 
          @click="router.push('/profile/change-password')"
          class="w-full flex items-center justify-between px-4 py-4 hover:bg-[#2b2930]/50 transition-colors text-left"
        >
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-[#2b2930] flex items-center justify-center text-[#cac4d0]">
              <Lock :size="18" />
            </div>
            <span class="font-medium text-sm text-[#e6e1e5]">修改密码</span>
          </div>
          <div class="flex items-center text-[#cac4d0]">
            <ChevronRight :size="18" />
          </div>
        </button>

      </div>
    </section>

    <div class="pt-4 pb-8">
      <button 
        @click="handleLogout"
        class="w-full h-12 bg-[#1d1b20] border border-red-500/30 text-red-500 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-red-500/10 active:scale-[0.98] transition-all"
      >
        <LogOut :size="20" />
        退出登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showSuccessToast, showFailToast } from 'vant';
import { ChevronRight, LogOut, User, Lock, Mail, Edit3, Check, Scale } from 'lucide-vue-next';
import axios from 'axios';

const router = useRouter();
const authStore = useAuthStore();

// 显示的数据
const username = ref('');
const email = ref('');
const weight = ref(70);
const userId = ref('');

// 编辑态绑定的临时数据
const tempUsername = ref('');
const tempEmail = ref('');
const tempWeight = ref(70);

// 展开/收起状态
const isEditingNickname = ref(false);
const isEditingEmail = ref(false);
const isEditingWeight = ref(false);

// 初始化获取数据
onMounted(async () => {
  try {
    const res = await axios.get('/api/users/me', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    userId.value = String(res.data.id).padStart(6, '0');
    username.value = res.data.username;
    email.value = res.data.email;
    weight.value = res.data.weight;
  } catch (e) {
    console.error("加载信息失败", e);
  }
});

// 通用的保存函数，自动同步到数据库
const saveProfile = async (field) => {
  let payload = {};
  
  if (field === 'username') {
    if (!tempUsername.value) return showFailToast('昵称不能为空');
    payload.username = tempUsername.value;
  } else if (field === 'email') {
    payload.email = tempEmail.value;
  } else if (field === 'weight') {
    payload.weight = parseFloat(tempWeight.value);
  }

  try {
    await axios.put('/api/users/me', payload, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    
    // 成功后更新显示的数据并关闭输入框
    if (field === 'username') {
      username.value = tempUsername.value;
      isEditingNickname.value = false;
      showSuccessToast('昵称修改成功\n若登录失效请重新登录');
    } else if (field === 'email') {
      email.value = tempEmail.value;
      isEditingEmail.value = false;
      showSuccessToast('邮箱绑定成功');
    } else if (field === 'weight') {
      weight.value = tempWeight.value;
      isEditingWeight.value = false;
      showSuccessToast('体重更新成功');
    }
  } catch (error) {
    showFailToast(error.response?.data?.detail || '更新失败');
    // 如果失败了，恢复编辑状态不改变原值
  }
};

const handleLogout = () => {
  authStore.logout?.();
  localStorage.clear();
  showSuccessToast('已成功退出');
  router.replace('/login');
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700;900&display=swap');
.font-sans { font-family: 'Lexend', sans-serif; }

.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease-out; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-10px); }
</style>