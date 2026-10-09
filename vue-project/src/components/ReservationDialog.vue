<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createReservation } from '@/api/reservation'
import { listEquipments } from '@/api/equipment'

const props = defineProps({
  modelValue: Boolean,
  labId: [Number, String],
  labName: String,
  equipmentId: [Number, String],
  equipmentName: String,
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const loading = ref(false)
const equipmentLoading = ref(false)
const equipmentOptions = ref([])
const form = reactive({
  equipment_id: null,
  date: '',
  start_time: '',
  end_time: '',
  remark: '',
})

const selectedEquipmentName = computed(() => {
  if (!form.equipment_id) return ''
  if (props.equipmentId && Number(props.equipmentId) === Number(form.equipment_id)) {
    return props.equipmentName || ''
  }
  return equipmentOptions.value.find((item) => item.id === form.equipment_id)?.name || ''
})

const targetName = computed(() => {
  const labName = props.labName || '实验室'
  return selectedEquipmentName.value ? `${labName} / ${selectedEquipmentName.value}` : labName
})

const rules = {
  date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    {
      validator: (_, value, callback) => {
        if (value && form.start_time && value <= form.start_time) {
          callback(new Error('结束时间必须晚于开始时间'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

async function loadEquipmentOptions() {
  if (!Number(props.labId)) {
    equipmentOptions.value = []
    return
  }

  equipmentLoading.value = true

  try {
    const result = await listEquipments({
      page: 1,
      pageSize: 100,
      labId: Number(props.labId),
    })
    equipmentOptions.value = result.items.filter((item) => Number(item.status) === 1)
  } catch (error) {
    equipmentOptions.value = []
    ElMessage.error(error.message || '设备选项获取失败')
  } finally {
    equipmentLoading.value = false
  }
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) return

    form.equipment_id = props.equipmentId ? Number(props.equipmentId) : null
    form.date = ''
    form.start_time = ''
    form.end_time = ''
    form.remark = ''
    formRef.value?.clearValidate()
    loadEquipmentOptions()
  },
)

function disabledDate(date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date.getTime() < today.getTime()
}

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  if (loading.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    await createReservation({
      lab_id: Number(props.labId),
      equipment_id: form.equipment_id || null,
      date: form.date,
      start_time: form.start_time,
      end_time: form.end_time,
      remark: form.remark,
    })
    ElMessage.success('预约提交成功')
    emit('success')
    close()
  } catch (error) {
    ElMessage.error(error.message || '预约失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="发起实验室预约"
    width="min(520px, calc(100vw - 28px))"
    destroy-on-close
    @update:model-value="close"
  >
    <el-alert
      class="reservation-target"
      type="info"
      :closable="false"
      show-icon
      :title="`预约对象：${targetName}`"
    />

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="预约设备">
        <el-select
          v-model="form.equipment_id"
          class="equipment-select"
          clearable
          :loading="equipmentLoading"
          placeholder="仅预约实验室"
        >
          <el-option label="仅预约实验室" :value="null" />
          <el-option
            v-for="equipment in equipmentOptions"
            :key="equipment.id"
            :label="equipment.name"
            :value="equipment.id"
          />
        </el-select>
        <div v-if="!equipmentLoading && !equipmentOptions.length" class="equipment-empty">
          该实验室暂无可预约设备
        </div>
      </el-form-item>

      <el-form-item label="预约日期" prop="date">
        <el-date-picker
          v-model="form.date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="请选择日期"
          :disabled-date="disabledDate"
          style="width: 100%"
        />
      </el-form-item>

      <div class="reservation-time">
        <el-form-item label="开始时间" prop="start_time">
          <el-time-select
            v-model="form.start_time"
            start="08:00"
            step="00:30"
            end="22:00"
            placeholder="开始时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="结束时间" prop="end_time">
          <el-time-select
            v-model="form.end_time"
            :start="form.start_time || '08:00'"
            step="00:30"
            end="22:30"
            placeholder="结束时间"
            style="width: 100%"
          />
        </el-form-item>
      </div>

      <el-form-item label="备注" prop="remark">
        <el-input
          v-model.trim="form.remark"
          type="textarea"
          :rows="3"
          maxlength="200"
          show-word-limit
          placeholder="可填写用途、人数等信息"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button :disabled="loading" @click="close">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">提交预约</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.reservation-target {
  margin-bottom: 18px;
}

.equipment-select {
  width: 100%;
}

.equipment-empty {
  margin-top: 5px;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.reservation-time {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

@media (max-width: 520px) {
  .reservation-time {
    grid-template-columns: 1fr;
  }
}
</style>
