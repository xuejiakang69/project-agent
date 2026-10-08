<script setup>
import { Compass } from '@element-plus/icons-vue'

defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
  inverse: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <div class="app-brand" :class="{ 'app-brand--inverse': inverse }">
    <span class="app-brand__mark" aria-hidden="true">
      <el-icon><Compass /></el-icon>
    </span>
    <span v-if="!compact" class="app-brand__text">
      <strong>智能实验室</strong>
      <small>预约系统</small>
    </span>
  </div>
</template>

<style scoped>
.app-brand {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
}

.app-brand__mark {
  display: inline-flex;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #ffffff;
  background: var(--app-primary);
  font-size: 20px;
}

.app-brand__text {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.15;
}

.app-brand__text strong {
  color: var(--app-text);
  font-size: 17px;
  font-weight: 700;
}

.app-brand__text small {
  margin-top: 3px;
  color: var(--app-text-secondary);
  font-size: 11px;
  font-weight: 500;
}

.app-brand--inverse .app-brand__mark {
  color: #111827;
  background: #ffffff;
}

.app-brand--inverse .app-brand__text strong {
  color: #ffffff;
}

.app-brand--inverse .app-brand__text small {
  color: #cbd5e1;
}
</style>
