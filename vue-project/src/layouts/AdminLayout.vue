<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  EditPen,
  Location,
  Setting,
  OfficeBuilding,
  SwitchButton,
  Calendar,
  ChatDotRound,
  Cpu,
  Upload,
  User,
} from '@element-plus/icons-vue'
import AppBrand from '@/components/AppBrand.vue'
import { resolveMediaUrl, uploadAvatar } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const collapsed = ref(window.innerWidth < 768)
const profileDialogVisible = ref(false)
const profileLoading = ref(false)
const avatarUploading = ref(false)
const profileFormRef = ref()

const profileForm = reactive({
  name: '',
  email: '',
  phone: '',
  avatar: '',
})

const currentUser = computed(() => authStore.state.user || {})
const isAdmin = authStore.isAdmin
const isStudent = authStore.isStudent
const displayName = computed(
  () =>
    currentUser.value.displayName ||
    currentUser.value.name ||
    currentUser.value.username ||
    '当前用户',
)
const avatarUrl = computed(() => resolveMediaUrl(currentUser.value.avatar))
const profileAvatarUrl = computed(() => resolveMediaUrl(profileForm.avatar))

const profileRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度应为 2 至 20 个字符', trigger: 'blur' },
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] },
  ],
  phone: [
    { max: 20, message: '手机号不能超过 20 个字符', trigger: 'blur' },
    { pattern: /^[0-9+\-\s]*$/, message: '请输入有效的手机号', trigger: 'blur' },
  ],
}

function openProfile() {
  const user = currentUser.value
  profileForm.name = user.name || user.displayName || ''
  profileForm.email = user.email || ''
  profileForm.phone = user.phone || ''
  profileForm.avatar = user.avatar || ''
  profileDialogVisible.value = true
}

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('头像只能是图片文件')
    return false
  }

  if (!isLt2M) {
    ElMessage.error('头像不能超过 2MB')
    return false
  }

  return true
}

async function handleAvatarUpload({ file }) {
  if (!beforeAvatarUpload(file)) return

  avatarUploading.value = true

  try {
    const uploaded = await uploadAvatar(file)
    profileForm.avatar = uploaded.path
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error(error.message || '头像上传失败')
  } finally {
    avatarUploading.value = false
  }
}

async function saveProfile() {
  if (profileLoading.value) return

  try {
    await profileFormRef.value.validate()
    profileLoading.value = true
    await authStore.updateProfile({
      name: profileForm.name,
      email: profileForm.email,
      phone: profileForm.phone,
      avatar: profileForm.avatar,
    })
    profileDialogVisible.value = false
    ElMessage.success('个人信息已更新')
  } catch (error) {
    if (error instanceof Error && error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    profileLoading.value = false
  }
}

async function logout() {
  await ElMessageBox.confirm('确定要退出当前账号吗？', '退出登录', {
    type: 'warning',
    confirmButtonText: '退出',
    cancelButtonText: '取消',
  })

  authStore.logout()
  router.replace('/login')
}

function handleCommand(command) {
  if (command === 'profile') {
    openProfile()
    return
  }

  if (command === 'logout') {
    logout()
  }
}
</script>

<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-header__title">
        <strong>智能实验室预约系统</strong>
        <span>实验室资源与预约管理</span>
      </div>

      <el-dropdown trigger="hover" placement="bottom-end" @command="handleCommand">
        <button class="user-menu-trigger" type="button">
          <el-avatar :size="36" :src="avatarUrl || undefined" class="user-avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="user-name">{{ displayName }}</span>
          <el-icon class="user-menu-arrow"><ArrowDown /></el-icon>
        </button>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><EditPen /></el-icon>
              修改个人信息
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-header>

    <el-container class="app-body">
      <el-aside class="app-aside" :width="collapsed ? '72px' : '232px'">
        <div class="app-aside__brand">
          <AppBrand :compact="collapsed" inverse />
        </div>

        <el-menu
          class="app-menu"
          :default-active="route.path"
          :collapse="collapsed"
          :collapse-transition="false"
          router
        >
          <el-menu-item index="/home">
            <el-icon><Location /></el-icon>
            <template #title>工作台</template>
          </el-menu-item>
          <el-menu-item index="/home/chat">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>智能助手</template>
          </el-menu-item>
          <template v-if="isStudent">
            <el-menu-item index="/home/student/labs">
              <el-icon><OfficeBuilding /></el-icon>
              <template #title>实验室预约</template>
            </el-menu-item>
            <el-menu-item index="/home/my-reservations">
              <el-icon><Calendar /></el-icon>
              <template #title>我的预约</template>
            </el-menu-item>
          </template>
          <template v-if="isAdmin">
            <el-menu-item index="/home/users">
              <el-icon><User /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
          </template>
          <template v-if="isAdmin">
            <el-menu-item index="/home/labs">
              <el-icon><OfficeBuilding /></el-icon>
              <template #title>实验室管理</template>
            </el-menu-item>
            <el-menu-item index="/home/equipments">
              <el-icon><Cpu /></el-icon>
              <template #title>设备管理</template>
            </el-menu-item>
            <el-menu-item index="/home/reservations">
              <el-icon><Calendar /></el-icon>
              <template #title>已预约</template>
            </el-menu-item>
          </template>
          <template v-if="isAdmin">
            <el-menu-item index="/home/settings">
              <el-icon><Setting /></el-icon>
              <template #title>系统设置</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>

      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>

    <el-dialog
      v-model="profileDialogVisible"
      title="修改个人信息"
      width="min(480px, calc(100vw - 28px))"
      destroy-on-close
    >
      <el-form
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        label-position="top"
        size="large"
      >
        <el-form-item label="头像">
          <div class="avatar-editor">
            <el-upload
              :show-file-list="false"
              :http-request="handleAvatarUpload"
              accept="image/*"
            >
              <el-avatar :size="72" :src="profileAvatarUrl || undefined" class="profile-avatar">
                <el-icon><Upload /></el-icon>
              </el-avatar>
            </el-upload>
            <div class="avatar-editor__hint">点击头像上传图片，支持 JPG、PNG，最大 2MB</div>
          </div>
        </el-form-item>

        <el-form-item label="姓名" prop="name">
          <el-input v-model.trim="profileForm.name" placeholder="请输入姓名" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model.trim="profileForm.email" type="email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model.trim="profileForm.phone" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="profileLoading || avatarUploading"
          @click="saveProfile"
        >
          保存修改
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.app-header {
  position: relative;
  z-index: 10;
  display: flex;
  height: 64px;
  flex: 0 0 64px;
  padding: 0 22px;
  border-bottom: 1px solid var(--app-border);
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
}

.app-header__title {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.25;
}

.app-header__title strong {
  color: var(--app-text);
  font-size: 15px;
}

.app-header__title span {
  margin-top: 3px;
  color: var(--app-text-secondary);
  font-size: 11px;
}

.user-menu-trigger {
  display: inline-flex;
  min-height: 42px;
  padding: 3px 8px 3px 4px;
  border: 1px solid transparent;
  border-radius: 8px;
  align-items: center;
  gap: 8px;
  color: var(--app-text);
  background: transparent;
  cursor: pointer;
}

.user-menu-trigger:hover,
.user-menu-trigger:focus-visible {
  border-color: var(--app-border);
  background: var(--app-background);
  outline: none;
}

.user-avatar {
  flex: 0 0 36px;
  color: var(--app-primary);
  background: #e9f0ff;
}

.user-name {
  max-width: 150px;
  overflow: hidden;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-menu-arrow {
  color: var(--app-text-secondary);
  font-size: 12px;
}

.app-body {
  min-height: 0;
  overflow: hidden;
}

.app-aside {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 16px 10px;
  background: #111827;
}

.app-aside__brand {
  display: flex;
  min-height: 48px;
  padding: 0 8px;
  align-items: center;
}

.app-menu {
  margin-top: 16px;
  border-right: 0;
  background: transparent;
}

.app-menu :deep(.el-menu-item) {
  margin-bottom: 4px;
  border-radius: 6px;
  color: #cbd5e1;
}

.app-menu :deep(.el-menu-item:hover),
.app-menu :deep(.el-menu-item.is-active) {
  color: #ffffff;
  background: #2563eb;
}

.app-main {
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  padding: 0;
  background: #ffffff;
}

.avatar-editor {
  display: flex;
  align-items: center;
  gap: 14px;
}

.profile-avatar {
  color: var(--app-primary);
  background: #e9f0ff;
  cursor: pointer;
}

.avatar-editor__hint {
  color: var(--app-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 14px;
  }

  .app-header__title span {
    display: none;
  }

  .user-menu-trigger {
    padding-right: 4px;
  }

  .user-name {
    display: none;
  }

  .app-aside {
    width: 72px;
  }
}
</style>
