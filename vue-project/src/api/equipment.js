import axios from 'axios'

import { readToken, resolveMediaUrl } from '@/api/auth'

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

function authHeaders() {
  const token = readToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function requestConfig() {
  return {
    timeout: 15000,
    headers: {
      ...authHeaders(),
      'Content-Type': 'application/json',
    },
  }
}

function normalizeText(value) {
  return String(value ?? '').trim() || null
}

function normalizePayload(payload = {}) {
  return {
    lab_id: Number(payload.lab_id),
    name: String(payload.name ?? '').trim(),
    description: normalizeText(payload.description),
    img: normalizeText(payload.img),
    spec: normalizeText(payload.spec),
    quantity: Number(payload.quantity),
    status: Number(payload.status) === 0 ? 0 : 1,
  }
}

function normalizeEquipment(equipment) {
  return {
    ...equipment,
    id: Number(equipment.id),
    lab_id: Number(equipment.lab_id),
    lab_name: equipment.lab_name || '',
    description: equipment.description || '',
    img: equipment.img || '',
    spec: equipment.spec || '',
    quantity: Number(equipment.quantity),
    status: Number(equipment.status) === 0 ? 0 : 1,
  }
}

function validateEquipmentResponse(result, fallbackMessage) {
  const equipment = result?.result

  if (result?.code !== 0 || !equipment?.id) {
    throw new Error(result?.message || fallbackMessage)
  }

  return normalizeEquipment(equipment)
}

export async function listEquipments({ page = 1, pageSize = 10, keyword = '', labId = null } = {}) {
  try {
    const normalizedKeyword = String(keyword ?? '').trim()
    const response = await axios.get(`${API_BASE_URL}/equipment/list`, {
      ...requestConfig(),
      params: {
        page: Number(page) || 1,
        page_size: Number(pageSize) || 10,
        ...(normalizedKeyword ? { keyword: normalizedKeyword } : {}),
        ...(labId ? { lab_id: Number(labId) } : {}),
      },
    })

    const result = response.data
    const pageResult = result?.result

    if (result?.code !== 0 || !pageResult || !Array.isArray(pageResult.items)) {
      throw new Error(result?.message || '设备列表响应格式不正确')
    }

    return {
      items: pageResult.items.map(normalizeEquipment),
      total: Number(pageResult.total) || 0,
      page: Number(pageResult.page) || Number(page) || 1,
      page_size: Number(pageResult.page_size) || Number(pageSize) || 10,
      total_pages: Number(pageResult.total_pages) || 0,
    }
  } catch (error) {
    throw new Error(getErrorMessage(error, '设备列表获取失败，请稍后重试'))
  }
}

export async function createEquipment(payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/equipment/create`,
      normalizePayload(payload),
      requestConfig(),
    )

    return validateEquipmentResponse(response.data, '设备创建响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '设备创建失败，请稍后重试'))
  }
}

export async function updateEquipment(id, payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/equipment/update/${Number(id)}`,
      normalizePayload(payload),
      requestConfig(),
    )

    return validateEquipmentResponse(response.data, '设备更新响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '设备更新失败，请稍后重试'))
  }
}

export async function deleteEquipment(id) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/equipment/delete/${Number(id)}`,
      {},
      requestConfig(),
    )

    const result = response.data

    if (result?.code !== 0 || result?.result !== true) {
      throw new Error(result?.message || '设备删除响应格式不正确')
    }

    return true
  } catch (error) {
    throw new Error(getErrorMessage(error, '设备删除失败，请稍后重试'))
  }
}

export async function uploadEquipmentImage(file) {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE_URL}/file/upload`, formData, {
      timeout: 20000,
      headers: authHeaders(),
    })

    const result = response.data
    const uploaded = result?.result

    if (result?.code !== 0 || !uploaded) {
      throw new Error(result?.message || '设备图片上传响应格式不正确')
    }

    const path = uploaded.disk_name || uploaded.url

    return {
      path,
      url: resolveMediaUrl(path),
    }
  } catch (error) {
    throw new Error(getErrorMessage(error, '设备图片上传失败，请稍后重试'))
  }
}