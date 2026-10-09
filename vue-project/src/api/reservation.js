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
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
  }
}

function normalizeReservation(reservation) {
  return {
    ...reservation,
    id: Number(reservation.id),
    user_id: Number(reservation.user_id),
    lab_id: Number(reservation.lab_id),
    equipment_id: reservation.equipment_id ? Number(reservation.equipment_id) : null,
    user_name: reservation.user_name || '',
    lab_name: reservation.lab_name || '',
    equipment_name: reservation.equipment_name || '',
    remark: reservation.remark || '',
    status: Number(reservation.status),
  }
}

function normalizePayload(payload = {}) {
  return {
    lab_id: Number(payload.lab_id),
    equipment_id: payload.equipment_id ? Number(payload.equipment_id) : null,
    date: String(payload.date ?? '').trim(),
    start_time: String(payload.start_time ?? '').trim(),
    end_time: String(payload.end_time ?? '').trim(),
    remark: String(payload.remark ?? '').trim() || null,
  }
}

function validateReservationResponse(result, fallbackMessage) {
  const reservation = result?.result

  if (result?.code !== 0 || !reservation?.id) {
    throw new Error(result?.message || fallbackMessage)
  }

  return normalizeReservation(reservation)
}

export async function listReservations({ page = 1, pageSize = 10, status = null, keyword = '' } = {}) {
  try {
    const normalizedKeyword = String(keyword ?? '').trim()
    const response = await axios.get(`${API_BASE_URL}/reservations/list`, {
      ...requestConfig(),
      params: {
        page: Number(page) || 1,
        page_size: Number(pageSize) || 10,
        ...(status === null || status === '' ? {} : { status: Number(status) }),
        ...(normalizedKeyword ? { keyword: normalizedKeyword } : {}),
      },
    })

    const result = response.data
    const pageResult = result?.result

    if (result?.code !== 0 || !pageResult || !Array.isArray(pageResult.items)) {
      throw new Error(result?.message || '预约列表响应格式不正确')
    }

    return {
      items: pageResult.items.map(normalizeReservation),
      total: Number(pageResult.total) || 0,
      page: Number(pageResult.page) || Number(page) || 1,
      page_size: Number(pageResult.page_size) || Number(pageSize) || 10,
      total_pages: Number(pageResult.total_pages) || 0,
    }
  } catch (error) {
    throw new Error(getErrorMessage(error, '预约列表获取失败，请稍后重试'))
  }
}

export async function createReservation(payload = {}) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/reservations/create`,
      normalizePayload(payload),
      requestConfig(),
    )

    return validateReservationResponse(response.data, '预约响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '预约失败，请稍后重试'))
  }
}

export async function revokeReservation(id) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/reservations/revoke/${Number(id)}`,
      {},
      requestConfig(),
    )

    return validateReservationResponse(response.data, '取消预约响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '取消预约失败，请稍后重试'))
  }
}

export async function auditReservation(id, status) {
  try {
    const normalizedStatus = Number(status)
    if (![1, 2].includes(normalizedStatus)) {
      throw new Error('审核状态错误')
    }

    const response = await axios.post(
      `${API_BASE_URL}/reservations/audit/${Number(id)}/${normalizedStatus}`,
      {},
      requestConfig(),
    )

    return validateReservationResponse(response.data, '审核响应格式不正确')
  } catch (error) {
    throw new Error(getErrorMessage(error, '审核失败，请稍后重试'))
  }
}
