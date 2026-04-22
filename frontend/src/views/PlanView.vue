<template>
  <div class="min-h-screen bg-[#0f1115] pb-24 text-[#e6e1e5] pt-6 px-4 md:px-6 space-y-6 font-sans antialiased">
    <section class="space-y-1">
      <div class="flex items-center gap-3 mb-2">
        <button @click="$router.back()" class="w-10 h-10 flex items-center justify-center rounded-full bg-[#2b2930] shadow-sm hover:bg-[#1d1b20] transition-colors">
          <ArrowLeft :size="20" />
        </button>
        <h1 class="text-2xl font-bold">智能计划生成</h1>
      </div>
      <p class="text-sm text-[#cac4d0] pl-1">根据您的身体数据与目标，AI 将为您量身定制训练方案。</p>
    </section>

    <section v-if="!hasGeneratedPlan" class="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-500">
      <div class="col-span-1 md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-[#1d1b20] p-4 rounded-2xl border border-white/5 flex flex-col gap-2 shadow-sm focus-within:ring-1 focus-within:ring-[#22c55e] transition-all">
          <div class="flex items-center gap-2 text-[#cac4d0]"><User :size="14" /><span class="text-[10px] font-bold uppercase tracking-widest">年龄</span></div>
          <input type="number" v-model="metrics.age" class="bg-transparent border-none p-0 text-xl font-bold text-[#22c55e] focus:ring-0 outline-none w-full" />
        </div>
        <div class="bg-[#1d1b20] p-4 rounded-2xl border border-white/5 flex flex-col gap-2 shadow-sm focus-within:ring-1 focus-within:ring-[#22c55e] transition-all">
          <div class="flex items-center gap-2 text-[#cac4d0]"><Scale :size="14" /><span class="text-[10px] font-bold uppercase tracking-widest">体重 (kg)</span></div>
          <input type="number" v-model="metrics.weight" class="bg-transparent border-none p-0 text-xl font-bold text-[#22c55e] focus:ring-0 outline-none w-full" />
        </div>
        <div class="bg-[#1d1b20] p-4 rounded-2xl border border-white/5 flex flex-col gap-2 shadow-sm focus-within:ring-1 focus-within:ring-[#22c55e] transition-all">
          <div class="flex items-center gap-2 text-[#cac4d0]"><Activity :size="14" /><span class="text-[10px] font-bold uppercase tracking-widest">身份/职业</span></div>
          <input type="text" v-model="metrics.identity" placeholder="例如: 学生" class="bg-transparent border-none p-0 text-base font-bold text-[#22c55e] focus:ring-0 outline-none w-full placeholder-[#22c55e]/40" />
        </div>
        <div class="bg-[#1d1b20] p-4 rounded-2xl border border-white/5 flex flex-col gap-2 shadow-sm focus-within:ring-1 focus-within:ring-[#22c55e] transition-all">
          <div class="flex items-center gap-2 text-[#cac4d0]"><ShieldAlert :size="14" /><span class="text-[10px] font-bold uppercase tracking-widest">伤病情况</span></div>
          <input type="text" v-model="metrics.injury" placeholder="无" class="bg-transparent border-none p-0 text-base font-bold text-[#22c55e] focus:ring-0 outline-none w-full placeholder-[#22c55e]/40" />
        </div>
      </div>

      <div class="bg-[#1d1b20] p-4 rounded-2xl flex flex-col gap-3 border border-white/5 shadow-sm">
        <div class="flex items-center gap-2"><Target :size="20" class="text-[#22c55e]" /><h2 class="text-lg font-bold">训练目标</h2></div>
        <div class="grid grid-cols-3 gap-2">
          <button v-for="goal in ['减脂', '增肌', '塑形']" :key="goal" @click="metrics.goal = goal"
            :class="['py-2 rounded-xl text-sm font-bold transition-all', metrics.goal === goal ? 'bg-[#22c55e] text-white' : 'bg-[#2b2930] text-[#cac4d0] hover:bg-[#2b2930]/80']">
            {{ goal }}
          </button>
        </div>
      </div>

      <div class="bg-[#1d1b20] p-4 rounded-2xl flex flex-col gap-3 border border-white/5 shadow-sm">
        <div class="flex items-center gap-2"><BarChart :size="20" class="text-[#22c55e]" /><h2 class="text-lg font-bold">当前水平</h2></div>
        <div class="grid grid-cols-3 gap-2">
          <button v-for="level in ['初级', '中级', '高级']" :key="level" @click="metrics.level = level"
            :class="['py-2 rounded-xl text-sm font-bold transition-all', metrics.level === level ? 'bg-[#22c55e] text-white' : 'bg-[#2b2930] text-[#cac4d0] hover:bg-[#2b2930]/80']">
            {{ level }}
          </button>
        </div>
      </div>

      <div class="bg-[#1d1b20] p-4 rounded-2xl flex flex-col gap-3 border border-white/5 shadow-sm md:col-span-1">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2"><Calendar :size="20" class="text-[#22c55e]" /><h2 class="text-lg font-bold">频率</h2></div>
          <div class="text-[#22c55e] font-bold text-xl">{{ metrics.days }}<span class="text-xs ml-1 font-normal text-[#cac4d0]">天/周</span></div>
        </div>
        <div class="flex items-center gap-4 pt-2 border-t border-white/5">
          <button @click="metrics.days = Math.max(1, metrics.days - 1)" class="w-8 h-8 rounded-full bg-[#2b2930] flex items-center justify-center text-white"><Minus :size="16" /></button>
          <div class="flex-1 h-1.5 bg-[#2b2930] rounded-full overflow-hidden relative">
            <div class="absolute h-full bg-[#22c55e] transition-all" :style="{ width: `${(metrics.days/7)*100}%` }"></div>
          </div>
          <button @click="metrics.days = Math.min(7, metrics.days + 1)" class="w-8 h-8 rounded-full bg-[#2b2930] flex items-center justify-center text-white"><Plus :size="16" /></button>
        </div>
      </div>

      <div class="bg-[#1d1b20] p-4 rounded-2xl flex flex-col gap-3 border border-white/5 shadow-sm md:col-span-1">
        <div class="flex items-center gap-2"><Dumbbell :size="20" class="text-[#22c55e]" /><h2 class="text-lg font-bold">器械</h2></div>
        <div class="flex flex-wrap gap-2">
          <button v-for="eq in ['哑铃', '杠铃', '弹力带', '自重']" :key="eq" @click="toggleEquipment(eq)"
            :class="['px-3 py-1 rounded-full text-[10px] font-bold border transition-all', metrics.equipments.includes(eq) ? 'bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]' : 'bg-transparent border-[#49454f] text-[#cac4d0]']">
            {{ eq }}
          </button>
        </div>
      </div>

      <button @click="generatePlan" :disabled="isGenerating" class="col-span-1 md:col-span-2 h-14 bg-[#22c55e] text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-[#22c55e]/20 active:scale-[0.98] transition-all disabled:opacity-50 disabled:grayscale">
        <Bolt v-if="!isGenerating" :size="20" fill="currentColor" />
        <span v-else class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
        {{ isGenerating ? 'AI 引擎计算中...' : '生成专属计划' }}
      </button>
    </section>

    <section v-else class="space-y-4 animate-in slide-in-from-bottom-4 duration-500">
      <div class="flex items-end justify-between">
        <div><h2 class="text-xl font-bold">专属训练计划</h2><p class="text-xs text-[#cac4d0] mt-1 italic">基于您的最新评估生成</p></div>
        <div class="flex items-center gap-1.5 text-[#22c55e] bg-[#22c55e]/10 px-2.5 py-1 rounded-lg border border-[#22c55e]/20"><Cloud :size="14" /><Check :size="10" /><span class="text-[10px] font-bold">已自动保存</span></div>
      </div>

      <div class="space-y-3">
        <div v-for="day in groupedPlan" :key="day.id" class="rounded-2xl border border-white/5 overflow-hidden transition-all" :class="expandedDay === day.id ? 'bg-[#1d1b20] shadow-md' : 'bg-[#1d1b20]/60'">
          <button @click="expandedDay = expandedDay === day.id ? 0 : day.id" class="w-full p-4 flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div :class="['w-10 h-10 rounded-xl flex items-center justify-center font-bold text-lg', expandedDay === day.id ? 'bg-[#22c55e] text-white' : 'bg-[#2b2930] text-[#cac4d0]']">D{{ day.id }}</div>
              <div class="text-left"><h3 class="font-bold">{{ day.title }}</h3><p class="text-[10px] text-[#cac4d0]">{{ day.exercises.length }} 个动作</p></div>
            </div>
            <component :is="expandedDay === day.id ? ChevronUp : ChevronDown" :size="20" class="text-[#cac4d0]" />
          </button>
          <div v-show="expandedDay === day.id" class="border-t border-white/5">
            <div v-for="(ex, i) in day.exercises" :key="i" class="flex justify-between items-center py-3 px-4 border-b last:border-0 border-white/5 bg-[#2b2930]/30">
              <div class="flex flex-col"><span class="font-bold text-sm text-[#e6e1e5]">{{ ex.exercise_name }}</span><span class="text-[10px] text-[#cac4d0]">{{ ex.advice || '保持核心收紧' }}</span></div>
              <div class="text-right flex items-center gap-1">
                <span class="font-bold text-[#22c55e]">{{ ex.sets }}</span><span class="text-[10px] text-[#cac4d0]">组 ×</span>
                <span class="font-bold">{{ ex.reps }}</span><span class="text-[10px] text-[#cac4d0]">次</span>
                <button @click="$router.push({ path: '/workout', query: { exercise: ex.exercise_code } })" class="ml-2 w-7 h-7 rounded-full bg-[#22c55e]/10 text-[#22c55e] flex items-center justify-center"><Play :size="12" fill="currentColor" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <button @click="rawPlanData = []" class="w-full p-4 bg-[#1d1b20] border border-white/5 text-[#cac4d0] hover:text-white hover:bg-[#2b2930] transition-colors font-bold rounded-2xl flex items-center justify-center gap-2 mt-4"><RefreshCw :size="20" /> 重新生成评估</button>
    </section>
  </div>
</template>

<script setup>
// 【新增】：导入了 onMounted 生命周期钩子
import { ref, reactive, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';
import { showToast, showFailToast } from 'vant';
import { ArrowLeft, Bolt, Target, BarChart, Calendar, Dumbbell, Cloud, Check, ChevronDown, ChevronUp, RefreshCw, Minus, Plus, User, Scale, Activity, ShieldAlert, Play } from 'lucide-vue-next';

const authStore = useAuthStore();
const isGenerating = ref(false);
const rawPlanData = ref([]); 
const expandedDay = ref(1);

const metrics = reactive({ age: 25, weight: 70, identity: '学生', injury: '', goal: '减脂', level: '中级', days: 4, equipments: ['哑铃', '弹力带'] });
const hasGeneratedPlan = computed(() => rawPlanData.value.length > 0);

// 【核心逻辑补充】：页面加载时自动请求已有计划
onMounted(async () => {
  try {
    const res = await axios.get('/api/plan/my', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    // 如果数据库里已经有了计划，就填充给前端展示
    if (res.data && res.data.plan && res.data.plan.length > 0) {
      rawPlanData.value = res.data.plan;
      expandedDay.value = rawPlanData.value[0]?.day || 1;
    }
  } catch (error) {
    console.error("加载已有计划失败:", error);
  }
});

const toggleEquipment = (eq) => {
  const i = metrics.equipments.indexOf(eq);
  i > -1 ? metrics.equipments.splice(i, 1) : metrics.equipments.push(eq);
};

const groupedPlan = computed(() => {
  const groups = {};
  rawPlanData.value.forEach(item => {
    // 兼容重新载入后的标题展示
    if (!groups[item.day]) groups[item.day] = { id: item.day, title: `训练日 ${item.day}`, exercises: [] };
    groups[item.day].exercises.push(item);
  });
  return Object.values(groups).sort((a, b) => a.id - b.id);
});

const generatePlan = async () => {
  isGenerating.value = true;
  try {
    const res = await axios.post('/api/plan/generate', { ...metrics, weight: Number(metrics.weight) }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    rawPlanData.value = res.data.plan;
    expandedDay.value = rawPlanData.value[0]?.day || 1;
    showToast('AI 计划已生成');
  } catch (error) {
    showFailToast('生成失败，请检查服务');
  } finally {
    isGenerating.value = false;
  }
};
</script>