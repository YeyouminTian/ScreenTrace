/**
 * Toast通知工具
 */

let toastContainer = null;

/**
 * 显示Toast通知
 */
export function showToast(message, duration = 3000, type = 'info') {
  // 创建容器（如果不存在）
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 1080;
      display: flex;
      flex-direction: column;
      gap: 10px;
    `;
    document.body.appendChild(toastContainer);
  }

  // 创建Toast元素
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  // 添加到容器
  toastContainer.appendChild(toast);

  // 自动移除
  setTimeout(() => {
    toast.classList.add('fadeOut');
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }

      // 如果没有Toast了，移除容器
      if (toastContainer && toastContainer.children.length === 0) {
        document.body.removeChild(toastContainer);
        toastContainer = null;
      }
    }, 300);
  }, duration);

  return toast;
}

/**
 * 成功通知
 */
export function showSuccess(message, duration) {
  return showToast(message, duration, 'success');
}

/**
 * 错误通知
 */
export function showError(message, duration) {
  return showToast(message, duration, 'error');
}

/**
 * 警告通知
 */
export function showWarning(message, duration) {
  return showToast(message, duration, 'warning');
}

/**
 * 信息通知
 */
export function showInfo(message, duration) {
  return showToast(message, duration, 'info');
}
