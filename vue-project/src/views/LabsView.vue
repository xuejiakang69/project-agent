<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete,
  EditPen,
  Plus,
  RefreshLeft,
  Search,
} from '@element-plus/icons-vue'
import { createLab, deleteLab, listLabs, updateLab } from '@/api/lab'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = authStore.isAdmin
const pageTitle = computed(() => (isAdmin.value ? '实验室管理' : '实验室预约'))
const pageDescription = computed(() =>
  isAdmin.value
    ? '维护实验室信息、开放状态、地点与容量配置。'
    : '查看实验室资源、开放时间和可容纳人数。',
)

const loading = ref(false)
const labs = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeKeyword = ref('')

const formDialogVisible = ref(false)
const formLoading = ref(false)
const formRef = ref()
const editingLabId = ref(null)

const form = reactive({
  name: '',
  description: '',
  status: 1,
  location: '',
  open_time: '',
  close_time: '',
  capacity: null,
})

const formRules = {
  name: [
    { required: true, message: '请输入实验室名称', trigger: 'blur' },
    { min: 1, max: 50, message: '实验室名称不能超过 50 个字符', trigger: 'blur' },
  ],
  description: [
    { max: 255, message: '实验室描述不能超过 255 个字符', trigger: 'blur' },
  ],
  location: [
    { max: 50, message: '实验室地点不能超过 50 个字符', trigger: 'blur' },
  ],
  open_time: [
    { max: 50, message: '开放时间不能超过 50 个字符', trigger: 'blur' },
  ],
  close_time: [
    { max: 50, message: '关闭时间不能超过 50 个字符', trigger: 'blur' },
  ],
  capacity: [
    {
      validator: (_, value, callback) => {
        if (value === null || value === undefined || value === '') {
          callback()
          return
        }

        if (!Number.isInteger(Number(value)) || Number(value) < 0) {
          callback(new Error('容量必须是不小于 0 的整数'))
          return
        }

        callback()
      },
      trigger: ['blur', 'change'],
    },
  ],
}

function createEmptyForm() {
  return {
    name: '',
    description: '',
    status: 1,
    location: '',
    open_time: '',
    close_time: '',
    capacity: null,
  }
}

async function loadLabs() {
  loading.value = true

  try {
    const result = await listLabs({
      page: page.value,
      pageSize: pageSize.value,
      keyword: activeKeyword.value,
    })

    labs.value = result.items
    total.value = result.total
    page.value = result.page
    pageSize.value = result.page_size
    totalPages.value = result.total_pages
  } catch (error) {
    labs.value = []
    total.value = 0
    totalPages.value = 0
    ElMessage.error(error.message || '实验室列表获取失败')
  } finally {
    loading.value = false
  }
}

function searchLabs() {
  activeKeyword.value = searchKeyword.value.trim()
  page.value = 1
  loadLabs()
}

function resetSearch() {
  searchKeyword.value = ''
  activeKeyword.value = ''
  page.value = 1
  loadLabs()
}

function changePage(nextPage) {
  page.value = nextPage
  loadLabs()
}

function changePageSize(nextSize) {
  pageSize.value = nextSize
  page.value = 1
  loadLabs()
}

function openCreateDialog() {
  if (!isAdmin.value) return

  editingLabId.value = null
  Object.assign(form, createEmptyForm())
  formDialogVisible.value = true
}

function openEditDialog(row) {
  if (!isAdmin.value) return

  editingLabId.value = row.id
  Object.assign(form, {
    name: row.name || '',
    description: row.description || '',
    status: Number(row.status) === 0 ? 0 : 1,
    location: row.location || '',
    open_time: row.open_time || '',
    close_time: row.close_time || '',
    capacity: row.capacity === null ? null : Number(row.capacity),
  })
  formDialogVisible.value = true
}

async function submitLab() {
  if (!isAdmin.value || formLoading.value) return

  try {
    await formRef.value.validate()
    formLoading.value = true

    const payload = {
      name: form.name,
      description: form.description,
      status: form.status,
      location: form.location,
      open_time: form.open_time,
      close_time: form.close_time,
      capacity: form.capacity,
    }

    if (editingLabId.value) {
      await updateLab(editingLabId.value, payload)
      ElMessage.success('实验室信息已更新')
    } else {
      await createLab(payload)
      ElMessage.success('实验室创建成功')
    }

    formDialogVisible.value = false
    await loadLabs()
  } catch (error) {
    if (error?.message) {
      ElMessage.error(error.message)
    }
  } finally {
    formLoading.value = false
  }
}

async function confirmDelete(row) {
  if (!isAdmin.value) return

  try {
    await ElMessageBox.confirm(
      `确定要删除实验室“${row.name}”吗？删除后无法恢复。`,
      '删除实验室',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )

    await deleteLab(row.id)
    ElMessage.success('实验室已删除')

    if (labs.value.length === 1 && page.value > 1) {
      page.value -= 1
    }

    await loadLabs()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close' && error?.message) {
      ElMessage.error(error.message)
    }
  }
}

function statusLabel(status) {
  return Number(status) === 1 ? '开放中' : '维护中'
}

function statusTagType(status) {
  return Number(status) === 1 ? 'success' : 'warning'
}

onMounted(loadLabs)
</script>

<template>
  <section class="labs-page">
    <header class="page-header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageDescription }}</p>
      </div>

      <el-button v-if="isAdmin" type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增实验室
      </el-button>
    </header>

    <el-card class="labs-card" shadow="never">
      <div class="toolbar">
        <el-input
          v-model.trim="searchKeyword"
          class="toolbar__search"
          clearable
          placeholder="搜索实验室名称、地点或描述"
          :disabled="loading"
          @keyup.enter="searchLabs"
          @clear="resetSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="toolbar__actions">
          <el-button type="primary" :loading="loading" @click="searchLabs">
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
        :data="labs"
        class="labs-table"
        row-key="id"
        empty-text="暂无实验室数据"
      >
        <el-table-column prop="id" label="ID" width="76" />

        <el-table-column label="实验室" min-width="220">
          <template #default="{ row }">
            <div class="lab-cell">
              <strong>{{ row.name }}</strong>
              <span>{{ row.description || '暂无实验室介绍' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="location" label="地点" min-width="150">
          <template #default="{ row }">{{ row.location || '--' }}</template>
        </el-table-column>

        <el-table-column label="开放时间" min-width="170">
          <template #default="{ row }">
            <span v-if="row.open_time || row.close_time">
              {{ row.open_time || '--' }} - {{ row.close_time || '--' }}
            </span>
            <span v-else>--</span>
          </template>
        </el-table-column>

        <el-table-column prop="capacity" label="容量" width="90">
          <template #default="{ row }">
            {{ row.capacity === null ? '--' : `${row.capacity} 人` }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column v-if="isAdmin" label="操作" width="176" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button text type="primary" @click="openEditDialog(row)">
                <el-icon><EditPen /></el-icon>
                编辑
              </el-button>
              <el-button text type="danger" @click="confirmDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <footer class="pagination-bar">
        <span class="pagination-bar__summary">
          共 {{ total }} 条，第 {{ page }} / {{ Math.max(totalPages, 1) }} 页
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

    <el-dialog
      v-model="formDialogVisible"
      :title="editingLabId ? '编辑实验室' : '新增实验室'"
      width="min(640px, calc(100vw - 28px))"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="96px"
        class="lab-form"
      >
        <el-form-item label="实验室名称" prop="name">
          <el-input
            v-model.trim="form.name"
            maxlength="50"
            show-word-limit
            placeholder="请输入实验室名称"
          />
        </el-form-item>

        <el-form-item label="实验室介绍" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="255"
            show-word-limit
            placeholder="请输入实验室介绍"
          />
        </el-form-item>

        <el-form-item label="地点" prop="location">
          <el-input
            v-model.trim="form.location"
            maxlength="50"
            placeholder="请输入实验室地点"
          />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="开放时间" prop="open_time">
            <el-input
              v-model.trim="form.open_time"
              maxlength="50"
              placeholder="如 08:00"
            />
          </el-form-item>

          <el-form-item label="关闭时间" prop="close_time">
            <el-input
              v-model.trim="form.close_time"
              maxlength="50"
              placeholder="如 22:00"
            />
          </el-form-item>

          <el-form-item label="容量" prop="capacity">
            <el-input-number
              v-model="form.capacity"
              :min="0"
              :precision="0"
              :controls="false"
              placeholder="不限制可留空"
            />
          </el-form-item>

          <el-form-item label="开放状态">
            <el-switch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
              active-text="开放"
              inactive-text="维护"
            />
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="submitLab">
          {{ editingLabId ? '保存修改' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.labs-page {
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

.labs-card {
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
  width: min(440px, 100%);
}

.toolbar__actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.labs-table {
  width: 100%;
}

.lab-cell {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.55;
}

.lab-cell strong {
  overflow: hidden;
  color: var(--app-text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lab-cell span {
  overflow: hidden;
  color: var(--app-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-actions {
  display: flex;
  align-items: center;
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

.lab-form :deep(.el-select),
.lab-form :deep(.el-input-number) {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 16px;
}

.form-grid :deep(.el-form-item) {
  min-width: 0;
}

@media (max-width: 768px) {
  .labs-page {
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

  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>