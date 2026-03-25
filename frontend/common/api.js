// common/api.js
import request from './request.js';
import { setTokens, clearTokens } from './auth.js';

// --- 认证模块 ---

/**
 * @description 登录（免鉴权）
 */
export async function login(data) {
  const res = await request("/login/", "POST", data, {}, { authFree: true });
  // 兼容不同字段名
  const access = res.access || res.token || res.access_token;
  const refresh = res.refresh || res.refresh_token;
  if (access) {
    setTokens({ access, refresh });
  }
  return res;
}

/**
 * @description 注册（免鉴权）
 */
export function register(data) {
  return request("/register/", "POST", data, {}, { authFree: true });
}

/**
 * @description 登出（带鉴权，并清除本地 Token）
 */
export async function logout() {
  try {
    await request("/logout/", "POST");
  } finally {
    clearTokens();
  }
}

// --- 用户管理 (Users) ---

export function user_view(data) { // data 参数用于查询条件、分页等
  return request("/permission/users/", "GET", data);
}

export function user_create(data) {
  return request("/permission/users/", "POST", data);
}

export function user_view_id(userId) {
  return request(`/permission/users/${userId}/`, "GET");
}

export function user_update(userId, data) {
  return request(`/permission/users/${userId}/`, "PATCH", data);
}

export function user_del(userId) {
  return request(`/permission/users/${userId}/`, "DELETE");
}

// --- 角色/组管理 (Groups) ---

export function groups_view(data) { // data 参数用于查询条件、分页等
  return request("/permission/groups/", "GET", data);
}

export function groups_create(data) {
  return request("/permission/groups/", "POST", data);
}

export function groups_view_id(groupId) {
  return request(`/permission/groups/${groupId}/`, "GET");
}

export function groups_update(groupId, data) {
  return request(`/permission/groups/${groupId}/`, "PATCH", data);
}

export function groups_del(groupId) {
  return request(`/permission/groups/${groupId}/`, "DELETE");
}

// --- 客户管理 (Customers) ---

export function customer_view(data) {
  return request(`/customer/customers/`, "GET", data);
}

export function customer_create(data) {
  return request("/customer/customers/", "POST", data);
}

export function customer_view_id(customerId) {
  return request(`/customer/customers/${customerId}/`, "GET");
}

export function customer_update(customerId, data) {
  return request(`/customer/customers/${customerId}/`, "PATCH", data);
}

export function customer_del(customerId) {
  return request(`/customer/customers/${customerId}/`, "DELETE");
}


// --- 项目管理 (Projects) ---

export function project_view(data) {
  return request(`/project/projects/`, "GET", data);
}

export function project_create(data) {
  return request("/project/projects/", "POST", data);
}

export function project_view_id(projectId) {
  return request(`/project/projects/${projectId}/`, "GET");
}

export function project_update(projectId, data) {
  return request(`/project/projects/${projectId}/`, "PATCH", data);
}

export function project_del(projectId) {
  return request(`/project/projects/${projectId}/`, "DELETE");
}

// --- 行动记录 (Activities) ---

export function activity_view(data) {
  return request(`/project/activities/`, "GET", data);
}

export function activity_create(data) {
  return request("/project/activities/", "POST", data);
}

export function activity_view_id(activityId) {
  return request(`/project/activities/${activityId}/`, "GET");
}

export function activity_update(activityId, data) {
  return request(`/project/activities/${activityId}/`, "PATCH", data);
}

export function activity_del(activityId) {
  return request(`/project/activities/${activityId}/`, "DELETE");
}

// --- 项目阶段 (ProjectStage) ---

export function stage_view(data) {
  return request(`/project/stages/`, "GET", data);
}


/**
 * @param {Object} params
 * @param {string} [params.message] - 单条用户输入（兼容旧接口）
 * @param {Array<{role: 'user'|'ai'|'assistant'|'system', content: string}>} [params.messages] - 全量对话历史（推荐）
 * @param {string|null} [params.conversationId]
 */
export async function aiChat({ message, messages, conversationId = null } = {}) {
  const data = {
    conversation_id: conversationId,
  };

  if (Array.isArray(messages) && messages.length > 0) {
    data.messages = messages;
    // 兼容后端仍然只读 message/query 的情况
    const lastUser = [...messages].reverse().find(m => m && m.role === "user" && (m.content || "").trim());
    if (lastUser) data.message = (lastUser.content || "").trim();
  } else {
    data.message = message;
  }

  // 默认走鉴权（如确实免鉴权，再在调用方传 opts 或改这里）
  return request("/aihelper/ai/chat/", "POST", data);
}