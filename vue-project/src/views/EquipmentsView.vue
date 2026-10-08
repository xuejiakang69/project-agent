<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete,
  EditPen,
  Picture,
  Plus,
  RefreshLeft,
  Search,
  Upload,
} from '@element-plus/icons-vue'
import {
  createEquipment,
  deleteEquipment,
  listEquipments,
  updateEquipment,
  uploadEquipmentImage,
} from '@/api/equipment'
import { listLabs } from '@/api/lab'
import { resolveMediaUrl } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = authStore.isAdmin
const pageTitle = computed(() => (isAdmin.value ? '设备管理' : '设备信息'))
const pageDescription = computed(() =>
  isAdmin.value
    ? '维护实验室设备信息、所属实验室、规格和运行状态。'
    : '查看实验室设备信息、数量和运行状态。',
)

const loading = ref(false)
const equipments = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeKeyword = ref('')

const formDialogVisible = ref(false)
const formLoading = ref(false)
const formRef = ref()
const editingEquipmentId = ref(null)
const imageUploading = ref(false)
const labOptions = ref([])

const form = reactive({
  lab_id: null,
  name: '',
  description: '',
  img: '',
  spec: '',
  quantity: 1,
  status: 1,
})

const formRules = {
  lab_id: [
    { required: true, message: '请选择所属实验室', trigger: ['blur', 'change'] },
  ],
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 1, max: 50, message: '设备名称不能超过 50 个字符', trigger: 'blur' },
  ],
  description: [
    { max: 500, message: '设备说明不能超过 500 个字符', trigger: 'blur' },
  ],
  img: [
    { max: 200, message: '设备图片路径不能超过 200 个字符', trigger: 'blur' },
  ],
  spec: [
    { max: 100, message: '型号规格不能超过 100 个字符', trigger: 'blur' },
  ],
  quantity: [
    {
      validator: (_, value, callback) => {
        if (value === null || value === undefined || value === '') {
          callback(new Error('请输入设备数量'))
          return
        }

        if (!Number.isInteger(Number(value)) || Number(value) < 0) {
          callback(new Error('数量必须是不小于 0 的整数'))
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
    lab_id: null,
    name: '',
    description: '',
    img: '',
    spec: '',
    quantity: 1,
    status: 1,
  }
}

async function loadEquipments() {
  loading.value = true

  try {
    const result = await listEquipments({
      page: page.value,
      pageSize: pageSize.value,
      keyword: activeKeyword.value,
    })

    equipments.value = result.items
    total.value = result.total
    page.value = result.page
    pageSize.value = result.page_size
    totalPages.value = result.total_pages
  } catch (error) {
    equipments.value = []
    total.value = 0
    totalPages.value = 0
    ElMessage.error(error.message || '设备列表获取失败')
  } finally {
    loading.value = false
  }
}

async function loadLabOptions() {
  if (labOptions.value.length) return

  try {
    const firstPage = await listLabs({ page: 1, pageSize: 100 })
    const options = [...firstPage.items]

    for (let currentPage = 2; currentPage <= firstPage.total_pages; currentPage += 1) {
      const result = await listLabs({ page: currentPage, pageSize: 100 })
      options.push(...result.items)
    }

    labOptions.value = options.map((lab) => ({
      value: lab.id,
      label: lab.name,
    }))
  } catch (error) {
    ElMessage.error(error.message || '实验室选项获取失败')
  }
}

function searchEquipments() {
  activeKeyword.value = searchKeyword.value.trim()
  page.value = 1
  loadEquipments()
}

function resetSearch() {
  searchKeyword.value = ''
  activeKeyword.value = ''
  page.value = 1
  loadEquipments()
}

function changePage(nextPage) {
  page.value = nextPage
  loadEquipments()
}

function changePageSize(nextSize) {
  pageSize.value = nextSize
  page.value = 1
  loadEquipments()
}

async function openCreateDialog() {
  if (!isAdmin.value) return

  editingEquipmentId.value = null
  Object.assign(form, createEmptyForm())
  formDialogVisible.value = true
  await loadLabOptions()
}

async function openEditDialog(row) {
  if (!isAdmin.value) return

  editingEquipmentId.value = row.id
  Object.assign(form, {
    lab_id: row.lab_id,
    name: row.name || '',
    description: row.description || '',
    img: row.img || '',
    spec: row.spec || '',
    quantity: Number(row.quantity),
    status: Number(row.status) === 0 ? 0 : 1,
  })
  formDialogVisible.value = true
  await loadLabOptions()
}

function beforeImageUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('设备图片只能是图片文件')
    return false
  }

  if (!isLt2M) {
    ElMessage.error('设备图片不能超过 2MB')
    return false
  }

  return true
}

async function handleImageUpload({ file }) {
  if (!beforeImageUpload(file)) {
    throw new Error('图片校验失败')
  }

  imageUploading.value = true

  try {
    const uploaded = await uploadEquipmentImage(file)
    form.img = uploaded.path
    ElMessage.success('设备图片上传成功')
    return uploaded
  } catch (error) {
    ElMessage.error(error.message || '设备图片上传失败')
    throw error
  } finally {
    imageUploading.value = false
  }
}

function removeImage() {
  form.img = ''
}

async function submitEquipment() {
  if (!isAdmin.value || formLoading.value) return

  try {
    await formRef.value.validate()
    formLoading.value = true

    const payload = {
      lab_id: form.lab_id,
      name: form.name,
      description: form.description,
      img: form.img,
      spec: form.spec,
      quantity: form.quantity,
      status: form.status,
    }

    if (editingEquipmentId.value) {
      await updateEquipment(editingEquipmentId.value, payload)
      ElMessage.success('设备信息已更新')
    } else {
      await createEquipment(payload)
      ElMessage.success('设备创建成功')
    }

    formDialogVisible.value = false
    await loadEquipments()
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
      `确定要删除设备“${row.name}”吗？删除后无法恢复。`,
      '删除设备',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )

    await deleteEquipment(row.id)
    ElMessage.success('设备已删除')

    if (equipments.value.length === 1 && page.value > 1) {
      page.value -= 1
    }

    await loadEquipments()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close' && error?.message) {
      ElMessage.error(error.message)
    }
  }
}

function statusLabel(status) {
  return Number(status) === 1 ? '正常' : '维修'
}

function statusTagType(status) {
  return Number(status) === 1 ? 'success' : 'warning'
}

onMounted(loadEquipments)
</script>

<template>
  <section class="equipments-page">
    <header class="page-header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageDescription }}</p>
      </div>

      <el-button v-if="isAdmin" type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增设备
      </el-button>
    </header>

    <el-card class="equipments-card" shadow="never">
      <div class="toolbar">
        <el-input
          v-model.trim="searchKeyword"
          class="toolbar__search"
          clearable
          placeholder="搜索设备名称、规格、说明或所属实验室"
          :disabled="loading"
          @keyup.enter="searchEquipments"
          @clear="resetSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="toolbar__actions">
          <el-button type="primary" :loading="loading" @click="searchEquipments">
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
        :data="equipments"
        class="equipments-table"
        row-key="id"
        empty-text="暂无设备数据"
      >
        <el-table-column prop="id" label="ID" width="72" />

        <el-table-column label="设备" min-width="240">
          <template #default="{ row }">
            <div class="equipment-cell">
              <el-image
                v-if="row.img"
                :src="resolveMediaUrl(row.img)"
                :preview-src-list="[resolveMediaUrl(row.img)]"
                preview-teleported
                fit="cover"
                class="equipment-cell__image"
              >
                <template #error>
                  <el-icon class="equipment-cell__image-error"><Picture /></el-icon>
                </template>
              </el-image>
              <div v-else class="equipment-cell__placeholder">
                <el-icon><Picture /></el-icon>
              </div>

              <div class="equipment-cell__identity">
                <strong>{{ row.name }}</strong>
                <span>{{ row.spec || '暂无型号规格' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="所属实验室" min-width="150">
          <template #default="{ row }">{{ row.lab_name || '--' }}</template>
        </el-table-column>

        <el-table-column prop="quantity" label="数量" width="86">
          <template #default="{ row }">{{ row.quantity }}</template>
        </el-table-column>

        <el-table-column label="状态" width="92">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="说明" min-width="220">
          <template #default="{ row }">
            <span class="description-text">{{ row.description || '--' }}</span>
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
      :title="editingEquipmentId ? '编辑设备' : '新增设备'"
      width="min(720px, calc(100vw - 28px))"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="96px"
        class="equipment-form"
      >
        <div class="form-grid form-grid--two">
          <el-form-item label="所属实验室" prop="lab_id">
            <el-select
              v-model="form.lab_id"
              filterable
              placeholder="请选择所属实验室"
            >
              <el-option
                v-for="lab in labOptions"
                :key="lab.value"
                :label="lab.label"
                :value="lab.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="设备名称" prop="name">
            <el-input
              v-model.trim="form.name"
              maxlength="50"
              show-word-limit
              placeholder="请输入设备名称"
            />
          </el-form-item>
        </div>

        <el-form-item label="设备说明" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="请输入设备说明"
          />
        </el-form-item>

        <div class="form-grid form-grid--two">
          <el-form-item label="型号规格" prop="spec">
            <el-input
              v-model.trim="form.spec"
              maxlength="100"
              placeholder="请输入型号规格"
            />
          </el-form-item>

          <el-form-item label="设备数量" prop="quantity">
            <el-input-number
              v-model="form.quantity"
              :min="0"
              :precision="0"
              :controls="false"
              placeholder="请输入设备数量"
            />
          </el-form-item>
        </div>

        <el-form-item label="设备状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="正常"
            inactive-text="维修"
          />
        </el-form-item>

        <el-form-item label="设备图片" prop="img">
          <div class="image-editor">
            <el-upload
              action="#"
              accept="image/*"
              :show-file-list="false"
              :http-request="handleImageUpload"
              :disabled="imageUploading"
            >
              <div class="image-upload">
                <el-image
                  v-if="form.img"
                  :src="resolveMediaUrl(form.img)"
                  fit="cover"
                  class="image-upload__preview"
                >
                  <template #error>
                    <el-icon class="equipment-cell__image-error"><Picture /></el-icon>
                  </template>
                </el-image>
                <div v-else class="image-upload__empty">
                  <el-icon><Upload /></el-icon>
                  <span>上传图片</span>
                </div>
              </div>
            </el-upload>

            <div class="image-editor__actions">
              <el-button
                v-if="form.img"
                text
                type="danger"
                :disabled="imageUploading"
                @click="removeImage"
              >
                <el-icon><Delete /></el-icon>
                移除图片
              </el-button>
              <span>支持 JPG、PNG，最大 2MB</span>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="formLoading || imageUploading"
          @click="submitEquipment"
        >
          {{ editingEquipmentId ? '保存修改' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.equipments-page {
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

.equipments-card {
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
  width: min(460px, 100%);
}

.toolbar__actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.equipments-table {
  width: 100%;
}

.equipment-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.equipment-cell__image,
.equipment-cell__placeholder {
  flex: 0 0 52px;
  width: 52px;
  height: 52px;
  border: 1px solid var(--app-border);
  border-radius: 6px;
}

.equipment-cell__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-secondary);
  background: var(--app-background);
}

.equipment-cell__image-error {
  color: var(--app-text-secondary);
}

.equipment-cell__identity {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.55;
}

.equipment-cell__identity strong,
.description-text {
  display: -webkit-box;
  overflow: hidden;
  color: var(--app-text);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.equipment-cell__identity span {
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

.equipment-form :deep(.el-select),
.equipment-form :deep(.el-input-number) {
  width: 100%;
}

.form-grid {
  display: grid;
  column-gap: 16px;
}

.form-grid--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-grid :deep(.el-form-item) {
  min-width: 0;
}

.image-editor {
  display: flex;
  align-items: center;
  gap: 14px;
}

.image-upload {
  width: 112px;
  height: 112px;
  overflow: hidden;
  border: 1px dashed var(--app-border);
  border-radius: 6px;
  background: var(--app-background);
}

.image-upload__preview {
  width: 100%;
  height: 100%;
}

.image-upload__empty {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.image-editor__actions {
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  gap: 8px;
  color: var(--app-text-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .equipments-page {
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

  .form-grid--two {
    grid-template-columns: minmax(0, 1fr);
  }

  .image-editor {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>