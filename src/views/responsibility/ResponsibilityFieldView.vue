<template>
  <div class="responsibility-field-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">责任田</h1>
        <p class="page-subtitle">团队成员的专属领域和职责划分</p>
      </div>
      <div v-if="authStore.isAdmin" class="header-actions">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          accept=".xlsx,.xls"
        >
          <el-button type="primary" :icon="Upload" :loading="uploading">
            上传 Excel
          </el-button>
        </el-upload>
        <el-button
          v-if="data"
          type="danger"
          plain
          :icon="Delete"
          @click="handleDelete"
        >
          删除
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <section v-if="loading" class="tcgs-surface loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </section>

    <!-- 空状态 -->
    <section v-else-if="!data" class="tcgs-surface empty-state">
      <div class="empty-content">
        <el-icon class="empty-icon"><Grid /></el-icon>
        <h3 class="empty-title">暂无责任田数据</h3>
        <p class="empty-desc">
          {{ authStore.isAdmin ? '请上传 Excel 文件来定义责任田' : '管理员尚未上传责任田定义' }}
        </p>
      </div>
    </section>

    <!-- Excel 展示 -->
    <template v-else>
      <!-- 文件信息 -->
      <div class="file-info">
        <span class="file-name">{{ data.originalFilename }}</span>
        <span class="file-meta">
          由 {{ data.uploadedBy }} 上传于 {{ formatDate(data.uploadedAt) }}
        </span>
      </div>

      <!-- Sheet 选项卡 -->
      <el-tabs v-model="activeSheet" class="sheet-tabs">
        <el-tab-pane
          v-for="sheet in data.sheets"
          :key="sheet.name"
          :label="sheet.name"
          :name="sheet.name"
        >
          <div class="table-container">
            <table class="excel-table">
              <tbody>
                <tr v-for="(row, rowIndex) in sheet.rows" :key="rowIndex">
                  <td
                    v-for="(cell, colIndex) in row"
                    :key="colIndex"
                    v-show="!isMergedHidden(sheet, rowIndex, colIndex)"
                    :rowspan="getMergedRowspan(sheet, rowIndex, colIndex)"
                    :colspan="getMergedColspan(sheet, rowIndex, colIndex)"
                    :style="getCellStyle(sheet, colIndex)"
                    :class="{ 'header-cell': rowIndex === 0 }"
                  >
                    {{ cell }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { responsibilityApi, type ResponsibilityData, type SheetData, type MergedCell } from '@/api/responsibility';
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus';
import { Grid, Upload, Delete, Loading } from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const authStore = useAuthStore();

const loading = ref(true);
const uploading = ref(false);
const data = ref<ResponsibilityData | null>(null);
const activeSheet = ref('');

onMounted(async () => {
  await loadData();
});

async function loadData() {
  loading.value = true;
  try {
    const result = await responsibilityApi.getData();
    data.value = result.data;
    if (data.value && data.value.sheets.length > 0) {
      activeSheet.value = data.value.sheets[0].name;
    }
  } catch (error) {
    console.error('Failed to load responsibility data:', error);
  } finally {
    loading.value = false;
  }
}

async function handleFileChange(uploadFile: UploadFile) {
  if (!uploadFile.raw) return;

  uploading.value = true;
  try {
    const result = await responsibilityApi.upload(uploadFile.raw);
    data.value = result.data;
    if (data.value && data.value.sheets.length > 0) {
      activeSheet.value = data.value.sheets[0].name;
    }
    ElMessage.success('责任田数据已更新');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '上传失败');
  } finally {
    uploading.value = false;
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除责任田数据吗？', '删除确认', {
      type: 'warning',
    });
    await responsibilityApi.delete();
    data.value = null;
    activeSheet.value = '';
    ElMessage.success('责任田数据已删除');
  } catch (error) {
    // 用户取消或删除失败
  }
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm');
}

// 检查单元格是否被合并隐藏（不是合并区域的左上角）
function isMergedHidden(sheet: SheetData, rowIndex: number, colIndex: number): boolean {
  for (const merged of sheet.mergedCells) {
    if (
      rowIndex >= merged.startRow && rowIndex <= merged.endRow &&
      colIndex >= merged.startCol && colIndex <= merged.endCol
    ) {
      // 如果不是左上角单元格，则隐藏
      if (rowIndex !== merged.startRow || colIndex !== merged.startCol) {
        return true;
      }
    }
  }
  return false;
}

// 获取合并单元格的 rowspan
function getMergedRowspan(sheet: SheetData, rowIndex: number, colIndex: number): number {
  for (const merged of sheet.mergedCells) {
    if (rowIndex === merged.startRow && colIndex === merged.startCol) {
      return merged.endRow - merged.startRow + 1;
    }
  }
  return 1;
}

// 获取合并单元格的 colspan
function getMergedColspan(sheet: SheetData, rowIndex: number, colIndex: number): number {
  for (const merged of sheet.mergedCells) {
    if (rowIndex === merged.startRow && colIndex === merged.startCol) {
      return merged.endCol - merged.startCol + 1;
    }
  }
  return 1;
}

// 获取单元格样式
function getCellStyle(sheet: SheetData, colIndex: number): Record<string, string> {
  const width = sheet.colWidths[colIndex];
  if (width && width > 0) {
    return {
      minWidth: `${Math.max(width * 8, 60)}px`,
    };
  }
  return { minWidth: '80px' };
}
</script>

<style scoped>
.responsibility-field-page {
  padding: var(--space-6);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  flex-shrink: 0;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0 0;
}

.header-actions {
  display: flex;
  gap: var(--space-2);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-16);
  color: var(--color-text-secondary);
}

.empty-state {
  padding: var(--space-16) var(--space-6);
  flex: 1;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-2) 0;
}

.empty-desc {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.file-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}

.file-meta {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.sheet-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sheet-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.sheet-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
}

.table-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: white;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
}

.excel-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.excel-table td {
  border: 1px solid var(--color-border-light);
  padding: var(--space-2) var(--space-3);
  white-space: pre-wrap;
  word-break: break-word;
  vertical-align: middle;
  background: white;
  line-height: 1.5;
}

.excel-table td.header-cell {
  background: var(--color-neutral-100);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  position: sticky;
  top: 0;
  z-index: 1;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--space-3);
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .file-info {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-1);
  }
}
</style>
