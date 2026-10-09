<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Calendar,
  Cpu,
  OfficeBuilding,
  RefreshLeft,
  Search,
} from '@element-plus/icons-vue'
import { listEquipments } from '@/api/equipment'
import { resolveMediaUrl } from '@/api/auth'

const route = useRoute()
const router = useRouter()

const labId = Number(route.params.labId)
const labName = String(route.query.lab_name || '').trim()
const labImage = String(route.query.lab_img || '').trim()

const loading = ref(false)
const equipments = ref([])
const page = ref(1)
const pageSize = ref(8)
const total = ref(0)
const totalPages = ref(0)
const searchKeyword = ref('')
const activeKeyword = ref('')

async function loadEquipments() {
  if (!Number.isInteger(labId) || labId <= 0) {
    ElMessage.error('实验室参数不正确')
    return
  }

  loading.value = true

  try {
    const result = await listEquipments({
      page: page.value,
      pageSize: pageSize.value,
      keyword: activeKeyword.value,
      labId,
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

function statusLabel(status) {
  return Number(status) === 1 ? '正常' : '维修中'
}

function reserveLab() {
  ElMessage.info('预约功能待开发')
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }

  router.push('/home/student-labs')
}

onMounted(loadEquipments)
</script>

<template>
  <section class="student-equipments-page">
    <header class="page-header">
      <div class="page-header__content">
        <div>
          <span class="page-header__eyebrow">实验室设备</span>
          <h1>{{ labName || `实验室 #${labId}` }}</h1>
          <p>查看该实验室当前配置的设备、数量和运行状态。</p>
        </div>
        <div>
          <el-button type="primary" size="large" @click="goBack">
            <ArrowLeft />
            返回上一页
          </el-button>
          <el-button type="primary" size="large" @click="reserveLab">
            <el-icon>
              <Calendar />
            </el-icon>
            预约实验室
          </el-button>
        </div>

      </div>
    </header>

    <el-card class="lab-banner" shadow="never">
      <div class="lab-banner__media">
        <img v-if="labImage" :src="resolveMediaUrl(labImage)" :alt="labName || '实验室'" />
        <el-icon v-else>
          <OfficeBuilding />
        </el-icon>
      </div>

      <div class="lab-banner__content">
        <span>当前实验室</span>
        <strong>{{ labName || `实验室 #${labId}` }}</strong>
        <p>设备仅提供查看功能，如需使用请先发起实验室预约。</p>
      </div>

      <div class="lab-banner__count">
        <el-icon>
          <Cpu />
        </el-icon>
        <div>
          <strong>{{ total }}</strong>
          <span>项设备</span>
        </div>
      </div>
    </el-card>

    <el-card class="search-card" shadow="never">
      <div class="search-bar">
        <el-input v-model.trim="searchKeyword" class="search-bar__input" clearable placeholder="搜索设备名称、规格或说明"
          :disabled="loading" @keyup.enter="searchEquipments" @clear="resetSearch">
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>

        <el-button type="primary" :loading="loading" @click="searchEquipments">
          <el-icon>
            <Search />
          </el-icon>
          搜索
        </el-button>

        <el-button :disabled="loading" @click="resetSearch">
          <el-icon>
            <RefreshLeft />
          </el-icon>
          重置
        </el-button>
      </div>
    </el-card>

    <div v-loading="loading" class="equipment-content">
      <div v-if="equipments.length" class="equipment-grid">
        <article v-for="equipment in equipments" :key="equipment.id" class="equipment-card">
          <div class="equipment-card__media">
            <img v-if="equipment.img" :src="resolveMediaUrl(equipment.img)" :alt="equipment.name" />
            <div v-else class="equipment-card__placeholder">
              <el-icon>
                <Cpu />
              </el-icon>
              <span>暂无设备图片</span>
            </div>

            <el-tag class="equipment-card__status" :type="Number(equipment.status) === 1 ? 'success' : 'warning'"
              effect="dark">
              {{ statusLabel(equipment.status) }}
            </el-tag>
          </div>

          <div class="equipment-card__body">
            <div class="equipment-card__title">
              <h2>{{ equipment.name }}</h2>
              <span>#{{ equipment.id }}</span>
            </div>

            <p>{{ equipment.description || '暂无设备说明' }}</p>

            <div class="equipment-card__details">
              <div>
                <span>规格</span>
                <strong>{{ equipment.spec || '--' }}</strong>
              </div>
              <div>
                <span>数量</span>
                <strong>{{ equipment.quantity }}</strong>
              </div>
            </div>
          </div>

          <div class="equipment-card__actions">
            <el-button type="primary" @click="reserveLab">
              <el-icon>
                <Calendar />
              </el-icon>
              预约使用
            </el-button>
          </div>
        </article>
      </div>

      <el-empty v-else-if="!loading" description="该实验室暂未配置设备" />
    </div>

    <footer v-if="total > 0" class="pagination-bar">
      <span>共 {{ total }} 项设备，第 {{ page }} / {{ Math.max(totalPages, 1) }} 页</span>
      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
        :page-sizes="[8, 12, 16, 24]" layout="sizes, prev, pager, next" background @current-change="changePage"
        @size-change="changePageSize" />
    </footer>
  </section>
</template>

<style scoped>
.student-equipments-page {
  min-height: calc(100vh - 64px);
  padding: 24px 28px 30px;
  background: #f8fafc;
}

.page-header,
.lab-banner,
.search-card,
.equipment-content,
.pagination-bar {
  max-width: 1320px;
  margin-right: auto;
  margin-left: auto;
}

.page-header__back {
  margin: 0 0 12px -10px;
  padding-left: 10px;
  color: var(--app-text-secondary);
}

.page-header__content {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.page-header__eyebrow {
  color: var(--app-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.page-header h1 {
  margin: 5px 0 0;
  color: var(--app-text);
  font-size: 26px;
  line-height: 1.35;
}

.page-header p {
  margin: 7px 0 0;
  color: var(--app-text-secondary);
  font-size: 14px;
}

.lab-banner {
  margin-bottom: 18px;
  overflow: hidden;
  border-color: var(--app-border);
}

.lab-banner :deep(.el-card__body) {
  display: grid;
  padding: 18px;
  align-items: center;
  grid-template-columns: 132px minmax(0, 1fr) auto;
  gap: 20px;
}

.lab-banner__media {
  overflow: hidden;
  width: 132px;
  height: 86px;
  border-radius: 9px;
  background: #e2e8f0;
}

.lab-banner__media img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.lab-banner__media .el-icon {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 31px;
}

.lab-banner__content span {
  color: var(--app-text-secondary);
  font-size: 12px;
}

.lab-banner__content strong {
  display: block;
  margin-top: 3px;
  color: var(--app-text);
  font-size: 19px;
}

.lab-banner__content p {
  margin: 7px 0 0;
  color: var(--app-text-secondary);
  font-size: 13px;
}

.lab-banner__count {
  display: flex;
  min-width: 130px;
  padding: 13px 16px;
  border-radius: 9px;
  align-items: center;
  gap: 11px;
  background: #eff6ff;
}

.lab-banner__count>.el-icon {
  color: var(--app-primary);
  font-size: 25px;
}

.lab-banner__count div {
  display: flex;
  flex-direction: column;
}

.lab-banner__count strong {
  color: var(--app-text);
  font-size: 19px;
}

.lab-banner__count span {
  color: var(--app-text-secondary);
  font-size: 11px;
}

.search-card {
  margin-bottom: 20px;
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

.equipment-content {
  min-height: 350px;
}

.equipment-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.equipment-card {
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

.equipment-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.1);
}

.equipment-card__media {
  position: relative;
  overflow: hidden;
  aspect-ratio: 16 / 10;
  background: #eef2f7;
}

.equipment-card__media img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.25s ease;
}

.equipment-card:hover .equipment-card__media img {
  transform: scale(1.035);
}

.equipment-card__placeholder {
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

.equipment-card__placeholder .el-icon {
  font-size: 34px;
}

.equipment-card__placeholder span {
  font-size: 12px;
}

.equipment-card__status {
  position: absolute;
  top: 12px;
  right: 12px;
}

.equipment-card__body {
  display: flex;
  min-height: 185px;
  padding: 18px;
  flex: 1;
  flex-direction: column;
}

.equipment-card__title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.equipment-card__title h2 {
  margin: 0;
  overflow: hidden;
  color: var(--app-text);
  font-size: 17px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.equipment-card__title span {
  flex: 0 0 auto;
  color: #94a3b8;
  font-size: 11px;
}

.equipment-card__body>p {
  display: -webkit-box;
  min-height: 44px;
  margin: 10px 0 16px;
  overflow: hidden;
  color: var(--app-text-secondary);
  font-size: 13px;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.equipment-card__details {
  display: grid;
  margin-top: auto;
  padding-top: 13px;
  border-top: 1px solid #f1f5f9;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.equipment-card__details div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.equipment-card__details span {
  color: var(--app-text-secondary);
  font-size: 11px;
}

.equipment-card__details strong {
  overflow: hidden;
  color: var(--app-text);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.equipment-card__actions {
  padding: 13px 18px 18px;
}

.equipment-card__actions .el-button {
  width: 100%;
  margin: 0;
}

.pagination-bar {
  display: flex;
  margin-top: 22px;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  color: var(--app-text-secondary);
  font-size: 13px;
}

@media (max-width: 1180px) {
  .equipment-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .equipment-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .lab-banner :deep(.el-card__body) {
    grid-template-columns: 112px minmax(0, 1fr);
  }

  .lab-banner__media {
    width: 112px;
    height: 80px;
  }

  .lab-banner__count {
    display: none;
  }
}

@media (max-width: 680px) {
  .student-equipments-page {
    padding: 20px 14px 28px;
  }

  .page-header__content {
    align-items: stretch;
    flex-direction: column;
  }

  .page-header h1 {
    font-size: 22px;
  }

  .lab-banner :deep(.el-card__body) {
    grid-template-columns: 1fr;
  }

  .lab-banner__media {
    width: 100%;
    height: 160px;
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

  .equipment-grid {
    grid-template-columns: 1fr;
  }

  .pagination-bar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
