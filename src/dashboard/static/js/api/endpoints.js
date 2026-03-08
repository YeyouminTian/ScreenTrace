/**
 * API端点定义
 */

export const API_ENDPOINTS = {
  // 统计数据
  STATS_OVERVIEW: '/api/stats/overview',
  STATS_KPI: '/api/stats/kpi',
  STATS_CATEGORY: '/api/stats/category',
  STATS_APPS: '/api/stats/apps',
  STATS_ACTIVITY_FORM: '/api/stats/activity-form',
  EFFICIENCY: '/api/efficiency',
  RECENT_ACTIVITIES: '/api/recent-activities',

  // 时间线
  TIMELINE: '/api/timeline',

  // 报告
  REPORT_TIMELINE: '/api/report/timeline',
  REPORT_NARRATIVE: '/api/report/narrative',

  // 数据质量
  QUALITY_METRICS: '/api/quality/metrics',

  // 图表数据 (FastAPI JSON 格式)
  CHART: {
    CATEGORY_PIE: '/api/charts/category-pie',
    DAILY_BAR: '/api/charts/daily-bar',
    HEATMAP: '/api/charts/heatmap',

    // 兼容旧的 Flask 端点 (返回 HTML)
    CATEGORY_PIE_HTML: '/api/chart/category-pie',
    DAILY_BAR_HTML: '/api/chart/daily-bar',
    HEATMAP_HTML: '/api/chart/heatmap',
    TREND_HTML: '/api/chart/trend',
    DASHBOARD_HTML: '/api/chart/dashboard'
  }
};

/**
 * 构建带查询参数的URL
 */
export function buildURL(endpoint, params = {}) {
  const url = new URL(endpoint, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, value);
    }
  });
  return url.pathname + url.search;
}
