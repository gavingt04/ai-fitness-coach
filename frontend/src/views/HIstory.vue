<template>
  <div class="p-4 md:p-6 space-y-6 min-h-screen bg-[#0f1115] text-[#e6e1e5] pb-24 font-sans">
    <section class="space-y-1">
      <h1 class="text-2xl font-bold tracking-tight">历史数据洞察</h1>
      <p class="text-sm text-[#cac4d0]">查看您的训练表现与 AI 生物力学反馈</p>
    </section>

    <section class="grid grid-cols-2 md:grid-cols-3 gap-3">
      <div class="bg-[#1d1b20] rounded-2xl p-4 border border-white/5 space-y-4 shadow-sm">
        <div class="flex items-center gap-2 text-[#22c55e] text-[10px] font-bold uppercase tracking-wider">
          <Calendar :size="14" /> 累计锻炼天数
        </div>
        <div class="flex items-baseline gap-1">
          <span class="text-4xl font-bold text-[#22c55e]">{{ totalDays }}</span>
          <span class="text-xs text-[#cac4d0] ml-1">天</span>
        </div>
      </div>

      <div class="bg-[#1d1b20] rounded-2xl p-4 border border-white/5 md:col-span-2 flex flex-col justify-between shadow-sm">
  <div class="flex items-center gap-2 text-[#22c55e] text-[10px] font-bold uppercase tracking-wider">
    <Timer :size="14" /> 本周时长
  </div>
  <div class="flex items-center justify-between w-full mt-4">
    <div class="flex-1 space-y-1 pr-8">
      <div class="flex justify-between text-[10px] text-[#cac4d0] mb-1 font-bold">
        <span>0 分钟</span><span>目标: 90分钟</span>
      </div>
      <div class="h-1.5 bg-[#2b2930] rounded-full overflow-hidden">
        <div class="h-full bg-[#22c55e] transition-all duration-1000" :style="{ width: `${weeklyProgress}%` }"></div>
      </div>
    </div>
    <div class="flex items-baseline gap-1">
      <span class="text-3xl font-bold">{{ weeklyMinutes }}</span><span class="text-xs text-[#cac4d0] ml-1">分钟</span>
    </div>
  </div>
</div>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-[#1d1b20] rounded-2xl p-4 border border-white/5 space-y-4 shadow-sm">
        <div class="flex justify-between items-center">
          <h2 class="font-bold flex items-center gap-2"><TrendingUp :size="18" class="text-[#22c55e]" />运动趋势</h2>
          <span class="text-[10px] font-bold text-[#22c55e] bg-[#22c55e]/10 px-2 py-1 rounded-lg">Reps / 天</span>
        </div>
        <div ref="barChartRef" class="h-48 w-full"></div>
      </div>

      <div class="bg-[#1d1b20] rounded-2xl p-4 border border-white/5 space-y-4 shadow-sm">
        <div class="flex justify-between items-center">
          <h2 class="font-bold flex items-center gap-2"><PieChartIcon :size="18" class="text-[#22c55e]" />动作占比</h2>
        </div>
        <div class="space-y-4 pt-2">
          <div v-for="item in distribution" :key="item.name" class="space-y-1.5">
            <div class="flex justify-between text-xs font-bold">
              <span>{{ item.name }}</span><span>{{ item.value }}%</span>
            </div>
            <div class="w-full bg-[#2b2930] rounded-full h-1.5 overflow-hidden">
              <div class="h-full rounded-full transition-all duration-1000" :style="{ width: `${item.value}%`, backgroundColor: item.color }"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <h2 class="text-lg font-bold">系统判决日志</h2>
      <div class="space-y-3">
        <div v-for="(log, i) in logs" :key="i" class="bg-[#1d1b20] rounded-2xl p-4 border border-white/5 space-y-4 shadow-sm hover:border-[#22c55e]/30 transition-all cursor-pointer group">
          <div class="flex justify-between items-start">
            <div class="space-y-1">
              <h3 class="font-bold group-hover:text-[#22c55e] transition-colors">{{ log.name }}</h3>
              <p class="text-[10px] text-[#cac4d0] font-medium">{{ log.date }}</p>
            </div>
            <div class="text-right space-y-1">
              <div class="text-sm font-bold">{{ log.reps }} 次</div>
              <div class="text-[10px] text-[#22c55e] font-bold uppercase tracking-widest">{{ log.calories }} kcal</div>
            </div>
          </div>
          <div class="h-px bg-white/5"></div>
          <div class="flex flex-wrap gap-2 items-center">
            <span class="text-[10px] text-[#cac4d0] font-bold">AI 指导反馈:</span>
            <div v-for="(f, j) in log.feedback" :key="j" 
                 :class="['rounded-lg px-2 py-1 text-[10px] flex items-center gap-1.5 border font-bold', 
                          f.type === 'warning' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-[#2b2930] text-[#cac4d0] border-white/5']">
              <component :is="f.icon" :size="12" />
              {{ f.text }}
            </div>
          </div>
        </div>
        
        <div v-if="logs.length === 0" class="text-center py-8 text-[#cac4d0] text-sm">
          暂无训练数据，去开启你的第一次训练吧！
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import * as echarts from 'echarts';
import { Calendar, Timer, TrendingUp, PieChart as PieChartIcon, AlertTriangle, Star } from 'lucide-vue-next';

const authStore = useAuthStore();
const logs = ref([]);
const distribution = ref([]);
const barChartRef = ref(null);

// 新增的响应式变量
const totalDays = ref(0);
const weeklyMinutes = ref(0);
const weeklyProgress = ref(0);

// 动作名称格式化
const formatType = (t) => ({ 
  SQUAT: '深蹲', 
  BICEP_CURL: '二头弯举', 
  DEADLIFT: '硬拉', 
  PUSH_UP: '俯卧撑', 
  BENCH_PRESS: '卧推' 
}[t] || t);

// AI 诊断词汇翻译字典
const issueTranslation = {
  'Knee Valgus': '膝盖内扣',
  'High Impact': '下落冲击过大',
  'Shoulder Stress': '肩部受压/手肘外展过大',
  'AC Joint Stress': '握距过窄/肩锁关节受压',
  'Spinal Creep': '背部弯曲',
  'Bar Path Shift': '轨迹偏移',
  'Core Sagging': '核心塌陷/塌腰',
  'Trunk Swing': '躯干晃动借力',
  'Deltoid Compensation': '三角肌代偿',
  'Ready': '准备就绪',
  'Perfect!': '动作标准'
};

const MET_VALUES = { SQUAT: 5.0, BICEP_CURL: 3.0, DEADLIFT: 6.0, PUSH_UP: 3.8, BENCH_PRESS: 3.5 };

const translateFeedback = (text) => {
  const key = text.trim();
  return issueTranslation[key] || key; 
};

onMounted(async () => {
  try {
    // 1. 获取用户真实体重（用于精准卡路里计算）
    let userWeight = 70;
    try {
      const userRes = await axios.get('/api/users/me', { headers: { Authorization: `Bearer ${authStore.token}` } });
      userWeight = userRes.data.weight || 70;
    } catch(e) { console.warn("无法获取体重，使用默认值"); }

    // 2. 获取训练记录
    const res = await axios.get('/api/records/my', { headers: { Authorization: `Bearer ${authStore.token}` } });
    const records = res.data;
    
    // --- 【动态计算 1】：累计锻炼天数 ---
    const uniqueDates = new Set(records.map(r => new Date(r.timestamp).toLocaleDateString('zh-CN')));
    totalDays.value = uniqueDates.size;

    // --- 【动态计算 2】：本周时长 ---
    const now = new Date();
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    let weeklyReps = 0;
    
    records.forEach(r => {
      if (new Date(r.timestamp) >= oneWeekAgo) {
        weeklyReps += r.count;
      }
    });
    
    // 假设每个动作平均耗时 4 秒，计算总分钟数
   const minutes = Math.round((weeklyReps * 4) / 60); 
   weeklyMinutes.value = minutes;
   // 目标假设为 300 分钟 (即原来的 5 小时)，计算进度条百分比
   weeklyProgress.value = Math.min((minutes / 300) * 100, 100);
    // --- 【动态计算 3】：动作分布占比 ---
    const typeCount = {};
    let totalReps = 0;
    records.forEach(r => { 
      const name = formatType(r.exercise_type);
      typeCount[name] = (typeCount[name] || 0) + r.count;
      totalReps += r.count;
    });
    
    distribution.value = Object.keys(typeCount).map((name, i) => ({
      name, value: Math.round((typeCount[name]/totalReps)*100),
      color: ['#22c55e', '#10b981', '#f59e0b', '#6366f1'][i % 4]
    })).sort((a,b) => b.value - a.value);

    // --- 【日志处理】 ---
    logs.value = records.slice(0, 10).map(r => {
      const met = MET_VALUES[r.exercise_type] || 3.0; 
      const kcalPerRep = met * userWeight * (4 / 3600); // 引入真实体重 userWeight
      const totalKcal = (r.count * kcalPerRep).toFixed(1);

      return {
        name: formatType(r.exercise_type),
        date: new Date(r.timestamp).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        reps: r.count,
        calories: totalKcal,
        feedback: r.issues ? r.issues.split(',').filter(Boolean).map(text => ({ 
          type: 'warning', 
          text: translateFeedback(text), 
          icon: AlertTriangle 
        })) : [{ type: 'success', text: '动作标准', icon: Star }]
      };
    });

    await nextTick();
    initChart(records);
  } catch (e) { 
    console.error(e); 
  }
});

const initChart = (records) => {
  if (!barChartRef.value) return;
  const chart = echarts.init(barChartRef.value);
  const dataMap = {};
  
  records.forEach(r => {
    const d = new Date(r.timestamp).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
    dataMap[d] = (dataMap[d] || 0) + r.count;
  });
  
  const dates = Object.keys(dataMap).sort().slice(-7);
  
  if (dates.length === 0) {
    chart.setOption({ title: { text: '暂无数据', textStyle: { color: '#cac4d0', fontSize: 12 }, left: 'center', top: 'center' } });
    return;
  }

  chart.setOption({
    grid: { top: 10, left: 0, right: 0, bottom: 20, containLabel: true },
    xAxis: { type: 'category', data: dates, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#cac4d0', fontSize: 10 } },
    yAxis: { show: false },
    series: [{
      data: dates.map(d => dataMap[d]), type: 'bar', barWidth: '40%',
      itemStyle: { borderRadius: [4, 4, 0, 0], color: (p) => p.dataIndex === dates.length-1 ? '#22c55e' : 'rgba(34, 197, 94, 0.2)' }
    }]
  });
};
</script>