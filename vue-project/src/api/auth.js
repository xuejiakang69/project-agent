import axios from 'axios'

const SESSION_KEY = 'vue-project:session'
const TOKEN_KEY = 'vue-project:token'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function getApiOrigin() {
  try {
    return new URL(API_BASE_URL, window.location.origin).origin
  } catch {
    return window.location.origin
  }
}

export function resolveMediaUrl(value) {
  if (!value) return ''
  if (/^(?:https?:|data:|blob:)/i.test(value)) return value

  const normalized = String(value).replace(/^\/+/, '')
  const path = normalized.startsWith('uploads/') ? normalized : `uploads/${normalized}`
  return `${getApiOrigin()}/${path}`
}

function normalizeUser(user) {
  return {
    ...user,
    displayName: user.name || user.displayName || user.username,
  }
}

function persistSession(user, token, remember) {
  const storage = remember ? window.localStorage : window.sessionStorage
  window.localStorage.removeItem(SESSION_KEY)
  window.localStorage.removeItem(TOKEN_KEY)
  window.sessionStorage.removeItem(SESSION_KEY)
  window.sessionStorage.removeItem(TOKEN_KEY)
  storage.setItem(SESSION_KEY, JSON.stringify(user))
  storage.setItem(TOKEN_KEY, token)
}

function getErrorMessage(error, fallback = '请求失败，请稍后重试') {
  const response = error?.response
  const detail = response?.data?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg).filter(Boolean)
    if (messages.length) return messages.join('；')
  }

  if (typeof response?.data?.message === 'string' && response.data.message.trim()) {
    return response.data.message
  }

  if (error?.request) {
    return '无法连接服务，请确认后端已启动'
  }

  return error?.message || fallback
}

function requestConfig() {
  return {
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
  }
}

function authHeaders() {
  const token = readToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function protectedRequestConfig(contentType = 'application/json') {
  return {
    timeout: 15000,
    headers: {
      ...authHeaders(),
      ...(contentType ? { 'Content-Type': contentType } : {}),
    },
  }
}

export async function login({ username, password, remember = true } = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/auth/login`,
      {
        username: String(username ?? '').trim(),
        password: String(password ?? ''),
      },
      requestConfig(),
    )

    const result = response.data
    const loginResult = result?.result

    if (result?.code !== 0 || !loginResult?.data || !loginResult.token) {
      throw new Error(result?.message || '登录响应格式不正确')
    }

    const user = normalizeUser(loginResult.data)
    persistSession(user, loginResult.token, remember)

    return user
  } catch (error) {
    throw new Error(getErrorMessage(error, '登录失败，请稍后重试'))
  }
}

export async function register(payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/user/register`,
      {
        name: String(payload.displayName ?? payload.name ?? '').trim(),
        email: String(payload.email ?? '').trim(),
        phone: String(payload.phone ?? '').trim(),
        username: String(payload.username ?? '').trim(),
        password: String(payload.password ?? ''),
      },
      requestConfig(),
    )

    const result = response.data
    const registeredUser = result?.result

    if (result?.code !== 0 || !registeredUser) {
      throw new Error(result?.message || '注册响应格式不正确')
    }

    return normalizeUser(registeredUser)
  } catch (error) {
    throw new Error(getErrorMessage(error, '注册失败，请稍后重试'))
  }
}

export async function updateProfile(payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/user/update`,
      {
        name: String(payload.name ?? '').trim() || null,
        email: String(payload.email ?? '').trim() || null,
        phone: String(payload.phone ?? '').trim() || null,
        avatar: String(payload.avatar ?? '').trim() || null,
      },
      protectedRequestConfig(),
    )

    const result = response.data
    const updatedUser = result?.result

    if (result?.code !== 0 || !updatedUser) {
      throw new Error(result?.message || '个人信息响应格式不正确')
    }

    const user = normalizeUser(updatedUser)
    persistSession(
      user,
      readToken(),
      Boolean(window.localStorage.getItem(TOKEN_KEY)),
    )

    return user
  } catch (error) {
    throw new Error(getErrorMessage(error, '个人信息更新失败，请稍后重试'))
  }
}

export async function uploadAvatar(file) {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
      `${API_BASE_URL}/file/upload`,
      formData,
      {
        timeout: 20000,
        headers: authHeaders(),
      },
    )

    const result = response.data
    const uploaded = result?.result

    if (result?.code !== 0 || !uploaded) {
      throw new Error(result?.message || '头像上传响应格式不正确')
    }

    const path = uploaded.disk_name || uploaded.url

    return {
      path,
      url: resolveMediaUrl(path),
    }
  } catch (error) {
    throw new Error(getErrorMessage(error, '头像上传失败，请稍后重试'))
  }
}

export async function listUsers({ page = 1, pageSize = 20, keyword = '' } = {}) {
  try {
    const normalizedKeyword = String(keyword ?? '').trim()
    const response = await axios.get(`${API_BASE_URL}/user/all`, {
      ...protectedRequestConfig(),
      params: {
        page: Number(page) || 1,
        page_size: Number(pageSize) || 20,
        ...(normalizedKeyword ? { keyword: normalizedKeyword } : {}),
      },
    })

    const result = response.data
    const pageResult = result?.result

    if (result?.code !== 0 || !pageResult || !Array.isArray(pageResult.items)) {
      throw new Error(result?.message || '用户列表响应格式不正确')
    }

    return {
      items: pageResult.items.map(normalizeUser),
      total: Number(pageResult.total) || 0,
      page: Number(pageResult.page) || Number(page) || 1,
      page_size: Number(pageResult.page_size) || Number(pageSize) || 20,
      total_pages: Number(pageResult.total_pages) || 0,
    }
  } catch (error) {
    throw new Error(getErrorMessage(error, '用户列表获取失败，请稍后重试'))
  }
}

export async function updateUserStatus({ id, status } = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/user/status`,
      {
        id: Number(id),
        status: Number(status),
      },
      protectedRequestConfig(),
    )

    const result = response.data
    const updatedUser = result?.result

    if (result?.code !== 0 || !updatedUser) {
      throw new Error(result?.message || '用户状态响应格式不正确')
    }

    return normalizeUser(updatedUser)
  } catch (error) {
    throw new Error(getErrorMessage(error, '用户状态更新失败，请稍后重试'))
  }
}

export function readToken() {
  return (
    window.localStorage.getItem(TOKEN_KEY) ||
    window.sessionStorage.getItem(TOKEN_KEY) ||
    null
  )
}

export function readSession() {
  const value =
    window.localStorage.getItem(SESSION_KEY) || window.sessionStorage.getItem(SESSION_KEY)

  if (!value || !readToken()) return null

  try {
    const user = JSON.parse(value)
    return user?.username ? user : null
  } catch {
    return null
  }
}

export function clearSession() {
  window.localStorage.removeItem(SESSION_KEY)
  window.localStorage.removeItem(TOKEN_KEY)
  window.sessionStorage.removeItem(SESSION_KEY)
  window.sessionStorage.removeItem(TOKEN_KEY)
}