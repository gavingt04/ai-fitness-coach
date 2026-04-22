<template>
  <div class="min-h-screen flex flex-col bg-[#0f1115] text-[#e6e1e5] font-sans">
    <header v-if="!hideNav" class="fixed top-0 w-full z-50 bg-[#0f1115]/80 backdrop-blur-md border-b border-white/5 flex justify-between items-center px-4 h-14 max-w-300 mx-auto left-1/2 -translate-x-1/2">
      <div class="text-xl font-bold text-[#22c55e] font-lexend tracking-tight">
        智动AI教练
      </div>
      <div class="flex items-center gap-4">
        <button class="text-[#cac4d0] hover:text-white transition-colors">
          <Bell :size="24" />
        </button>
      </div>
    </header>

    <main 
      :class="[
        'flex-1 w-full max-w-300 mx-auto transition-all duration-300',
        !hideNav ? 'pt-14 pb-20 md:pl-60' : ''
      ]"
    >
      <router-view v-slot="{ Component, route }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <nav v-if="!hideNav" class="fixed bottom-0 left-0 w-full flex justify-around items-center h-16 pb-safe bg-[#1d1b20]/90 backdrop-blur-lg border-t border-white/5 shadow-[0_-2px_10px_rgba(0,0,0,0.5)] z-50 rounded-t-2xl md:hidden">
      <router-link 
        v-for="item in navItems" 
        :key="item.path" 
        :to="item.path"
        custom
        v-slot="{ navigate, isActive }"
      >
        <div 
          @click="navigate"
          class="flex flex-col items-center justify-center transition-all duration-200 cursor-pointer"
          :class="isActive ? 'text-[#22c55e] scale-110' : 'text-[#cac4d0] opacity-60 hover:opacity-100'"
        >
          <component :is="item.icon" :size="24" :stroke-width="isActive ? 2.5 : 2" />
          <span class="text-[10px] font-lexend font-medium mt-1">{{ item.label }}</span>
        </div>
      </router-link>
    </nav>

    <aside v-if="!hideNav" class="hidden md:flex fixed top-14 left-0 h-[calc(100vh-56px)] w-60 border-r border-white/5 bg-[#1d1b20]/50 flex-col py-8 px-4 gap-4">
      <router-link 
        v-for="item in navItems" 
        :key="item.path" 
        :to="item.path"
        custom
        v-slot="{ navigate, isActive }"
      >
        <div 
          @click="navigate"
          class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer"
          :class="isActive ? 'bg-[#22c55e]/10 text-[#22c55e] border border-[#22c55e]/20' : 'text-[#cac4d0] hover:bg-[#2b2930] hover:text-white'"
        >
          <component :is="item.icon" :size="20" />
          <span class="font-medium">{{ item.label }}</span>
        </div>
      </router-link>
    </aside>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { Bell, Dumbbell, Compass, Brain, User } from 'lucide-vue-next';

const route = useRoute();
const hideNav = computed(() => ['/training', '/auth', '/workout', '/login'].includes(route.path));

const navItems = [
  { path: '/', label: '训练', icon: Dumbbell },
  { path: '/plan', label: '计划', icon: Compass },
  { path: '/data', label: '数据', icon: Brain },
  { path: '/profile', label: '我的', icon: User },
];
</script>

<style scoped>
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.2s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(10px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }
.pb-safe { padding-bottom: env(safe-area-inset-bottom); }
</style>