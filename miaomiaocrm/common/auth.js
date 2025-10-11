// common/auth.js
const ACCESS_KEY = 'ACCESS_TOKEN';
const REFRESH_KEY = 'REFRESH_TOKEN';
const REFRESH_URL = '/refresh/';

let refreshing = false;
let waitQueue = []; // 等待刷新完成后继续发请求

function b64urlDecode(str) {
  // 兼容小程序/H5
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  const pad = str.length % 4;
  if (pad) str += '='.repeat(4 - pad);
  try {
    const decoded = decodeURIComponent(escape(atob(str)));
    return decoded;
  } catch (e) {
    // 某些端没有 atob
    const base64 = typeof uni !== 'undefined' && uni.base64ToArrayBuffer
      ? String.fromCharCode.apply(null, new Uint8Array(uni.base64ToArrayBuffer(str)))
      : '';
    return base64;
  }
}

function decodeJWT(token) {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const json = b64urlDecode(payload);
    return JSON.parse(json);
  } catch (e) {
    return null;
  }
}

export function getTokens() {
  return {
    access: uni.getStorageSync(ACCESS_KEY) || '',
    refresh: uni.getStorageSync(REFRESH_KEY) || ''
  };
}

export function setTokens({ access, refresh }) {
  if (access) uni.setStorageSync(ACCESS_KEY, access);
  if (refresh) uni.setStorageSync(REFRESH_KEY, refresh);
}

export function clearTokens() {
  uni.removeStorageSync(ACCESS_KEY);
  uni.removeStorageSync(REFRESH_KEY);
}

function willExpireSoon(token, leadSeconds = 60) {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return false; // 解不出来就先当作不过期
  const now = Math.floor(Date.now() / 1000);
  return payload.exp - now <= leadSeconds;
}

// 发起真正的刷新请求
function doRefreshToken(baseRequest) {
  const { refresh } = getTokens();
  if (!refresh) return Promise.reject(new Error('NO_REFRESH_TOKEN'));

  return baseRequest(REFRESH_URL, 'POST', { refresh })
    .then(res => {
      // 兼容两种返回：{access, refresh?} 或 {access}
      const access = res.access || res.token || res.access_token;
      const newRefresh = res.refresh || refresh;
      if (!access) throw new Error('NO_ACCESS_IN_REFRESH_RESPONSE');
      setTokens({ access, refresh: newRefresh });
      return access;
    });
}

// 确保 access 可用；必要时刷新（单飞）
export function ensureAccessToken(baseRequest) {
  const { access } = getTokens();

  // 没登录态
  if (!access) return Promise.resolve(null);

  // 不到期，直接用
  if (!willExpireSoon(access, 30)) return Promise.resolve(access);

  // 到期/将到期 -> 刷新
  if (refreshing) {
    // 已在刷新：把当前请求放入队列，等待刷新完拿新 token
    return new Promise((resolve, reject) => {
      waitQueue.push({ resolve, reject });
    });
  }

  refreshing = true;
  return doRefreshToken(baseRequest)
    .then(newAccess => {
      refreshing = false;
      // 唤醒队列
      waitQueue.forEach(p => p.resolve(newAccess));
      waitQueue = [];
      return newAccess;
    })
    .catch(err => {
      refreshing = false;
      waitQueue.forEach(p => p.reject(err));
      waitQueue = [];
      clearTokens();
      return Promise.reject(err);
    });
}
