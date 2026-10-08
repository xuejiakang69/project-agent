import axios from 'axios'

import { readToken } from '@/api/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

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
  const token = readToken()

  return {
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  }
}

function normalizePayload(payload = {}) {
  const normalizeText = (value) => {
    const text = String(value ?? '').trim()
    return text || null
  }

  return {
    name: String(payload.name ?? '').trim(),
    description: normalizeText(payload.description),
    status: Number(payload.status) === 0 ? 0 : 1,
    location: normalizeText(payload.location),
    open_time: normalizeText(payload.open_time),
    close_time: normalizeText(payload.close_time),
    capacity:
      payload.capacity === null || payload.capacity === '' || payload.capacity === undefined
        ? null
        : Number(payload.capacity),
  }
}

function normalizeUpdatePayload(payload = {}) {
  return {
    name: String(payload.name ?? '').trim() || null,
    description: payload.description === '' ? null : payload.description,
    status: Number(payload.status) === 0 ? 0 : 1,
    location: payload.location === '' ? null : payload.location,
    open_time: payload.open_time === '' ? null : payload.open_time,
    close_time: payload.close_time === '' ? null : payload.close_time,
    capacity:
      payload.capacity === null || payload.capacity === '' || payload.capacity === undefined
        ? null
        : Number(payload.capacity),
  }
}

function normalizeLab(lab) {
  return {
    ...lab,
    id: Number(lab.id),
    status: Number(lab.status) === 0 ? 0 : 1,
    capacity: lab.capacity === null ? null : Number(lab.capacity),
    description: lab.description || '',
    location: lab.location || '',
    open_time: lab.open_time || '',
    close_time: lab.close_time || '',
  }
}

function validateLabResponse(result, fallbackMessage) {
  const lab = result?.result

  if (result?.code !== 0 || !lab?.id) {
    throw new Error(result?.message || fallbackMessage)
  }

  return normalizeLab(lab)
}

export async function listLabs({ page = 1, pageSize = 10, keyword = '' } = {}) {
  try {
    const normalizedKeyword = String(keyword ?? '').trim()
    const response = await axios.get(`${API_BASE_URL}/lab/list`, {
      ...requestConfig(),
      params: {
        page: Number(page) || 1,
        page_size: Number(pageSize) || 10,
        ...(normalizedKeyword ? { keyword: normalizedKeyword } : {}),
      },
    })

    const result = response.data
    const pageResult = result?.result

    if (result?.code !== 0 || !pageResult || !Array.isArray(pageResult.items)) {
      throw new Error(result?.message || '实验室列表响应格式不正确')
    }

    return {
      items: pageResult.items.map(normalizeLab),
      total: Number(pageResult.total) || 0,
      page: Number(pageResult.page) || Number(page) || 1,
      page_size: Number(pageResult.page_size) || Number(pageSize) || 10,
      total_pages: Number(pageResult.total_pages) || 0,
    }
  } catch (error) {
    throw new Error(getErrorMessage(error, '实验室列表获取失败，请稍后重试'))
  }
}

export async function createLab(payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/lab/create`,
      normalizePayload(payload),
      requestConfig(),
    )

    return validateLabResponse(response.data, '实验室创建响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '实验室创建失败，请稍后重试'))
  }
}

export async function updateLab(id, payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/lab/update/${Number(id)}`,
      normalizeUpdatePayload(payload),
      requestConfig(),
    )

    return validateLabResponse(response.data, '实验室更新响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '实验室更新失败，请稍后重试'))
  }
}

export async function deleteLab(id) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/lab/delete/${Number(id)}`,
      {},
      requestConfig(),
    )

    const result = response.data

    if (result?.code !== 0 || result?.result !== true) {
      throw new Error(result?.message || '实验室删除响应格式不正确')
    }

    return true
  } catch (error) {
    throw new Error(getErrorMessage(error, '实验室删除失败，请稍后重试'))
  }
}