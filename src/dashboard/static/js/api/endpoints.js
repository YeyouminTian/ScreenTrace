/**
 * API端点定义
 */

export const API_ENDPOINTS = {
  // 统计数据
  STATS_OVERVIEW: '/api/stats/overview',
  EFFICIENCY: '/api/efficiency',
  RECENT_ACTIVITIES: '/api/recent-activities',

  // 图表数据
  CHART: {
    CATEGORY_PIE: '/api/chart/category-pie',
    DAILY_BAR: '/api/chart/daily-bar',
    HEATMAP: '/api/chart/heatmap',
    TREND: '/api/chart/trend',
    DASHBOARD: '/api/chart/dashboard'
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
