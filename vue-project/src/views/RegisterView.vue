<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Check, Lock, Message, Phone, Postcard, User } from '@element-plus/icons-vue'
import AppBrand from '@/components/AppBrand.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  displayName: '',
  email: '',
  phone: '',
  username: '',
  password: '',
  confirmPassword: '',
  agreement: false,
})

function validateAgreement(_, value, callback) {
  if (!value) {
    callback(new Error('请先阅读并同意用户协议'))
    return
  }
  callback()
}

function validateConfirmPassword(_, value, callback) {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const rules = {
  displayName: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度应为 2 至 20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] },
  ],
  phone: [
    { max: 20, message: '手机号不能超过 20 个字符', trigger: 'blur' },
    { pattern: /^[0-9+\-\s]*$/, message: '请输入有效的手机号', trigger: 'blur' },
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_.-]{3,20}$/,
      message: '支持 3 至 20 位字母、数字、点、横线或下划线',
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少需要 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }],
  agreement: [{ validator: validateAgreement, trigger: 'change' }],
}

async function submitForm() {
  if (loading.value) return

  try {
    await formRef.value.validate()
    loading.value = true
    await authStore.register(form)

    ElMessage.success('注册成功，请使用新账号登录')
    router.push({ name: 'login', query: { username: form.username } })
  } catch (error) {
    if (error instanceof Error && error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}

function showAgreement() {
  ElMessage.info('演示环境中的用户协议仅供界面体验')
}
</script>

<template>
  <div class="register-page">
    <header class="register-header">
      <AppBrand />
      <RouterLink class="register-header__action" to="/login">
        <el-button text>
          <el-icon class="el-icon--left"><ArrowLeft /></el-icon>
          返回登录
        </el-button>
      </RouterLink>
    </header>

    <main class="register-main">
      <section class="register-panel" aria-labelledby="register-title">
        <div class="register-panel__heading">
          <div>
            <p class="register-panel__eyebrow">创建账号</p>
            <h1 id="register-title">加入智能实验室预约系统</h1>
            <p>填写以下信息，创建你的实验室预约账号。</p>
          </div>
          <span class="register-panel__badge">
            <el-icon><Check /></el-icon>
          </span>
        </div>

        <el-form
          ref="formRef"
          class="register-form"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          @submit.prevent="submitForm"
        >
          <div class="register-form__grid">
            <el-form-item label="姓名" prop="displayName">
              <el-input v-model.trim="form.displayName" placeholder="请输入姓名" autocomplete="name">
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model.trim="form.email"
                type="email"
                placeholder="name@example.com"
                autocomplete="email"
                clearable
              >
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <el-form-item label="手机号（选填）" prop="phone">
            <el-input
              v-model.trim="form.phone"
              placeholder="请输入手机号"
              autocomplete="tel"
              clearable
            >
              <template #prefix>
                <el-icon><Phone /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="用户名" prop="username">
            <el-input
              v-model.trim="form.username"
              placeholder="设置登录用户名"
              autocomplete="username"
              clearable
            >
              <template #prefix>
                <el-icon><Postcard /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <div class="register-form__grid">
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="至少 6 个字符"
                autocomplete="new-password"
                show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="再次输入密码"
                autocomplete="new-password"
                show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <el-form-item prop="agreement" label-width="0">
            <el-checkbox v-model="form.agreement">
              我已阅读并同意
              <el-link :underline="false" type="primary" @click="showAgreement">《用户协议》</el-link>
              和
              <el-link :underline="false" type="primary" @click="showAgreement">《隐私政策》</el-link>
            </el-checkbox>
          </el-form-item>

          <el-button
            class="register-form__submit"
            type="primary"
            native-type="submit"
            :loading="loading"
          >
            创建账号
          </el-button>
        </el-form>

        <p class="register-panel__login">
          已有账号？
          <RouterLink to="/login">直接登录</RouterLink>
        </p>
      </section>
    </main>

    <footer class="register-footer">© 2026 智能实验室预约系统 · 注册即代表你已了解演示环境用途</footer>
  </div>
</template>

<style scoped>
.register-page {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  background: #f5f7fa;
}

.register-header {
  display: flex;
  width: min(1120px, calc(100% - 40px));
  min-height: 76px;
  margin: 0 auto;
  align-items: center;
  justify-content: space-between;
}

.register-main {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 36px 20px;
}

.register-panel {
  width: min(100%, 720px);
  padding: 38px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 50px rgba(30, 41, 59, 0.1);
}

.register-panel__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 30px;
}

.register-panel__eyebrow {
  margin: 0 0 8px;
  color: var(--app-primary);
  font-size: 13px;
  font-weight: 700;
}

.register-panel h1 {
  margin: 0;
  color: var(--app-text);
  font-size: 26px;
  line-height: 1.35;
}

.register-panel__heading p:last-child {
  margin: 10px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.register-panel__badge {
  display: inline-flex;
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--app-success);
  background: #ecfdf3;
  font-size: 24px;
}

.register-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.register-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.register-form :deep(.el-form-item__label) {
  padding-bottom: 7px;
  color: #334155;
  font-weight: 600;
}

.register-form__submit {
  width: 100%;
  min-height: 44px;
  margin-top: 4px;
}

.register-panel__login {
  margin: 24px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
  text-align: center;
}

.register-panel__login a {
  color: var(--app-primary);
  font-weight: 600;
  text-decoration: none;
}

.register-footer {
  padding: 24px;
  color: var(--app-text-secondary);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 680px) {
  .register-header {
    width: calc(100% - 28px);
    min-height: 68px;
  }

  .register-main {
    align-items: flex-start;
    padding: 20px 14px;
  }

  .register-panel {
    padding: 28px 20px;
  }

  .register-panel h1 {
    font-size: 23px;
  }

  .register-form__grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .register-panel__badge {
    display: none;
  }
}
</style>
