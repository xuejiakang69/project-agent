import axios from 'axios'

import { readToken } from '@/api/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function getErrorMessage(error, fallback = '智能助手请求失败，请稍后重试') {
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

  if (error?.code === 'ECONNABORTED') {
    return '智能助手响应超时，请稍后重试'
  }

  if (error?.request) {
    return '无法连接服务，请确认后端已启动'
  }

  return error?.message || fallback
}

function normalizeMessages(messages) {
  return messages
    .map((message) => ({
      role: String(message?.role ?? '').trim(),
      content: String(message?.content ?? '').trim(),
    }))
    .filter(
      (message) =>
        ['user', 'assistant'].includes(message.role) && message.content.length > 0,
    )
}

export async function sendChat(messages) {
  const payload = normalizeMessages(messages)

  if (!payload.length) {
    throw new Error('请输入想要咨询的内容')
  }

  const token = readToken()

  try {
    const response = await axios.post(
      `${API_BASE_URL}/agent/chat`,
      { messages: payload },
      {
        timeout: 60000,
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          'Content-Type': 'application/json',
        },
      },
    )

    const result = response.data
    const reply = result?.result

    if (
      result?.code !== 0 ||
      !reply ||
      typeof reply.content !== 'string' ||
      !reply.content.trim()
    ) {
      throw new Error(result?.message || '智能助手响应格式不正确')
    }

    return {
      role: 'assistant',
      content: reply.content.trim(),
    }
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}
