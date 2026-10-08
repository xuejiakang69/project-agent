<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, RefreshLeft, Search } from '@element-plus/icons-vue'
import { listUsers } from '@/api/auth'

const users = ref([])
const total = ref(0)
const totalPages = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const appliedKeyword = ref('')
const loading = ref(false)
let requestSequence = 0

async function fetchUsers() {
  const sequence = ++requestSequence
  loading.value = true

  try {
    const result = await listUsers({
      page: page.value,
      pageSize: pageSize.value,
      keyword: appliedKeyword.value,
    })

    if (sequence !== requestSequence) return

    users.value = result.items
    total.value = result.total
    totalPages.value = result.total_pages
    page.value = result.page
    pageSize.value = result.page_size
  } catch (error) {
    if (sequence !== requestSequence) return
    ElMessage.error(error.message || '用户列表获取失败，请稍后重试')
  } finally {
    if (sequence === requestSequence) {
      loading.value = false
    }
  }
}

function searchUsers() {
  appliedKeyword.value = keyword.value.trim()
  page.value = 1
  fetchUsers()
}

function resetSearch() {
  keyword.value = ''
  appliedKeyword.value = ''
  page.value = 1
  fetchUsers()
}

function changePage(nextPage) {
  page.value = nextPage
  fetchUsers()
}

function changePageSize(nextPageSize) {
  pageSize.value = nextPageSize
  page.value = 1
  fetchUsers()
}

function roleLabel(role) {
  return role === 'admin' ? '管理员' : role === 'user' ? '普通用户' : role || '未知'
}

function roleTagType(role) {
  return role === 'admin' ? 'danger' : 'info'
}

function statusLabel(status) {
  return status === 1 ? '正常' : '禁用'
}

function statusTagType(status) {
  return status === 1 ? 'success' : 'info'
}

onMounted(fetchUsers)
</script>

<template>
  <section class="users-page">
    <header class="page-header">
      <div>
        <h1>用户管理</h1>
        <p>查看系统用户账号、身份和访问状态</p>
      </div>
      <el-button type="primary" :loading="loading" @click="searchUsers">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </header>

    <el-card shadow="never" class="users-card">
      <div class="toolbar">
        <el-input
          v-model="keyword"
          class="toolbar__search"
          placeholder="搜索用户名"
          clearable
          @keyup.enter="searchUsers"
          @clear="searchUsers"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="toolbar__actions">
          <el-button type="primary" :loading="loading" @click="searchUsers">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button :disabled="loading" @click="resetSearch">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="users"
        class="users-table"
        row-key="id"
        empty-text="暂无用户数据"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用户" min-width="210">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="36" class="user-cell__avatar">
                {{ (row.displayName || row.username || 'U').slice(0, 1).toUpperCase() }}
              </el-avatar>
              <div class="user-cell__identity">
                <strong>{{ row.displayName || row.name || row.username }}</strong>
                <span>@{{ row.username }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="190">
          <template #default="{ row }">{{ row.email || '--' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="140">
          <template #default="{ row }">{{ row.phone || '--' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" effect="light">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <footer class="pagination-bar">
        <span class="pagination-bar__summary">
          共 {{ total }} 条，{{ totalPages }} 页
        </span>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          :disabled="loading"
          layout="sizes, prev, pager, next, jumper"
          background
          @current-change="changePage"
          @size-change="changePageSize"
        />
      </footer>
    </el-card>
  </section>
</template>

<style scoped>
.users-page {
  min-height: calc(100vh - 64px);
  padding: 28px;
  background: #f8fafc;
}

.page-header {
  display: flex;
  margin: 0 auto 20px;
  max-width: 1440px;
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

.users-card {
  max-width: 1440px;
  margin: 0 auto;
  border-color: var(--app-border);
}

.toolbar {
  display: flex;
  margin-bottom: 18px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.toolbar__search {
  width: min(420px, 100%);
}

.toolbar__actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.users-table {
  width: 100%;
}

.user-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.user-cell__avatar {
  flex: 0 0 36px;
  color: var(--app-primary);
  background: #e9f0ff;
  font-weight: 700;
}

.user-cell__identity {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.45;
}

.user-cell__identity strong {
  overflow: hidden;
  color: var(--app-text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-cell__identity span {
  overflow: hidden;
  color: var(--app-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-bar {
  display: flex;
  margin-top: 20px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.pagination-bar__summary {
  color: var(--app-text-secondary);
  font-size: 13px;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .users-page {
    padding: 18px 14px;
  }

  .page-header {
    align-items: flex-start;
  }

  .page-header h1 {
    font-size: 21px;
  }

  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar__search {
    width: 100%;
  }

  .toolbar__actions {
    justify-content: flex-end;
  }

  .pagination-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .pagination-bar :deep(.el-pagination) {
    max-width: 100%;
    overflow-x: auto;
  }
}
</style>