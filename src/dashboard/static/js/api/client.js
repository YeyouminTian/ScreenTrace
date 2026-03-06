/**
 * API客户端
 * 统一管理所有API请求，支持缓存和错误处理
 */

class APIClient {
  constructor(baseURL = '') {
    this.baseURL = baseURL;
    this.cache = new Map();
    this.cacheTimeout = 5000; // 5秒缓存
  }

  /**
   * 发起API请求
   */
  async fetch(endpoint, options = {}) {
    const cacheKey = `${endpoint}-${JSON.stringify(options)}`;

    // 检查缓存
    if (this.cache.has(cacheKey)) {
      const { data, timestamp } = this.cache.get(cacheKey);
      if (Date.now() - timestamp < this.cacheTimeout) {
        console.log(`[APIClient] 缓存命中: ${endpoint}`);
        return data;
      }
    }

    try {
      console.log(`[APIClient] 请求: ${endpoint}`);
      const response = await fetch(`${this.baseURL}${endpoint}`, options);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.success) {
        // 缓存成功响应
        this.cache.set(cacheKey, {
          data: result.data,
          timestamp: Date.now()
        });
        return result.data;
      } else {
        throw new Error(result.error || 'API请求失败');
      }
    } catch (error) {
      console.error(`[APIClient] 请求失败 [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.cache.clear();
    console.log('[APIClient] 缓存已清除');
  }

  /**
   * 清除特定端点的缓存
   */
  clearEndpointCache(endpoint) {
    for (const key of this.cache.keys()) {
      if (key.startsWith(endpoint)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 批量请求
   */
  async fetchAll(endpoints) {
    const promises = endpoints.map(endpoint => this.fetch(endpoint));
    return Promise.all(promises);
  }

  /**
   * 带重试的请求
   */
  async fetchWithRetry(endpoint, options = {}, maxRetries = 3) {
    let lastError;

    for (let i = 0; i < maxRetries; i++) {
      try {
        return await this.fetch(endpoint, options);
      } catch (error) {
        lastError = error;
        console.warn(`[APIClient] 重试 ${i + 1}/${maxRetries}: ${endpoint}`);

        // 指数退避
        await new Promise(resolve =>
          setTimeout(resolve, Math.pow(2, i) * 1000)
        );
      }
    }

    throw lastError;
  }
}

// 导出单例
export const apiClient = new APIClient();
