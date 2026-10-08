<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Lock, User, UserFilled } from '@element-plus/icons-vue'
import AppBrand from '@/components/AppBrand.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: typeof route.query.username === 'string' ? route.query.username : '',
  password: '',
  remember: true,
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { max: 50, message: '用户名不能超过 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { max: 128, message: '密码不能超过 128 个字符', trigger: 'blur' },
  ],
}

function getRedirectTarget() {
  const redirect = route.query.redirect

  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')) {
    return redirect
  }

  return '/home'
}

async function login() {
  if (loading.value) return

  try {
    await formRef.value.validate()
    loading.value = true
    await authStore.login(form)
    ElMessage.success('登录成功，欢迎回来')
    router.replace(getRedirectTarget())
  } catch (error) {
    if (error instanceof Error && error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <header class="auth-header">
      <AppBrand />
      <RouterLink class="auth-header__action" to="/register">
        <el-button text>
          注册账号
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </RouterLink>
    </header>

    <main class="auth-main">
      <section class="auth-panel" aria-labelledby="login-title">
        <div class="auth-panel__icon" aria-hidden="true">
          <el-icon><UserFilled /></el-icon>
        </div>
        <h1 id="login-title">登录智能实验室预约系统</h1>

        <el-form
          ref="formRef"
          class="login-form"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="login"
        >
          <el-form-item prop="username">
            <el-input
              v-model.trim="form.username"
              size="large"
              placeholder="请输入用户名"
              :prefix-icon="User"
              autocomplete="username"
              clearable
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              autocomplete="current-password"
              show-password
            />
          </el-form-item>

          <div class="login-form__options">
            <el-checkbox v-model="form.remember">记住登录状态</el-checkbox>
          </div>

          <el-button
            class="auth-panel__login"
            type="primary"
            size="large"
            native-type="submit"
            :loading="loading"
          >
            登录
          </el-button>
        </el-form>

        <p class="auth-panel__register">
          还没有账号？
          <RouterLink to="/register">立即注册</RouterLink>
        </p>
      </section>
    </main>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  height: 100vh;
  height: 100svh;
  min-height: 0;
  overflow: hidden;
  flex-direction: column;
  background:
    linear-gradient(#e9eef6 1px, transparent 1px),
    linear-gradient(90deg, #e9eef6 1px, transparent 1px),
    #f5f7fa;
  background-size: 32px 32px;
}

.auth-header {
  display: flex;
  width: min(1120px, calc(100% - 40px));
  min-height: 76px;
  margin: 0 auto;
  align-items: center;
  justify-content: space-between;
}

.auth-main {
  display: flex;
  height: 100%;
  min-height: 0;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-panel {
  width: min(100%, 400px);
  padding: 32px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 50px rgba(30, 41, 59, 0.1);
  text-align: center;
}

.auth-panel__icon {
  display: inline-flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #ffffff;
  background: var(--app-primary);
  font-size: 25px;
}

.auth-panel h1 {
  margin: 22px 0 24px;
  color: var(--app-text);
  font-size: 24px;
  line-height: 1.35;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 42px;
}

.login-form__options {
  display: flex;
  min-height: 32px;
  margin: 0 0 14px;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.auth-panel__login {
  width: 100%;
  min-height: 44px;
}

.auth-panel__register {
  margin: 24px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
}

.auth-panel__register a {
  color: var(--app-primary);
  font-weight: 600;
  text-decoration: none;
}

@media (max-width: 560px) {
  .auth-header {
    width: calc(100% - 28px);
    min-height: 68px;
  }

  .auth-main {
    height: auto;
    min-height: calc(100svh - 68px);
    padding: 14px;
  }

  .auth-panel {
    padding: 28px 20px;
    box-shadow: 0 12px 35px rgba(30, 41, 59, 0.08);
  }

  .auth-panel h1 {
    font-size: 22px;
  }
}
</style>