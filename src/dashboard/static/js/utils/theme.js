/**
 * 主题管理工具
 */

const THEME_KEY = 'screentrace-theme';

/**
 * 初始化主题
 */
export function initTheme() {
  const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
  applyTheme(savedTheme);
  return savedTheme;
}

/**
 * 切换主题
 */
export function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

  applyTheme(newTheme);
  localStorage.setItem(THEME_KEY, newTheme);

  return newTheme;
}

/**
 * 应用主题
 */
export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  updateThemeIcon(theme);

  // 触发主题变化事件
  window.dispatchEvent(new CustomEvent('themechange', {
    detail: { theme }
  }));
}

/**
 * 更新主题图标
 */
export function updateThemeIcon(theme) {
  const icon = document.querySelector('.theme-icon');
  if (icon) {
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
}

/**
 * 获取当前主题
 */
export function getCurrentTheme() {
  return document.documentElement.getAttribute('data-theme') || 'light';
}

/**
 * 监听系统主题变化
 */
export function watchSystemTheme() {
  if (!window.matchMedia) return;

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  mediaQuery.addEventListener('change', (e) => {
    const savedTheme = localStorage.getItem(THEME_KEY);
    // 如果用户没有手动设置过主题，则跟随系统
    if (!savedTheme) {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });
}
