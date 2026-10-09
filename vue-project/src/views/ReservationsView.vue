<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshLeft, Search } from '@element-plus/icons-vue'
import { auditReservation, listReservations, revokeReservation } from '@/api/reservation'

const props = defineProps({
  mode: {
    type: String,
    default: 'mine',
    validator: (value) => ['mine', 'all'].includes(value),
  },
})

const isMine = computed(() => props.mode === 'mine')
const pageTitle = computed(() => (isMine.value ? '我的预约' : '已预约'))
const pageDescription = computed(() =>
  isMine.value ? '查看和管理本人提交的实验室及设备预约。' : '查看系统内全部用户的实验室及设备预约记录。',
)

const loading = ref(false)
const reservations = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeKeyword = ref('')
const statusFilter = ref(null)
const activeStatus = ref(null)

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '待审核', value: 0 },
  { label: '已通过', value: 1 },
  { label: '已拒绝', value: 2 },
  { label: '已取消', value: 3 },
]

function statusInfo(status) {
  const map = {
    0: { label: '待审核', type: 'warning' },
    1: { label: '已通过', type: 'success' },
    2: { label: '已拒绝', type: 'danger' },
    3: { label: '已取消', type: 'info' },
  }
  return map[Number(status)] || { label: '未知', type: 'info' }
}

async function loadReservations() {
  loading.value = true

  try {
    const result = await listReservations({
      page: page.value,
      pageSize: pageSize.value,
      status: activeStatus.value,
      keyword: activeKeyword.value,
    })

    reservations.value = result.items
    total.value = result.total
    page.value = result.page
    pageSize.value = result.page_size
    totalPages.value = result.total_pages
  } catch (error) {
    reservations.value = []
    total.value = 0
    totalPages.value = 0
    ElMessage.error(error.message || '预约列表获取失败')
  } finally {
    loading.value = false
  }
}

function searchReservations() {
  activeKeyword.value = searchKeyword.value.trim()
  activeStatus.value = statusFilter.value
  page.value = 1
  loadReservations()
}

function resetSearch() {
  searchKeyword.value = ''
  activeKeyword.value = ''
  statusFilter.value = null
  activeStatus.value = null
  page.value = 1
  loadReservations()
}

function changePage(nextPage) {
  page.value = nextPage
  loadReservations()
}

function changePageSize(nextSize) {
  pageSize.value = nextSize
  page.value = 1
  loadReservations()
}

async function cancelReservation(reservation) {
  try {
    await ElMessageBox.confirm('确定要取消这条预约吗？', '取消预约', {
      type: 'warning',
      confirmButtonText: '确定取消',
      cancelButtonText: '暂不取消',
    })
  } catch {
    return
  }

  try {
    await revokeReservation(reservation.id)
    ElMessage.success('预约已取消')
    await loadReservations()
  } catch (error) {
    ElMessage.error(error.message || '取消预约失败')
  }
}


async function auditReservationRecord(reservation, status) {
  const action = status === 1 ? '通过' : '拒绝'

  try {
    await ElMessageBox.confirm(`确定要${action}这条预约吗？`, `${action}预约`, {
      type: status === 1 ? 'success' : 'warning',
      confirmButtonText: `确定${action}`,
      cancelButtonText: '暂不处理',
    })
  } catch {
    return
  }

  try {
    await auditReservation(reservation.id, status)
    ElMessage.success(`预约已${action}`)
    await loadReservations()
  } catch (error) {
    ElMessage.error(error.message || `${action}预约失败`)
  }
}
onMounted(loadReservations)
</script>

<template>
  <section class="reservations-page">
    <header class="page-header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageDescription }}</p>
      </div>
      <div class="page-summary">
        <strong>{{ total }}</strong>
        <span>条预约</span>
      </div>
    </header>

    <el-card class="search-card" shadow="never">
      <div class="search-bar">
        <el-select
          v-model="statusFilter"
          class="status-select"
          placeholder="预约状态"
          :disabled="loading"
          @change="searchReservations"
        >
          <el-option
            v-for="item in statusOptions"
            :key="String(item.value)"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <el-input
          v-model.trim="searchKeyword"
          class="search-input"
          clearable
          :placeholder="isMine ? '搜索实验室或设备名称' : '搜索预约人、实验室或设备'"
          :disabled="loading"
          @keyup.enter="searchReservations"
          @clear="resetSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-button type="primary" :loading="loading" @click="searchReservations">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button :disabled="loading" @click="resetSearch">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
    </el-card>

    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="reservations"
        row-key="id"
        empty-text="暂无预约记录"
      >
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column v-if="!isMine" prop="user_name" label="预约人" min-width="110" />
        <el-table-column prop="lab_name" label="实验室" min-width="130" show-overflow-tooltip />
        <el-table-column label="设备" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.equipment_name || '仅预约实验室' }}</template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="112" />
        <el-table-column label="时间" width="122">
          <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
        </el-table-column>
        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <el-tag :type="statusInfo(row.status).type">
              {{ statusInfo(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="提交时间" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="168" fixed="right">
          <template #default="{ row }">
            <template v-if="isMine">
              <el-button
                v-if="row.status === 0 || row.status === 1"
                type="danger"
                text
                @click="cancelReservation(row)"
              >
                取消预约
              </el-button>
              <span v-else class="no-action">--</span>
            </template>
            <template v-else-if="row.status === 0">
              <el-button type="success" text @click="auditReservationRecord(row, 1)">
                通过
              </el-button>
              <el-button type="danger" text @click="auditReservationRecord(row, 2)">
                拒绝
              </el-button>
            </template>
            <span v-else class="no-action">--</span>
          </template>
        </el-table-column>
      </el-table>

      <footer v-if="total > 0" class="pagination-bar">
        <span>共 {{ total }} 条，第 {{ page }} / {{ Math.max(totalPages, 1) }} 页</span>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="sizes, prev, pager, next"
          background
          @current-change="changePage"
          @size-change="changePageSize"
        />
      </footer>
    </el-card>
  </section>
</template>

<style scoped>
.reservations-page {
  padding: 28px;
  background: #f8fafc;
}

.page-header,
.search-card,
.table-card {
  max-width: 1320px;
  margin-right: auto;
  margin-left: auto;
}

.page-header {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
}

.page-header h1 {
  margin: 0;
  color: var(--app-text);
  font-size: 26px;
}

.page-header p {
  margin: 7px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
}

.page-summary {
  display: flex;
  min-width: 120px;
  padding: 14px 18px;
  border: 1px solid var(--app-border);
  border-radius: 9px;
  align-items: baseline;
  gap: 7px;
  background: #ffffff;
}

.page-summary strong {
  color: var(--app-primary);
  font-size: 22px;
}

.page-summary span {
  color: var(--app-text-secondary);
  font-size: 12px;
}

.search-card {
  margin-bottom: 18px;
  border-color: var(--app-border);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-select {
  width: 150px;
}

.search-input {
  max-width: 520px;
}

.table-card {
  border-color: var(--app-border);
}

.pagination-bar {
  display: flex;
  margin-top: 20px;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  color: var(--app-text-secondary);
  font-size: 13px;
}

.no-action {
  color: var(--app-text-secondary);
}

@media (max-width: 680px) {
  .reservations-page {
    padding: 20px 14px 28px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .search-bar {
    align-items: stretch;
    flex-wrap: wrap;
  }

  .status-select,
  .search-input {
    width: 100%;
    max-width: none;
    flex-basis: 100%;
  }

  .pagination-bar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
