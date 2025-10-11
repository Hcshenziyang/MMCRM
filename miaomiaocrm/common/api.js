// common/api.js
import request from './request.js';
import { setTokens, clearTokens } from './auth.js';

// 登录（免鉴权）
export async function login(data) {
  const res = await request("/login/", "POST", data, {}, { authFree: true });
  // 兼容不同字段名
  const access = res.access || res.token || res.access_token;
  const refresh = res.refresh || res.refresh_token;
  if (access) setTokens({ access, refresh });
  return res;
}

// 注册（免鉴权）
export function register(data) {
  return request("/register/", "POST", data, {}, { authFree: true });
}

// 登出（带鉴权，且清除本地态）
export async function logout() {
  try {
    await request("/logout/", "POST");
  } finally {
    clearTokens();
  }
}

// 用户增删改查
export async function user_view(data) { // data参数用于查询条件、分页等
  return await request("/permission/users/", "GET", data);
}

export async function user_create(data) {
  return await request("/permission/users/", "POST", data);
}

export async function user_view_id(userId) {
  return await request(`/permission/users/${userId}/`, "GET");
}

export async function user_update(userId, data) {
  return await request(`/permission/users/${userId}/`, "PATCH", data);
}

export async function user_del(userId) {
  return await request(`/permission/users/${userId}/`, "DELETE");
}

// 角色（组）增删改查
// 展示完整角色+用户+权限
export async function groups_view(data) { // data参数用于查询条件、分页等
  return await request("/permission/groups/", "GET", data);
}

export async function groups_create(data) {
  return await request("/permission/groups/", "POST", data);
}

export async function groups_view_id(groupId) { // 注意这里命名为 groupId 更规范
  return await request(`/permission/groups/${groupId}/`, "GET");
}

export async function groups_update(groupId, data) {
  return await request(`/permission/groups/${groupId}/`, "PATCH", data);
}

export async function groups_del(groupId) {
  return await request(`/permission/groups/${groupId}/`, "DELETE");
}

// 客户增删改查
export async function customer_view(data) {
  return await request(`/customer/customers/`, "GET", data);
}

export async function customer_create(data) {
  return await request("/customer/customers/", "POST", data);
}

export async function customer_view_id(customerId) {
  return await request(`/customer/customers/${customerId}/`, "GET");
}

export async function customer_update(customerId, data) {
  return await request(`/customer/customers/${customerId}/`, "PATCH", data);
}

export async function customer_del(customerId) {
  return await request(`/customer/customers/${customerId}/`, "DELETE");
}