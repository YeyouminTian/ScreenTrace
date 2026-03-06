/**
 * 应用状态管理器
 * 采用发布-订阅模式，实现响应式状态更新
 */

class AppState {
  constructor() {
    // 应用状态
    this.state = {
      timeRange: 1,
      autoRefresh: true,
      refreshInterval: 10,
      theme: 'light',
      cardOrder: ['totalCount', 'mainCategory', 'topApp', 'deepWork'],
      loading: {
        recentActivities: false,
        statsOverview: false,
        categoryPie: false,
        dailyBar: false,
        heatmap: false,
        trend: false,
        appUsage: false
      },
      data: {
        recentActivities: null,
        statsOverview: null,
        efficiency: null
      }
    };

    // 订阅者映射
    this.subscribers = new Map();
  }

  /**
   * 获取状态值
   */
  get(key) {
    return key.split('.').reduce((obj, k) => obj?.[k], this.state);
  }

  /**
   * 设置状态值
   */
  set(key, value) {
    const oldValue = this.get(key);

    // 更新嵌套状态
    const keys = key.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((obj, k) => obj[k], this.state);
    target[lastKey] = value;

    // 通知订阅者
    this.notify(key, value, oldValue);
  }

  /**
   * 订阅状态变化
   */
  subscribe(key, callback) {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    this.subscribers.get(key).add(callback);

    // 返回取消订阅函数
    return () => {
      this.subscribers.get(key).delete(callback);
    };
  }

  /**
   * 通知订阅者
   */
  notify(key, newValue, oldValue) {
    if (this.subscribers.has(key)) {
      this.subscribers.get(key).forEach(callback => {
        try {
          callback(newValue, oldValue);
        } catch (error) {
          console.error(`状态订阅者回调失败 [${key}]:`, error);
        }
      });
    }
  }

  /**
   * 批量更新状态
   */
  batchUpdate(updates) {
    Object.entries(updates).forEach(([key, value]) => {
      this.set(key, value);
    });
  }

  /**
   * 重置状态
   */
  reset(key) {
    const defaultState = new AppState().state;
    if (key) {
      const keys = key.split('.');
      const lastKey = keys.pop();
      const target = keys.reduce((obj, k) => obj[k], this.state);
      target[lastKey] = defaultState[key];
    } else {
      this.state = defaultState;
    }
  }

  /**
   * 导出状态（用于调试）
   */
  export() {
    return JSON.parse(JSON.stringify(this.state));
  }
}

// 导出单例
export const appState = new AppState();
