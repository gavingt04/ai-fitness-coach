<template>
  <div class="history-container">
    <van-nav-bar title="训练数据统计" left-arrow @click-left="$router.back()" fixed placeholder />

    <div class="dashboard-content">
      <van-row gutter="16" class="stat-cards">
        <van-col span="12">
          <div class="card total-card">
            <div class="label">累计训练(次)</div>
            <div class="value">{{ totalSessions }}</div>
          </div>
        </van-col>
        <van-col span="12">
          <div class="card count-card">
            <div class="label">累计完成(个)</div>
            <div class="value">{{ totalReps }}</div>
          </div>
        </van-col>
      </van-row>

      <div class="chart-box">
        <h3>动作分布占比</h3>
        <div ref="pieChartRef" style="height: 250px;"></div>
      </div>

      <div class="chart-box">
        <h3>近七天训练趋势</h3>
        <div ref="lineChartRef" style="height: 300px;"></div>
      </div>

      <div class="list-box">
        <h3>最近活动</h3>
        <van-empty v-if="records.length === 0" description="暂无记录，快去训练吧" />
        <van-cell-group inset v-else>
          <van-cell 
            v-for="item in records.slice(0, 5)" 
            :key="item.id"
            :title="formatType(item.exercise_type)" 
            :value="item.count + ' 个'" 
            :label="formatTime(item.timestamp)"
          />
        </van-cell-group>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import * as echarts from 'echarts';

const authStore = useAuthStore();
const records = ref([]);
const totalSessions = ref(0);
const totalReps = ref(0);

const pieChartRef = ref(null);
const lineChartRef = ref(null);

const formatType = (type) => {
  const map = { SQUAT: '深蹲', BICEP_CURL: '弯举', DEADLIFT: '硬拉', PUSH_UP: '俯卧撑', BENCH_PRESS: '卧推' };
  return map[type] || type;
};

const formatTime = (ts) => new Date(ts).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

const initCharts = () => {
  // 1. 准备饼图数据：按动作类型分组
  const typeGroups = {};
  records.value.forEach(r => {
    typeGroups[r.exercise_type] = (typeGroups[r.exercise_type] || 0) + r.count;
  });
  const pieData = Object.keys(typeGroups).map(key => ({ name: formatType(key), value: typeGroups[key] }));

  const pieChart = echarts.init(pieChartRef.value);
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, position: 'outside' },
      data: pieData
    }]
  });

  // 2. 准备折线图数据：按日期汇总
  const dateGroups = {};
  records.value.forEach(r => {
    const date = new Date(r.timestamp).toLocaleDateString();
    dateGroups[date] = (dateGroups[date] || 0) + r.count;
  });
  const sortedDates = Object.keys(dateGroups).sort().slice(-7);
  
  const lineChart = echarts.init(lineChartRef.value);
  lineChart.setOption({
    xAxis: { type: 'category', data: sortedDates, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{
      data: sortedDates.map(d => dateGroups[d]),
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.2 },
      lineStyle: { width: 4 }
    }]
  });
};

onMounted(async () => {
  try {
    const res = await axios.get('/api/records/my', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    records.value = res.data;
    totalSessions.value = records.value.length;
    totalReps.value = records.value.reduce((acc, cur) => acc + cur.count, 0);

    await nextTick();
    initCharts();
  } catch (err) {
    console.error('获取历史记录失败', err);
  }
});
</script>

<style scoped>
.history-container { min-height: 100vh; background-color: #f7f8fa; padding-bottom: 30px; }
.dashboard-content { padding: 16px; }
.stat-cards { margin-bottom: 16px; }
.card { background: #fff; padding: 20px; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); text-align: center; }
.total-card { border-bottom: 4px solid #1989fa; }
.count-card { border-bottom: 4px solid #07c160; }
.label { font-size: 12px; color: #969799; margin-bottom: 8px; }
.value { font-size: 24px; font-weight: 900; color: #323233; }
.chart-box { background: #fff; padding: 16px; border-radius: 16px; margin-bottom: 16px; }
.chart-box h3 { margin: 0 0 15px 0; font-size: 14px; color: #323233; }
.list-box h3 { margin: 20px 0 10px 16px; font-size: 14px; color: #969799; }
</style>