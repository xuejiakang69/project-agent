<script setup>
import { computed } from 'vue'
import {
  Avatar,
  Lock,
  Message,
  Phone,
  UserFilled,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.state.user || {})
const isAdmin = authStore.isAdmin

const displayName = computed(
  () => user.value.displayName || user.value.name || user.value.username || '当前用户',
)
const roleLabel = computed(() => (isAdmin.value ? '系统管理员' : '普通用户'))
const accessDescription = computed(() =>
  isAdmin.value
    ? '你可以管理用户、实验室、设备和系统设置。'
    : '你可以使用工作台，并通过右上角头像维护个人资料。',
)

function displayValue(value) {
  const normalized = String(value ?? '').trim()
  return normalized || '未设置'
}
</script>

<template>
  <section class="dashboard-page">
    <header class="page-header">
      <div>
        <h1>工作台</h1>
        <p>查看账号信息和当前可用功能</p>
      </div>
      <el-tag :type="isAdmin ? 'danger' : 'success'" effect="light" size="large">
        {{ roleLabel }}
      </el-tag>
    </header>

    <el-card shadow="never" class="welcome-card">
      <div class="welcome-card__icon">
        <el-icon><UserFilled /></el-icon>
      </div>
      <div class="welcome-card__content">
        <span>欢迎回来</span>
        <h2>{{ displayName }}</h2>
        <p>{{ accessDescription }}</p>
      </div>
    </el-card>

    <div class="dashboard-grid">
      <el-card shadow="never" class="dashboard-card">
        <template #header>
          <div class="dashboard-card__header">
            <el-icon><Avatar /></el-icon>
            <strong>账号信息</strong>
          </div>
        </template>

        <div class="account-details">
          <div class="detail-item">
            <span>用户名</span>
            <strong>{{ displayValue(user.username) }}</strong>
          </div>
          <div class="detail-item">
            <span>姓名</span>
            <strong>{{ displayValue(user.name || user.displayName) }}</strong>
          </div>
          <div class="detail-item">
            <span>
              <el-icon><Message /></el-icon>
              邮箱
            </span>
            <strong>{{ displayValue(user.email) }}</strong>
          </div>
          <div class="detail-item">
            <span>
              <el-icon><Phone /></el-icon>
              手机号
            </span>
            <strong>{{ displayValue(user.phone) }}</strong>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="dashboard-card">
        <template #header>
          <div class="dashboard-card__header">
            <el-icon><Lock /></el-icon>
            <strong>访问权限</strong>
          </div>
        </template>

        <div class="permission-summary">
          <el-tag :type="isAdmin ? 'danger' : 'success'" effect="light">
            {{ roleLabel }}
          </el-tag>
          <p>{{ accessDescription }}</p>
          <ul>
            <li>工作台和个人资料始终可用</li>
            <li v-if="isAdmin">用户管理、实验室管理、设备管理和系统设置可用</li>
            <li v-else>管理模块仅对管理员开放</li>
          </ul>
        </div>
      </el-card>
    </div>
  </section>
</template>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 64px);
  padding: 28px;
  background: #f8fafc;
}

.page-header {
  display: flex;
  max-width: 1200px;
  margin: 0 auto 20px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.page-header h1 {
  margin: 0;
  color: var(--app-text);
  font-size: 24px;
  line-height: 1.35;
}

.page-header p {
  margin: 6px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
}

.welcome-card {
  max-width: 1200px;
  margin: 0 auto 18px;
  border-color: var(--app-border);
}

.welcome-card :deep(.el-card__body) {
  display: flex;
  padding: 24px;
  align-items: center;
  gap: 18px;
}

.welcome-card__icon {
  display: inline-flex;
  width: 56px;
  height: 56px;
  flex: 0 0 56px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #ffffff;
  background: var(--app-primary);
  font-size: 28px;
}

.welcome-card__content {
  min-width: 0;
}

.welcome-card__content span {
  color: var(--app-text-secondary);
  font-size: 13px;
}

.welcome-card__content h2 {
  margin: 3px 0 6px;
  color: var(--app-text);
  font-size: 20px;
}

.welcome-card__content p {
  margin: 0;
  color: var(--app-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.dashboard-grid {
  display: grid;
  max-width: 1200px;
  margin: 0 auto;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 18px;
}

.dashboard-card {
  border-color: var(--app-border);
}

.dashboard-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--app-text);
}

.account-details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 24px;
}

.detail-item {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.detail-item span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.detail-item strong {
  overflow-wrap: anywhere;
  color: var(--app-text);
  font-size: 14px;
}

.permission-summary p {
  margin: 14px 0;
  color: var(--app-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.permission-summary ul {
  margin: 0;
  padding-left: 20px;
  color: var(--app-text);
  font-size: 13px;
  line-height: 2;
}

@media (max-width: 820px) {
  .dashboard-page {
    padding: 20px 14px;
  }

  .page-header h1 {
    font-size: 21px;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .welcome-card :deep(.el-card__body) {
    align-items: flex-start;
    flex-direction: column;
  }

  .account-details {
    grid-template-columns: 1fr;
  }
}
</style>
