/**
 * ECharts 渲染模块
 * 使用 ECharts 替代 Plotly 进行数据可视化
 */

import { apiClient } from '../api/client.js';
import { API_ENDPOINTS, buildURL } from '../api/endpoints.js';

// ECharts 实例缓存
const chartInstances = {};

// 颜色配置
const COLORS = {
  primary: '#1a1f3a',
  secondary: '#ff6b4a',
  tertiary: '#4ecdc4',
  quaternary: '#45b7d1',
  success: '#2ecc71',
  warning: '#f39c12',
  danger: '#e74c3c',
  categories: {
    work: '#3498db',
    study: '#9b59b6',
    leisure: '#e74c3c',
    life: '#2ecc71',
    social: '#f39c12',
    unknown: '#95a5a6'
  }
};

// 主题配置
const THEME = {
  dark: {
    background: '#0f1419',
    text: '#ffffff',
    textSecondary: '#8899a6',
    border: '#192734',
    cardBg: '#15202b'
  },
  light: {
    background: '#f5f8fa',
    text: '#14171a',
    textSecondary: '#657786',
    border: '#e1e8ed',
    cardBg: '#ffffff'
  }
};

/**
 * 获取当前主题
 */
function getCurrentTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return isDark ? THEME.dark : THEME.light;
}

/**
 * 获取颜色调色板
 */
function getColorPalette() {
  return [
    COLORS.categories.work,
    COLORS.categories.study,
    COLORS.categories.leisure,
    COLORS.categories.life,
    COLORS.categories.social,
    COLORS.categories.unknown,
    '#e67e22',
    '#1abc9c',
    '#34495e',
    '#16a085'
  ];
}

/**
 * 初始化 ECharts 实例
 */
export function initChart(containerId, options = {}) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Chart container #${containerId} not found`);
    return null;
  }

  // 如果已存在实例，先销毁
  if (chartInstances[containerId]) {
    chartInstances[containerId].dispose();
  }

  const chart = echarts.init(container, null, { renderer: 'canvas' });
  chartInstances[containerId] = chart;

  // 响应式调整
  const resizeHandler = () => {
    chart.resize();
  };
  window.addEventListener('resize', resizeHandler);

  // 清理时移除监听器
  chart.on('dispose', () => {
    window.removeEventListener('resize', resizeHandler);
  });

  return chart;
}

/**
 * 渲染饼图
 */
export async function renderCategoryPieChart(containerId, params = { days: 7 }) {
  const chart = initChart(containerId);
  if (!chart) return;

  try {
    const data = await apiClient.fetch(
      buildURL(API_ENDPOINTS.CHART.CATEGORY_PIE, params)
    );

    if (!data || data.length === 0) {
      chart.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: getCurrentTheme().textSecondary }
        }
      });
      return;
    }

    const theme = getCurrentTheme();

    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
        backgroundColor: theme.cardBg,
        borderColor: theme.border,
        textStyle: { color: theme.text }
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        textStyle: { color: theme.text }
      },
      series: [{
        name: '生活维度',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: theme.background,
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            color: theme.text
          }
        },
        labelLine: { show: false },
        data: data,
        color: getColorPalette()
      }]
    });

  } catch (error) {
    console.error('Failed to render pie chart:', error);
    showErrorChart(containerId);
  }
}

/**
 * 渲染柱状图
 */
export async function renderDailyBarChart(containerId, params = { days: 7 }) {
  const chart = initChart(containerId);
  if (!chart) return;

  try {
    const response = await apiClient.fetch(
      buildURL(API_ENDPOINTS.CHART.DAILY_BAR, params)
    );

    const theme = getCurrentTheme();

    if (!response || !response.dates || response.dates.length === 0) {
      chart.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: theme.textSecondary }
        }
      });
      return;
    }

    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: theme.cardBg,
        borderColor: theme.border,
        textStyle: { color: theme.text }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: response.dates,
        axisLine: { lineStyle: { color: theme.border } },
        axisLabel: { color: theme.textSecondary }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: theme.border } },
        axisLabel: { color: theme.textSecondary },
        splitLine: { lineStyle: { color: theme.border, type: 'dashed' } }
      },
      series: [{
        name: '活动次数',
        type: 'bar',
        data: response.counts,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: COLORS.secondary },
            { offset: 1, color: COLORS.tertiary }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: COLORS.tertiary },
              { offset: 1, color: COLORS.secondary }
            ])
          }
        }
      }]
    });

  } catch (error) {
    console.error('Failed to render bar chart:', error);
    showErrorChart(containerId);
  }
}

/**
 * 渲染热力图
 */
export async function renderHeatmapChart(containerId, params = { days: 7 }) {
  const chart = initChart(containerId);
  if (!chart) return;

  try {
    const response = await apiClient.fetch(
      buildURL(API_ENDPOINTS.CHART.HEATMAP, params)
    );

    const theme = getCurrentTheme();

    if (!response || !response.data || response.data.length === 0) {
      chart.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: theme.textSecondary }
        }
      });
      return;
    }

    const hours = [];
    for (let i = 0; i < 24; i++) {
      hours.push(`${i}:00`);
    }
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        position: 'top',
        formatter: function(params) {
          return `${weekdays[params.value[0]]} ${hours[params.value[1]]}<br/>活动次数: ${params.value[2]}`;
        },
        backgroundColor: theme.cardBg,
        borderColor: theme.border,
        textStyle: { color: theme.text }
      },
      grid: {
        left: '15%',
        right: '10%',
        top: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: hours,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: theme.border } },
        axisLabel: { color: theme.textSecondary }
      },
      yAxis: {
        type: 'category',
        data: weekdays,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: theme.border } },
        axisLabel: { color: theme.textSecondary }
      },
      visualMap: {
        min: 0,
        max: Math.max(...response.data.map(d => d[2]), 10),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: {
          color: [theme.background, COLORS.tertiary, COLORS.secondary]
        },
        textStyle: { color: theme.text }
      },
      series: [{
        name: '活动热力',
        type: 'heatmap',
        data: response.data,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    });

  } catch (error) {
    console.error('Failed to render heatmap:', error);
    showErrorChart(containerId);
  }
}

/**
 * 渲染时间线图表
 */
export async function renderTimelineChart(containerId, days = 1) {
  const chart = initChart(containerId);
  if (!chart) return;

  try {
    const response = await apiClient.fetch(
      buildURL(API_ENDPOINTS.TIMELINE, { days })
    );

    const theme = getCurrentTheme();

    if (!response || !response.records || response.records.length === 0) {
      chart.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: theme.textSecondary }
        }
      });
      return;
    }

    // 将数据转换为 Gantt 格式
    const categoryColors = COLORS.categories;
    const records = response.records;

    const categoryData = {};
    records.forEach(record => {
      const category = record.life_category || 'unknown';
      if (!categoryData[category]) {
        categoryData[category] = [];
      }
      categoryData[category].push({
        name: record.app_name || 'Unknown',
        value: [
          records.indexOf(record),
          records.indexOf(record) + 1,
          record.description || ''
        ].join(','),
        itemStyle: { color: categoryColors[category] || categoryColors.unknown }
      });
    });

    // 简化的 Gantt 视图：使用散点图展示时间分布
    const timePoints = records.map(r => {
      const time = new Date(r.timestamp);
      return {
        name: r.app_name || 'Unknown',
        value: [time.getHours() + time.getMinutes() / 60, r.life_category || 'unknown'],
        itemStyle: { color: categoryColors[r.life_category] || categoryColors.unknown }
      };
    });

    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          const hour = Math.floor(params.value[0]);
          const minute = Math.round((params.value[0] - hour) * 60);
          return `${params.name}<br/>时间: ${hour}:${minute.toString().padStart(2, '0')}<br/>类别: ${params.value[1]}`;
        },
        backgroundColor: theme.cardBg,
        borderColor: theme.border,
        textStyle: { color: theme.text }
      },
      grid: {
        left: '10%',
        right: '10%',
        top: '10%',
        bottom: '10%'
      },
      xAxis: {
        type: 'value',
        min: 0,
        max: 24,
        name: '小时',
        nameLocation: 'middle',
        nameGap: 25,
        axisLine: { lineStyle: { color: theme.border } },
        axisLabel: {
          color: theme.textSecondary,
          formatter: '{value}:00'
        },
        splitLine: { lineStyle: { color: theme.border, type: 'dashed' } }
      },
      yAxis: {
        type: 'category',
        data: Object.keys(categoryColors),
        axisLine: { lineStyle: { color: theme.border } },
        axisLabel: { color: theme.textSecondary }
      },
      series: [{
        type: 'scatter',
        symbolSize: 10,
        data: timePoints,
        emphasis: {
          scale: 1.5
        }
      }]
    });

  } catch (error) {
    console.error('Failed to render timeline chart:', error);
    showErrorChart(containerId);
  }
}

/**
 * 显示错误状态的图表
 */
function showErrorChart(containerId) {
  const chart = initChart(containerId);
  if (!chart) return;

  const theme = getCurrentTheme();
  chart.setOption({
    title: {
      text: '加载失败',
      left: 'center',
      top: 'center',
      textStyle: { color: COLORS.danger }
    }
  });
}

/**
 * 销毁所有图表实例
 */
export function disposeAllCharts() {
  Object.keys(chartInstances).forEach(id => {
    if (chartInstances[id]) {
      chartInstances[id].dispose();
      delete chartInstances[id];
    }
  });
}

/**
 * 刷新所有图表
 */
export async function refreshAllCharts(params = { days: 7 }) {
  await Promise.allSettled([
    renderCategoryPieChart('categoryPieChart', params),
    renderDailyBarChart('dailyBarChart', params),
    renderHeatmapChart('heatmapChart', params)
  ]);
}
