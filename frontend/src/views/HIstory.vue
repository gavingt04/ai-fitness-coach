<template>
  <div class="history-container">
    <van-nav-bar title="运动成就" left-arrow @click-left="$router.back()" />
    
    <div class="summary-card">
      <div class="stat-box">
        <span class="num">{{ totalCount }}</span>
        <span class="label">累计总次数</span>
      </div>
      <div class="stat-box">
        <span class="num">{{ trainingDays }}</span>
        <span class="label">训练天数</span>
      </div>
    </div>

    <div class="chart-container">
      <div class="chart-title">近期训练趋势</div>
      <div ref="chartRef" style="width: 100%; height: 220px;"></div>
    </div>

    <div class="list-title">训练明细</div>
    <van-list finished-text="没有更多了">
      <van-cell v-for="item in records" :key="item.id" class="record-cell">
        <template #title>
          <span class="type">{{ item.exercise_type }}</span>
          <span class="date">{{ formatDate(item.timestamp) }}</span>
        </template>
        <template #value>
          <span class="count">+{{ item.count }}</span>
        </template>
      </van-cell>
    </van-list>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import * as echarts from 'echarts'; // 引入 ECharts

const authStore = useAuthStore();
const records = ref([]);
const chartRef = ref(null); // 图表 DOM 引用

// 累计总数
const totalCount = computed(() => {
  return records.value.reduce((sum, item) => sum + item.count, 0);
});

// 计算训练天数
const trainingDays = computed(() => {
  const uniqueDays = new Set(
    records.value.map(item => {
      const d = new Date(item.timestamp);
      return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
    })
  );
  return uniqueDays.size;
});

// --- 【新增】：初始化并绘制图表 ---
const initChart = () => {
  if (!chartRef.value || records.value.length === 0) return;

  // 1. 数据按日期聚合 (把同一天的次数加起来)
  const dailyData = {};
  records.value.forEach(item => {
    const d = new Date(item.timestamp);
    const dateKey = `${d.getMonth() + 1}-${d.getDate()}`;
    if (!dailyData[dateKey]) dailyData[dateKey] = 0;
    dailyData[dateKey] += item.count;
  });

  // 2. 提取 X轴(日期) 和 Y轴(次数)
  // 注意：后端传来的数据是倒序（最新的在前面），画图时我们需要正序（从左到右时间递增），所以要 reverse
  const dates = Object.keys(dailyData).reverse();
  const counts = Object.values(dailyData).reverse();

  // 3. 实例化 ECharts
  const myChart = echarts.init(chartRef.value);
  
  // 4. 图表高逼格配置
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderRadius: 8
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#ebedf0' } },
      axisLabel: { color: '#969799', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#ebedf0' } },
      axisLabel: { color: '#969799' }
    },
    series: [
      {
        data: counts,
        type: 'bar',
        barWidth: '40%',
        itemStyle: {
          // 漂亮的蓝色渐变与圆角
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#4facfe' },
            { offset: 1, color: '#00f2fe' }
          ]),
          borderRadius: [6, 6, 0, 0]
        },
        label: {
          show: true,
          position: 'top',
          color: '#1989fa',
          fontWeight: 'bold'
        }
      }
    ]
  };

  myChart.setOption(option);
};

// 获取数据
const fetchHistory = async () => {
  try {
    const res = await axios.get('/api/records/my', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    records.value = res.data;
    
    // 数据获取成功后，等待 DOM 渲染完毕再画图
    nextTick(() => {
      initChart();
    });
  } catch (err) {
    console.error('获取历史记录失败', err);
  }
};

const formatDate = (dateStr) => {
  const d = new Date(dateStr);
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  const hours = d.getHours().toString().padStart(2, '0');
  const minutes = d.getMinutes().toString().padStart(2, '0');
  return `${month}-${day} ${hours}:${minutes}`;
};

onMounted(fetchHistory);
</script>

<style scoped>
.history-container { min-height: 100vh; background: #f7f8fa; padding-bottom: 20px; }

.summary-card {
  margin: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #1989fa, #0570db);
  border-radius: 16px;
  display: flex;
  justify-content: space-around;
  color: white;
  box-shadow: 0 4px 12px rgba(25,137,250,0.3);
}

.stat-box { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.num { font-size: 32px; font-weight: 900; }
.label { font-size: 13px; opacity: 0.9; }

/* 图表容器样式 */
.chart-container {
  margin: 0 16px 16px;
  padding: 16px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.chart-title {
  font-size: 14px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 10px;
}

.list-title {
  margin: 0 16px 8px;
  font-size: 14px;
  font-weight: bold;
  color: #323233;
}

.record-cell { margin-bottom: 8px; align-items: center; border-radius: 8px; margin: 0 16px 8px; width: auto;}
.type { font-weight: bold; color: #323233; margin-right: 10px; }
.date { font-size: 12px; color: #969799; }
.count { font-size: 20px; color: #1989fa; font-weight: 900; }
</style>