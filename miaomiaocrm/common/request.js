// common/request.js
import { ensureAccessToken, clearTokens } from './auth.js';

// 建议：BASE_URL 不以斜杠结尾，后续统一拼接
const BASE_URL = "http://127.0.0.1:8000";

// 统一拼接，避免重复/缺失斜杠
function joinURL(base, path) {
  return base.replace(/\/+$/, '') + '/' + String(path || '').replace(/^\/+/, '');
}

// 基础请求：不做鉴权，供刷新 token 和裸请求使用
function baseRequest(url, method = "GET", data = {}, headers = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: joinURL(BASE_URL, url),
      method,
      data,
      header: {
        "Content-Type": "application/json",
        ...headers,              // ✅ 正确展开
      },
      success: (res) => {
        const { statusCode, data } = res;
        if (statusCode >= 200 && statusCode < 300) resolve(data);
        else reject(res);
      },
      fail: reject
    });
  });
}

// 鉴权 + 自动刷新 + 401 重试一次
async function request(url, method = "GET", data = {}, headers = {}, opts = {}) {
  const isAuthFree = opts.authFree === true;  // 登录/注册这类无需 token
  let token = null;

  if (!isAuthFree) {
    try {
      token = await ensureAccessToken(baseRequest);
    } catch (_) {
      token = null;
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
        clearTokens();            // 刷新失败，清理本地态
        // 可选：跳转登录页
        // uni.reLaunch({ url: '/pages/auth/auth' });
        throw e2;
      }
    }
    throw err;
  }
}

export default request;
export { baseRequest };
