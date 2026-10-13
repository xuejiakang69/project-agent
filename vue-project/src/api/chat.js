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


export async function sendChatStream(
  messages,
  { onEvent } = {},
  signal,
) {
  const payload = normalizeMessages(messages)

  if (!payload.length) {
    throw new Error('Please enter a question')
  }

  const token = readToken()
  let response

  try {
    response = await fetch(`${API_BASE_URL}/agent/chat/stream`, {
      method: 'POST',
      signal,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: payload }),
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new Error('Unable to connect to the server')
  }

  if (!response.ok) {
    let errorData = null
    try {
      errorData = await response.json()
    } catch {
      errorData = null
    }
    throw new Error(
      getErrorMessage(
        { response: { data: errorData } },
        `Smart assistant request failed (${response.status})`,
      ),
    )
  }

  if (!response.body) {
    throw new Error('Streaming response is unavailable')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let completed = false
  const result = {
    role: 'assistant',
    content: '',
    usedTools: [],
  }

  function parseBlock(block) {
    let eventName = 'message'
    const dataLines = []

    for (const line of block.split(/\r?\n/)) {
      if (!line || line.startsWith(':')) continue
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).replace(/^ /, ''))
      }
    }

    if (!dataLines.length) return

    let data
    try {
      data = JSON.parse(dataLines.join('\n'))
    } catch {
      throw new Error('Invalid streaming response')
    }

    const event = { type: eventName, data }
    onEvent?.(event)

    if (event.type === 'token') {
      result.content += String(event.data?.content ?? '')
    } else if (event.type === 'done') {
      completed = true
      result.content = String(event.data?.content ?? result.content)
      result.usedTools = Array.isArray(event.data?.used_tools)
        ? event.data.used_tools
        : []
    } else if (event.type === 'error') {
      throw new Error(String(event.data?.message || 'Smart assistant request failed'))
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split(/\r?\n\r?\n/)
      buffer = blocks.pop() ?? ''
      blocks.forEach(parseBlock)
    }

    buffer += decoder.decode()
    if (buffer.trim()) parseBlock(buffer)
  } finally {
    reader.releaseLock()
  }

  if (!completed) {
    throw new Error('Streaming response ended before completion')
  }

  return result
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
