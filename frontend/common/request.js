// common/request.js
import { ensureAccessToken, clearTokens } from './auth.js';

// 建议：BASE_URL 不以斜杠结尾，后续统一拼接
const BASE_URL = "/crm/api";

/**
 * @description 统一拼接 URL，避免重复或缺失斜杠
 * @param {string} base - 基础 URL
 * @param {string} path - 路径
 * @returns {string} - 拼接后的完整 URL
 */
function joinURL(base, path) {
  return base.replace(/\/+$/, '') + '/' + String(path || '').replace(/^\/+/, '');
}

/**
 * @description 基础请求：不做鉴权，供刷新 token 和裸请求使用
 */
function baseRequest(url, method = "GET", data = {}, headers = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: joinURL(BASE_URL, url),
      method,
      data,
      header: {
        "Content-Type": "application/json",
        ...headers, // ✅ 正确展开
      },
      success: (res) => {
        const { statusCode, data } = res;
        if (statusCode >= 200 && statusCode < 300) {
          resolve(data);
        } else {
          reject(res);
        }
      },
      fail: reject
    });
  });
}

/**
 * @description 鉴权请求：自动处理 Access Token、刷新及 401 重试
 * @param {string} url - 请求路径
 * @param {string} method - 请求方法
 * @param {object} data - 请求体数据
 * @param {object} headers - 自定义请求头
 * @param {object} opts - 配置项，如 { authFree: true } 表示无需鉴权
 * @returns {Promise<any>}
 */
async function request(url, method = "GET", data = {}, headers = {}, opts = {}) {
  const isAuthFree = opts.authFree === true; // 登录/注册这类无需 token
  let token = null;

  if (!isAuthFree) {
    try {
      token = await ensureAccessToken(baseRequest);
    } catch (_) {
      token = null; // 获取 token 失败，后续请求将不带 token
    }
  }

  const authHeader = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    // 第一次请求
    return await baseRequest(url, method, data, { ...authHeader, ...headers });
  } catch (err) {
    // 若 401，且需要鉴权，则尝试刷新后重试一次
    if (!isAuthFree && err && err.statusCode === 401) {
      try {
        const newToken = await ensureAccessToken(baseRequest); // 再次强制刷新
        const retryHeader = newToken ? { Authorization: `Bearer ${newToken}` } : {};
        return await baseRequest(url, method, data, { ...retryHeader, ...headers });
      } catch (e2) {
        clearTokens(); // 刷新失败，清理本地态
        // 可选：跳转登录页
        // uni.reLaunch({ url: '/pages/auth/auth' });
        throw e2;
      }
    }
    // 其他错误或无需重试的 401，直接抛出
    throw err;
  }
}

export default request;
export { baseRequest };
