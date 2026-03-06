/**
 * 应用主入口
 * 初始化所有模块，启动应用
 */

import { appState } from './state.js';
import { apiClient } from './api/client.js';
import { API_ENDPOINTS, buildURL } from './api/endpoints.js';
import { initTheme, toggleTheme } from './utils/theme.js';
import { showToast, showSuccess, showError } from './utils/toast.js';

class App {
  constructor() {
    this.autoRefreshTimer = null;
    this.isInitialized = false;
  }

  /**
   * 初始化应用
   */
  async init() {
    if (this.isInitialized) {
      console.warn('[App] 应用已初始化');
      return;
    }

    console.log('[App] 开始初始化...');

    try {
      // 1. 初始化主题
      const theme = initTheme();
      console.log(`[App] 主题: ${theme}`);

      // 2. 加载数据
      await this.loadAllData();

      // 3. 设置自动刷新
      this.setupAutoRefresh();

      // 4. 设置主题切换监听
      this.setupThemeToggle();

      // 5. 设置滚动观察器（图表入场动画）
      this.setupScrollObserver();

      this.isInitialized = true;
      console.log('[App] 初始化完成');

      showSuccess('应用加载成功');

    } catch (error) {
      console.error('[App] 初始化失败:', error);
      showError('应用初始化失败');
    }
  }

  /**
   * 加载所有数据
   */
  async loadAllData() {
    const days = appState.get('timeRange');

    // 并行加载所有数据
    const promises = [
      this.loadRecentActivities(),
      this.loadStatsOverview(days),
      this.loadCategoryPieChart(days),
      this.loadDailyBarChart(days),
      this.loadHeatmapChart(days),
      this.loadTrendChart(days),
      this.loadAppUsageChart(days)
    ];

    await Promise.allSettled(promises);
    this.updateLastUpdateTime();
  }

  /**
   * 加载最近活动
   */
  async loadRecentActivities() {
    const container = document.getElementById('recentActivityList');

    try {
      appState.set('loading.recentActivities', true);

      const data = await apiClient.fetch(
        buildURL(API_ENDPOINTS.RECENT_ACTIVITIES, { limit: 10 })
      );

      if (data && data.length >= 0) {
        this.renderRecentActivities(data);
        appState.set('data.recentActivities', data);
      }

    } catch (error) {
      container.innerHTML = '<div class="error">加载失败</div>';
      showError('加载最近活动失败');
    } finally {
      appState.set('loading.recentActivities', false);
    }
  }

  /**
   * 渲染最近活动
   */
  renderRecentActivities(activities) {
    const container = document.getElementById('recentActivityList');

    if (activities.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: var(--spacing-2xl); color: var(--color-text-tertiary);">
          暂无活动数据
        </div>
      `;
      return;
    }

    const html = activities.map(activity => {
      const time = activity.timestamp.substring(11, 19);
      const date = activity.timestamp.substring(0, 10);
      const icon = this.getCategoryIcon(activity.category);

      return `
        <article class="stat-card" style="padding: var(--spacing-lg); cursor: pointer;">
          <div style="display: grid; grid-template-columns: auto 1fr auto; gap: var(--spacing-lg); align-items: center;">
            <div style="text-align: center; min-width: 80px;">
              <div style="font-size: var(--text-2xl); margin-bottom: var(--spacing-xs);">${icon}</div>
              <div style="font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-tertiary);">${time}</div>
            </div>

            <div>
              <div style="font-weight: var(--font-semibold); font-size: var(--text-lg); margin-bottom: var(--spacing-xs); color: var(--color-text-primary);">
                ${activity.app}
              </div>
              <div style="font-size: var(--text-sm); color: var(--color-text-secondary); margin-bottom: var(--spacing-xs);">
                ${activity.description || '无描述'}
              </div>
              <div style="font-size: var(--text-xs); color: var(--color-text-tertiary);">
                ${activity.form || 'N/A'}
              </div>
            </div>

            <div style="text-align: right;">
              <span style="
                display: inline-block;
                padding: var(--spacing-xs) var(--spacing-md);
                background: var(--color-bg-secondary);
                border-radius: var(--radius-full);
                font-size: var(--text-sm);
                font-weight: var(--font-medium);
                color: var(--color-primary);
              ">
                ${activity.category}
              </span>
            </div>
          </div>
        </article>
      `;
    }).join('');

    container.innerHTML = html;
  }

  /**
   * 获取分类图标
   */
  getCategoryIcon(category) {
    const icons = {
      '工作': '💼',
      '学习': '📚',
      '休闲': '🎮',
      '生活': '🏠'
    };
    return icons[category] || '📌';
  }

  /**
   * 加载统计概览
   */
  async loadStatsOverview(days) {
    try {
      const data = await apiClient.fetch(
        buildURL(API_ENDPOINTS.STATS_OVERVIEW, { days })
      );

      if (data) {
        this.updateStatsCards(data);
        appState.set('data.statsOverview', data);
      }

      // 加载效率指标
      await this.loadEfficiencyMetrics(days);

    } catch (error) {
      console.error('加载统计概览失败:', error);
      showError('加载统计数据失败');
    }
  }

  /**
   * 更新统计卡片
   */
  updateStatsCards(data) {
    document.getElementById('totalCount').textContent = data.total_records || 0;

    // 主要活动
    if (data.life_category) {
      const mainCategory = Object.entries(data.life_category)
        .sort((a, b) => b[1] - a[1])[0];
      document.getElementById('mainCategory').textContent =
        mainCategory ? mainCategory[0] : '-';
    }

    // 常用应用
    if (data.top_apps) {
      const topApp = Object.keys(data.top_apps)[0];
      document.getElementById('topApp').textContent = topApp || '-';
    }
  }

  /**
   * 加载效率指标
   */
  async loadEfficiencyMetrics(days) {
    try {
      const data = await apiClient.fetch(
        buildURL(API_ENDPOINTS.EFFICIENCY, { days })
      );

      if (data) {
        document.getElementById('deepWork').textContent =
          data.deep_work_sessions || 0;
        appState.set('data.efficiency', data);
      }
    } catch (error) {
      console.error('加载效率指标失败:', error);
    }
  }

  /**
   * 加载图表（通用方法）
   */
  async loadChart(chartId, endpoint, params) {
    const container = document.getElementById(chartId);

    try {
      // 显示骨架屏
      container.innerHTML = '<div class="skeleton skeleton-chart"></div>';

      const response = await fetch(buildURL(endpoint, params));
      const html = await response.text();

      container.innerHTML = html;
      this.executeScripts(container);

    } catch (error) {
      container.innerHTML = '<div class="error">加载失败</div>';
      console.error(`加载图表失败 [${chartId}]:`, error);
    }
  }

  // 各个图表加载方法
  loadCategoryPieChart(days) {
    return this.loadChart('categoryPieChart', API_ENDPOINTS.CHART.CATEGORY_PIE, { days });
  }

  loadDailyBarChart(days) {
    return this.loadChart('dailyBarChart', API_ENDPOINTS.CHART.DAILY_BAR, { days });
  }

  loadHeatmapChart(days) {
    return this.loadChart('heatmapChart', API_ENDPOINTS.CHART.HEATMAP, { days });
  }

  loadTrendChart(days) {
    return this.loadChart('trendChart', API_ENDPOINTS.CHART.TREND, { days });
  }

  loadAppUsageChart(days) {
    return this.loadChart('appUsageChart', API_ENDPOINTS.CHART.DASHBOARD, { days });
  }

  /**
   * 执行容器内的script标签
   */
  executeScripts(container) {
    const scripts = container.querySelectorAll('script');
    scripts.forEach(oldScript => {
      const newScript = document.createElement('script');
      if (oldScript.src) {
        newScript.src = oldScript.src;
      } else {
        newScript.textContent = oldScript.textContent;
      }
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  }

  /**
   * 设置自动刷新
   */
  setupAutoRefresh() {
    const checkbox = document.getElementById('autoRefresh');
    const intervalSelect = document.getElementById('refreshInterval');
    const timeRangeSelect = document.getElementById('timeRange');
    const refreshBtn = document.getElementById('refreshBtn');

    // 手动刷新按钮
    if (refreshBtn) {
      refreshBtn.addEventListener('click', async () => {
        const btnText = refreshBtn.innerHTML;
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" class="spin">
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-dashoffset="32"/>
          </svg>
          刷新中...
        `;

        await this.loadAllData();
        showSuccess('数据已刷新');

        refreshBtn.disabled = false;
        refreshBtn.innerHTML = btnText;
      });
    }

    // 监听checkbox变化
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        this.startAutoRefresh();
        showSuccess('已开启自动刷新');
      } else {
        this.stopAutoRefresh();
        showSuccess('已关闭自动刷新');
      }
    });

    // 监听刷新间隔变化
    intervalSelect.addEventListener('change', () => {
      appState.set('refreshInterval', parseInt(intervalSelect.value));
      if (checkbox.checked) {
        this.stopAutoRefresh();
        this.startAutoRefresh();
      }
    });

    // 监听时间范围变化
    timeRangeSelect.addEventListener('change', () => {
      const days = parseInt(timeRangeSelect.value);
      appState.set('timeRange', days);
      this.loadAllData();
    });

    // 初始启动自动刷新
    if (checkbox.checked) {
      this.startAutoRefresh();
    }
  }

  /**
   * 启动自动刷新
   */
  startAutoRefresh() {
    const interval = appState.get('refreshInterval');
    this.autoRefreshTimer = setInterval(() => {
      this.loadAllData();
    }, interval * 1000);
  }

  /**
   * 停止自动刷新
   */
  stopAutoRefresh() {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
      this.autoRefreshTimer = null;
    }
  }

  /**
   * 设置主题切换
   */
  setupThemeToggle() {
    const themeToggleBtn = document.getElementById('themeToggle');

    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const newTheme = toggleTheme();
        showSuccess(newTheme === 'dark' ? '已切换到暗色模式' : '已切换到浅色模式');
      });
    }
  }

  /**
   * 设置滚动观察器（图表入场动画）
   */
  setupScrollObserver() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    });

    document.querySelectorAll('.chart-container, .stat-card').forEach(el => {
      observer.observe(el);
    });
  }

  /**
   * 更新最后更新时间
   */
  updateLastUpdateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) {
      lastUpdate.textContent = `最后更新: ${timeStr}`;
    }
  }
}

// 创建应用实例
const app = new App();

// 页面加载时初始化
window.onload = () => {
  console.log('[App] Window loaded, Plotly available:', typeof Plotly !== 'undefined');
  app.init();
};

// 导出供全局使用
window.app = app;
window.toggleTheme = () => toggleTheme();
