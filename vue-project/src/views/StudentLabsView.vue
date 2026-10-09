<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Cpu,
  Location,
  OfficeBuilding,
  RefreshLeft,
  Search,
  User,
} from '@element-plus/icons-vue'
import { listLabs } from '@/api/lab'
import ReservationDialog from '@/components/ReservationDialog.vue'
import { resolveMediaUrl } from '@/api/auth'

const router = useRouter()
const loading = ref(false)
const labs = ref([])
const page = ref(1)
const pageSize = ref(8)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeKeyword = ref('')
const reservationVisible = ref(false)
const reservationLab = ref({})

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

function statusLabel(status) {
  return Number(status) === 1 ? '开放中' : '维护中'
}

function viewLabEquipments(lab) {
  router.push({
    path: `/home/student/labs/${lab.id}/equipments`,
    query: {
      lab_name: lab.name || '',
      lab_img: lab.img || '',
    },
  })
}

function reserveLab(lab) {
  reservationLab.value = lab
  reservationVisible.value = true
}

function goBack() {
  router.push('/home')
}

onMounted(loadLabs)
</script>

<template>
  <section class="student-labs-page">
    <header class="page-header">
      <div class="page-header__content">
        <h1>实验室预约</h1>
        <p>浏览实验室资源，选择实验室查看设备或发起预约。</p>
      </div>

      <div class="page-header__summary">
        <el-icon><OfficeBuilding /></el-icon>
        <div>
          <strong>{{ total }}</strong>
          <span>个实验室</span>
        </div>
      </div>
    </header>

    <el-card class="search-card" shadow="never">
      <div class="search-bar">
        <el-input
          v-model.trim="searchKeyword"
          class="search-bar__input"
          clearable
          placeholder="搜索实验室名称、地点或说明"
          :disabled="loading"
          @keyup.enter="searchLabs"
          @clear="resetSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-button type="primary" :loading="loading" @click="searchLabs">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>

        <el-button :disabled="loading" @click="resetSearch">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
    </el-card>

    <div v-loading="loading" class="labs-content">
      <div v-if="labs.length" class="labs-grid">
        <article v-for="lab in labs" :key="lab.id" class="lab-card">
          <div class="lab-card__media">
            <img
              v-if="lab.img"
              :src="resolveMediaUrl(lab.img)"
              :alt="lab.name"
              class="lab-card__image"
            />
            <div v-else class="lab-card__placeholder">
              <el-icon><OfficeBuilding /></el-icon>
              <span>暂无实验室图片</span>
            </div>

            <el-tag
              class="lab-card__status"
              :type="Number(lab.status) === 1 ? 'success' : 'warning'"
              effect="dark"
            >
              {{ statusLabel(lab.status) }}
            </el-tag>
          </div>

          <div class="lab-card__body">
            <div class="lab-card__title">
              <h2>{{ lab.name }}</h2>
              <span>#{{ lab.id }}</span>
            </div>

            <p class="lab-card__description">
              {{ lab.description || '暂无实验室说明' }}
            </p>

            <div class="lab-card__meta">
              <div v-if="lab.location">
                <el-icon><Location /></el-icon>
                <span>{{ lab.location }}</span>
              </div>
              <div v-if="lab.open_time || lab.close_time">
                <el-icon><Clock /></el-icon>
                <span>{{ lab.open_time || '--' }} - {{ lab.close_time || '--' }}</span>
              </div>
              <div v-if="lab.capacity !== null">
                <el-icon><User /></el-icon>
                <span>可容纳 {{ lab.capacity }} 人</span>
              </div>
            </div>
          </div>

          <div class="lab-card__actions">
            <el-button type="primary" plain @click="viewLabEquipments(lab)">
              <el-icon><Cpu /></el-icon>
              查看设备
            </el-button>
            <el-button type="primary" @click="reserveLab(lab)">
              <el-icon><Calendar /></el-icon>
              立即预约
            </el-button>
          </div>
        </article>
      </div>

      <el-empty v-else-if="!loading" description="暂未找到符合条件的实验室" />
    </div>

    <footer v-if="total > 0" class="pagination-bar">
      <span>共 {{ total }} 个实验室，第 {{ page }} / {{ Math.max(totalPages, 1) }} 页</span>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[8, 12, 16, 24]"
        layout="sizes, prev, pager, next"
        background
        @current-change="changePage"
        @size-change="changePageSize"
      />
    </footer>
    <ReservationDialog
      v-model="reservationVisible"
      :lab-id="reservationLab.id"
      :lab-name="reservationLab.name"
    />
  </section>
</template>

<style scoped>
.student-labs-page {
  min-height: calc(100vh - 64px);
  padding: 28px;
  background: #f8fafc;
}

.page-header {
  display: flex;
  max-width: 1320px;
  margin: 0 auto 20px;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.page-header__back {
  margin: 0 0 8px -10px;
  padding-left: 10px;
  color: var(--app-text-secondary);
}

.page-header h1 {
  margin: 0;
  color: var(--app-text);
  font-size: 26px;
  line-height: 1.35;
}

.page-header p {
  margin: 7px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
}

.page-header__summary {
  display: flex;
  min-width: 152px;
  padding: 16px 18px;
  border: 1px solid var(--app-border);
  border-radius: 10px;
  align-items: center;
  gap: 12px;
  background: #ffffff;
}

.page-header__summary > .el-icon {
  color: var(--app-primary);
  font-size: 26px;
}

.page-header__summary div {
  display: flex;
  flex-direction: column;
}

.page-header__summary strong {
  color: var(--app-text);
  font-size: 20px;
}

.page-header__summary span {
  color: var(--app-text-secondary);
  font-size: 12px;
}

.search-card {
  max-width: 1320px;
  margin: 0 auto 20px;
  border-color: var(--app-border);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar__input {
  max-width: 520px;
}

.labs-content {
  max-width: 1320px;
  min-height: 360px;
  margin: 0 auto;
}

.labs-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.lab-card {
  display: flex;
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  flex-direction: column;
  background: #ffffff;
  box-shadow: 0 5px 18px rgba(15, 23, 42, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.lab-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.1);
}

.lab-card__media {
  position: relative;
  overflow: hidden;
  aspect-ratio: 16 / 10;
  background: #eef2f7;
}

.lab-card__image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.25s ease;
}

.lab-card:hover .lab-card__image {
  transform: scale(1.035);
}

.lab-card__placeholder {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 9px;
  color: #94a3b8;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
}

.lab-card__placeholder .el-icon {
  font-size: 34px;
}

.lab-card__placeholder span {
  font-size: 12px;
}

.lab-card__status {
  position: absolute;
  top: 12px;
  right: 12px;
}

.lab-card__body {
  display: flex;
  min-height: 190px;
  padding: 18px;
  flex: 1;
  flex-direction: column;
}

.lab-card__title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.lab-card__title h2 {
  margin: 0;
  overflow: hidden;
  color: var(--app-text);
  font-size: 17px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lab-card__title span {
  flex: 0 0 auto;
  color: #94a3b8;
  font-size: 11px;
}

.lab-card__description {
  display: -webkit-box;
  min-height: 44px;
  margin: 10px 0 15px;
  overflow: hidden;
  color: var(--app-text-secondary);
  font-size: 13px;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.lab-card__meta {
  display: flex;
  margin-top: auto;
  flex-direction: column;
  gap: 8px;
}

.lab-card__meta > div {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.lab-card__meta .el-icon {
  flex: 0 0 auto;
  color: var(--app-primary);
}

.lab-card__meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lab-card__actions {
  display: grid;
  padding: 13px 18px 18px;
  border-top: 1px solid #f1f5f9;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.lab-card__actions .el-button {
  width: 100%;
  margin: 0;
}

.pagination-bar {
  display: flex;
  max-width: 1320px;
  margin: 22px auto 0;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  color: var(--app-text-secondary);
  font-size: 13px;
}

@media (max-width: 1180px) {
  .labs-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .labs-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .student-labs-page {
    padding: 20px 14px;
  }

  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .page-header__summary {
    width: fit-content;
  }

  .search-bar {
    align-items: stretch;
    flex-wrap: wrap;
  }

  .search-bar__input {
    width: 100%;
    max-width: none;
    flex-basis: 100%;
  }

  .labs-grid {
    grid-template-columns: 1fr;
  }

  .pagination-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .pagination-bar :deep(.el-pagination) {
    max-width: 100%;
  }
}
</style>
