<template>
  <section class="chat-page">
    <div class="chat-shell">
      <header class="chat-header">
        <div class="chat-header__title">
          <div class="chat-header__icon">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div>
            <h1>智能助手</h1>
            <p>查询实验室信息，了解设备与预约流程</p>
          </div>
        </div>

        <el-button
          class="chat-header__clear"
          :disabled="sending || !messages.length"
          @click="clearChat"
        >
          <el-icon><Delete /></el-icon>
          <span>清空会话</span>
        </el-button>
      </header>

      <div class="chat-surface">
        <div ref="messagesPanel" class="messages-panel" aria-live="polite">
          <div v-if="!messages.length && !sending" class="empty-state">
            <div class="empty-state__icon">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <h2>今天想了解什么？</h2>
            <p>可以询问实验室开放时间、设备信息和预约流程。</p>
            <div class="empty-state__examples">
              <span>实验室什么时候开放？</span>
              <span>如何查看实验室设备？</span>
            </div>
          </div>

          <template v-else>
            <div
              v-for="(message, index) in messages"
              :key="`${message.role}-${index}`"
              class="message-row"
              :class="`message-row--${message.role}`"
            >
              <div class="message-avatar" :class="`message-avatar--${message.role}`">
                <el-icon>
                  <User v-if="message.role === 'user'" />
                  <Monitor v-else />
                </el-icon>
              </div>

              <div class="message-body">
                <span class="message-role">
                  {{ message.role === 'user' ? '我' : '智能助手' }}
                </span>
                <div
                  class="message-bubble"
                  :class="{ 'message-bubble--loading': message.streaming && !message.content }"
                >
                  <template v-if="message.streaming && !message.content">
                    <span />
                    <span />
                    <span />
                  </template>
                  <template v-else>
                    <div
                      v-if="message.role === 'assistant'"
                      class="message-markdown"
                      v-html="renderMarkdown(message.content)"
                    />
                    <div v-else class="message-text">
                      {{ message.content }}
                    </div>
                  </template>
                </div>
              </div>
            </div>

            <div v-if="sending && !hasStreamingMessage" class="message-row message-row--assistant">
              <div class="message-avatar message-avatar--assistant">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="message-body">
                <span class="message-role">智能助手</span>
                <div class="message-bubble message-bubble--loading" aria-label="正在回复">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          </template>
        </div>

        <div v-if="errorMessage" class="error-banner" role="alert">
          <el-icon><WarningFilled /></el-icon>
          <span>{{ errorMessage }}</span>
          <el-button link type="primary" :disabled="sending" @click="retry">
            重试
          </el-button>
        </div>

        <div class="composer">
          <el-input
            v-model="draft"
            class="composer__input"
            type="textarea"
            :rows="3"
            :maxlength="2000"
            :disabled="sending"
            resize="none"
            aria-label="输入想咨询的内容"
            placeholder="输入想咨询的内容"
            @keydown="handleKeydown"
          />

          <div class="composer__footer">
            <span class="composer__hint">Enter 发送，Shift + Enter 换行</span>
            <el-button
              type="primary"
              :disabled="!canSend"
              :loading="sending"
              @click="sendMessage"
            >
              <el-icon><Promotion /></el-icon>
              <span>发送</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import {
  ChatDotRound,
  Delete,
  Monitor,
  Promotion,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'

import { sendChatStream } from '@/api/chat'
import { renderMarkdown } from '@/utils/markdown'

const messages = ref([])
const draft = ref('')
const sending = ref(false)
const errorMessage = ref('')
const messagesPanel = ref(null)

const canSend = computed(() => !sending.value && draft.value.trim().length > 0)
const hasStreamingMessage = computed(() =>
  messages.value.some((message) => message.streaming),
)

async function scrollToBottom() {
  await nextTick()
  const panel = messagesPanel.value
  if (panel) {
    panel.scrollTop = panel.scrollHeight
  }
}

async function requestReply() {
  if (sending.value) return

  sending.value = true
  errorMessage.value = ''

  const assistantIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    streaming: true,
  })
  await scrollToBottom()

  try {
    await sendChatStream(messages.value, {
      onEvent: async (event) => {
        const reply = messages.value[assistantIndex]
        if (!reply) return

        if (event.type === 'token') {
          reply.content += String(event.data?.content ?? '')
          await scrollToBottom()
          return
        }

        if (event.type === 'done') {
          reply.content = String(event.data?.content ?? reply.content)
          reply.streaming = false
          await scrollToBottom()
        }
      },
    })

    const reply = messages.value[assistantIndex]
    if (reply) {
      reply.streaming = false
    }
  } catch (error) {
    messages.value.splice(assistantIndex, 1)
    errorMessage.value = error?.message || '\u667a\u80fd\u52a9\u624b\u8bf7\u6c42\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5'
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function sendMessage() {
  const content = draft.value.trim()
  if (!content || sending.value) return

  messages.value.push({
    role: 'user',
    content,
  })
  draft.value = ''
  await requestReply()
}

async function retry() {
  if (!messages.value.length || sending.value) return
  await requestReply()
}

function clearChat() {
  if (sending.value) return

  messages.value = []
  draft.value = ''
  errorMessage.value = ''
}

function handleKeydown(event) {
  if (
    event.key === 'Enter' &&
    !event.shiftKey &&
    !event.isComposing &&
    event.keyCode !== 229
  ) {
    event.preventDefault()
    sendMessage()
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  background: #f8fafc;
}

.chat-shell {
  display: flex;
  width: min(1120px, 100%);
  height: 100%;
  min-height: 0;
  margin: 0 auto;
  flex-direction: column;
}

.chat-header {
  display: flex;
  min-height: 76px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--app-border);
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  background: #ffffff;
}

.chat-header__title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.chat-header__icon {
  display: inline-flex;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #ffffff;
  background: #0f766e;
  font-size: 22px;
}

.chat-header h1 {
  margin: 0;
  color: var(--app-text);
  font-size: 18px;
  line-height: 1.35;
}

.chat-header p {
  margin: 3px 0 0;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.chat-header__clear {
  flex: 0 0 auto;
}

.chat-surface {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  background: #ffffff;
}

.messages-panel {
  min-height: 0;
  flex: 1;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 28px 24px 22px;
  scrollbar-gutter: stable;
}

.empty-state {
  display: flex;
  min-height: 100%;
  padding: 32px 16px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  text-align: center;
}

.empty-state__icon {
  display: inline-flex;
  width: 68px;
  height: 68px;
  margin-bottom: 18px;
  align-items: center;
  justify-content: center;
  border: 1px solid #99f6e4;
  border-radius: 8px;
  color: #0f766e;
  background: #ecfdf5;
  font-size: 34px;
}

.empty-state h2 {
  margin: 0;
  color: var(--app-text);
  font-size: 22px;
}

.empty-state p {
  max-width: 520px;
  margin: 10px 0 22px;
  color: var(--app-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.empty-state__examples {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

.empty-state__examples span {
  padding: 8px 12px;
  border: 1px solid var(--app-border);
  border-radius: 6px;
  color: #475569;
  background: #f8fafc;
  font-size: 12px;
}

.message-row {
  display: flex;
  width: min(780px, 100%);
  margin: 0 auto 22px;
  align-items: flex-start;
  gap: 12px;
}

.message-row--user {
  flex-direction: row-reverse;
}

.message-avatar {
  display: inline-flex;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 18px;
}

.message-avatar--user {
  color: #1d4ed8;
  background: #dbeafe;
}

.message-avatar--assistant {
  color: #0f766e;
  background: #ccfbf1;
}

.message-body {
  display: flex;
  min-width: 0;
  max-width: calc(100% - 52px);
  flex-direction: column;
  gap: 6px;
}

.message-row--user .message-body {
  align-items: flex-end;
}

.message-role {
  color: var(--app-text-secondary);
  font-size: 11px;
  line-height: 1.3;
}

.message-bubble {
  max-width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  color: var(--app-text);
  background: #f8fafc;
  font-size: 14px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.message-text {
  white-space: pre-wrap;
}

.message-markdown {
  min-width: 0;
  overflow-wrap: anywhere;
}

.message-markdown :deep(> :first-child) {
  margin-top: 0;
}

.message-markdown :deep(> :last-child) {
  margin-bottom: 0;
}

.message-markdown :deep(h1),
.message-markdown :deep(h2),
.message-markdown :deep(h3),
.message-markdown :deep(h4) {
  margin: 18px 0 8px;
  color: var(--app-text);
  font-weight: 650;
  line-height: 1.4;
}

.message-markdown :deep(h1) {
  font-size: 20px;
}

.message-markdown :deep(h2) {
  font-size: 18px;
}

.message-markdown :deep(h3),
.message-markdown :deep(h4) {
  font-size: 16px;
}

.message-markdown :deep(p),
.message-markdown :deep(ul),
.message-markdown :deep(ol),
.message-markdown :deep(blockquote),
.message-markdown :deep(pre) {
  margin: 8px 0;
}

.message-markdown :deep(ul),
.message-markdown :deep(ol) {
  padding-left: 22px;
}

.message-markdown :deep(li + li) {
  margin-top: 4px;
}

.message-markdown :deep(a) {
  color: #1d4ed8;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.message-markdown :deep(blockquote) {
  padding: 6px 12px;
  border-left: 3px solid #94a3b8;
  color: #475569;
  background: #f1f5f9;
}

.message-markdown :deep(code) {
  padding: 2px 5px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  color: #0f766e;
  background: #f1f5f9;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 0.9em;
}

.message-markdown :deep(pre) {
  max-width: 100%;
  padding: 12px 14px;
  border: 1px solid #dbe3ec;
  border-radius: 6px;
  color: #e2e8f0;
  background: #172033;
  overflow-x: auto;
}

.message-markdown :deep(pre code) {
  padding: 0;
  border: 0;
  color: inherit;
  background: transparent;
  font-size: 12px;
  line-height: 1.65;
}

.message-markdown :deep(table) {
  display: block;
  max-width: 100%;
  margin: 10px 0;
  border-collapse: collapse;
  overflow-x: auto;
}

.message-markdown :deep(th),
.message-markdown :deep(td) {
  padding: 7px 10px;
  border: 1px solid #dbe3ec;
  text-align: left;
  white-space: nowrap;
}

.message-markdown :deep(th) {
  color: #334155;
  background: #f1f5f9;
  font-weight: 650;
}

.message-markdown :deep(hr) {
  margin: 16px 0;
  border: 0;
  border-top: 1px solid var(--app-border);
}
.message-row--user .message-bubble {
  border-color: #2563eb;
  color: #ffffff;
  background: #2563eb;
}

.message-bubble--loading {
  display: inline-flex;
  min-width: 62px;
  min-height: 43px;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.message-bubble--loading span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #0f766e;
  animation: typing 1.2s infinite ease-in-out;
}

.message-bubble--loading span:nth-child(2) {
  animation-delay: 0.15s;
}

.message-bubble--loading span:nth-child(3) {
  animation-delay: 0.3s;
}

.error-banner {
  display: flex;
  min-height: 44px;
  padding: 9px 18px;
  border-top: 1px solid #fecaca;
  align-items: center;
  gap: 8px;
  color: #b91c1c;
  background: #fef2f2;
  font-size: 13px;
}

.error-banner span {
  min-width: 0;
  flex: 1;
  overflow-wrap: anywhere;
}

.composer {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--app-border);
  background: #ffffff;
}

.composer__input :deep(.el-textarea__inner) {
  min-height: 82px !important;
  padding: 12px 14px;
  border-radius: 8px;
  line-height: 1.6;
}

.composer__footer {
  display: flex;
  min-height: 38px;
  margin-top: 10px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.composer__hint {
  color: var(--app-text-secondary);
  font-size: 11px;
}

@keyframes typing {
  0%,
  60%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }

  30% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

@media (max-width: 720px) {
  .chat-header {
    min-height: 68px;
    padding: 12px 14px;
  }

  .chat-header__icon {
    width: 38px;
    height: 38px;
    flex-basis: 38px;
    font-size: 20px;
  }

  .chat-header h1 {
    font-size: 16px;
  }

  .chat-header p {
    display: none;
  }

  .chat-header__clear span {
    display: none;
  }

  .messages-panel {
    padding: 20px 12px 16px;
  }

  .message-row {
    gap: 8px;
  }

  .message-avatar {
    width: 32px;
    height: 32px;
    flex-basis: 32px;
    font-size: 16px;
  }

  .message-body {
    max-width: calc(100% - 42px);
  }

  .message-bubble {
    padding: 10px 12px;
    font-size: 13px;
  }

  .composer {
    padding: 12px 12px 14px;
  }

  .composer__hint {
    display: none;
  }

  .composer__footer {
    justify-content: flex-end;
  }
}
</style>
