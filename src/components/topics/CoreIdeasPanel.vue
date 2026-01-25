<template>
  <div class="bg-white rounded-xl border border-zinc-200 overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-lg">🧠</span>
        <h3 class="font-semibold text-zinc-800">算法思想</h3>
        <span class="text-sm text-zinc-500">{{ ideas.length }} 条</span>
      </div>
      <el-button v-if="canEdit" size="small" type="primary" plain @click="openAddDialog">
        <el-icon class="mr-1"><Plus /></el-icon>添加算法思想
      </el-button>
    </div>

    <!-- Ideas List -->
    <div class="p-4">
      <div v-if="ideas.length" class="space-y-3">
        <div 
          v-for="idea in ideas" 
          :key="idea.id" 
          class="p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md"
          :class="[
            idea.status === 'verified' ? 'bg-emerald-50 border-emerald-200' :
            idea.status === 'rejected' ? 'bg-rose-50 border-rose-200' :
            idea.status === 'superseded' ? 'bg-zinc-50 border-zinc-200 opacity-60' :
            'bg-white border-zinc-200'
          ]"
          @click="openEditDialog(idea)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <h4 class="font-medium text-zinc-800">{{ idea.title }}</h4>
              <p v-if="idea.ideaBody" class="text-sm text-zinc-600 mt-1 line-clamp-2">{{ idea.ideaBody }}</p>
            </div>
            <div class="text-right text-xs text-zinc-400 flex-shrink-0">
              <el-tag :type="getStatusType(idea.status)" size="small">
                {{ getStatusLabel(idea.status) }}
              </el-tag>
              <div class="mt-1">{{ idea.proposerName }}</div>
              <div class="mt-0.5">{{ formatDate(idea.createdAt) }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-8 text-zinc-400">
        <div class="text-4xl mb-2">💡</div>
        <p>暂无算法思想</p>
        <p class="text-sm mt-1">记录关键的算法认知和决策</p>
      </div>
    </div>

    <!-- Add/Edit Dialog -->
    <el-dialog 
      v-model="showDialog" 
      :title="editingIdea ? '编辑算法思想' : '添加算法思想'" 
      width="650px"
      :close-on-click-modal="false"
    >
      <el-form :model="ideaForm" label-position="top">
        <el-form-item label="一句话概括" required>
          <el-input v-model="ideaForm.title" placeholder="例如：我们不直接做X，而是把问题重构为Y" />
        </el-form-item>
        
        <el-form-item label="提出人" required>
          <el-select v-model="ideaForm.proposerId" class="w-full" filterable placeholder="选择提出人">
            <el-option 
              v-for="member in topicMembers" 
              :key="member.uniqueKey" 
              :value="member.userId" 
              :label="member.userName"
              :disabled="!member.userId"
            >
              <div class="flex items-center justify-between">
                <span>{{ member.userName }}</span>
                <span class="text-xs text-zinc-400">
                  {{ member.isDri ? 'DRI' : member.userRole === 'REVIEWER' ? '审核人' : member.userRole === 'CUSTOMER' ? 'PDT' : '成员' }}
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="editingIdea" label="状态">
          <el-radio-group v-model="ideaForm.status">
            <el-radio-button value="hypothesizing">假设中</el-radio-button>
            <el-radio-button value="verified">已验证</el-radio-button>
            <el-radio-button value="rejected">被否决</el-radio-button>
            <el-radio-button value="superseded">被替代</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-divider>核心内容</el-divider>
        
        <el-form-item label="💡 Idea 本体（是什么）">
          <el-input 
            v-model="ideaForm.ideaBody" 
            type="textarea" 
            :rows="3" 
            placeholder="我们不直接做 X，而是把问题重构为 Y..."
          />
        </el-form-item>
        
        <el-form-item label="❓ 出现动机（为什么）">
          <el-input 
            v-model="ideaForm.motivation" 
            type="textarea" 
            :rows="2" 
            placeholder="原方案在 A/B 场景下失败，瓶颈在于..."
          />
        </el-form-item>
        
        <el-form-item label="📊 关键证据">
          <el-input 
            v-model="ideaForm.evidence" 
            type="textarea" 
            :rows="2" 
            placeholder="仿真结果 / 对比实验 / 失败案例 / 数学推导..."
          />
        </el-form-item>
        
        <el-form-item label="🎯 影响与落点">
          <el-input 
            v-model="ideaForm.impact" 
            type="textarea" 
            :rows="2" 
            placeholder="影响了哪个模块 / 哪个参数 / 是否进入最终实现..."
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="flex justify-between">
          <el-button v-if="editingIdea" type="danger" text @click="deleteIdea">删除</el-button>
          <div class="flex gap-2 ml-auto">
            <el-button @click="showDialog = false">取消</el-button>
            <el-button type="primary" @click="saveIdea">{{ editingIdea ? '保存' : '创建' }}</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Plus } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { coreIdeasApi, ideaStatusLabels, type CoreIdea, type IdeaStatus } from '@/api/coreIdeas';
import { topicsApi } from '@/api/topics';
import dayjs from 'dayjs';

const props = defineProps<{
  topicId: number;
  stageInstances: any[];
  canEdit: boolean;
}>();

const emit = defineEmits(['refresh']);

const ideas = ref<CoreIdea[]>([]);
const topicMembers = ref<any[]>([]);
const showDialog = ref(false);
const editingIdea = ref<CoreIdea | null>(null);

const ideaForm = ref({
  title: '',
  proposerId: null as number | null,
  status: 'hypothesizing' as IdeaStatus,
  ideaBody: '',
  motivation: '',
  evidence: '',
  impact: '',
});

async function loadIdeas() {
  try {
    ideas.value = await coreIdeasApi.list(props.topicId);
  } catch (error) {
    console.error('Failed to load ideas:', error);
  }
}

async function loadTopicMembers() {
  try {
    const members = await topicsApi.getTopicMembers(props.topicId);
    // 添加唯一键并过滤有 userId 的成员
    topicMembers.value = members.map((m: any, idx: number) => ({
      ...m,
      uniqueKey: `${m.userId || m.slotId}-${idx}`,
    }));
  } catch (error) {
    console.error('Failed to load topic members:', error);
  }
}

function formatDate(date: string) {
  return dayjs(date).format('MM-DD HH:mm');
}

function getStatusLabel(status: IdeaStatus) {
  return ideaStatusLabels[status] || status;
}

function getStatusType(status: IdeaStatus): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<IdeaStatus, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    hypothesizing: 'warning',
    verified: 'success',
    rejected: 'danger',
    superseded: 'info',
  };
  return map[status] || '';
}

function openAddDialog() {
  editingIdea.value = null;
  resetForm();
  showDialog.value = true;
}

function openEditDialog(idea: CoreIdea) {
  editingIdea.value = idea;
  ideaForm.value = {
    title: idea.title,
    proposerId: idea.proposerId,
    status: idea.status,
    ideaBody: idea.ideaBody || '',
    motivation: idea.motivation || '',
    evidence: idea.evidence || '',
    impact: idea.impact || '',
  };
  showDialog.value = true;
}

async function saveIdea() {
  if (!ideaForm.value.title || !ideaForm.value.proposerId) {
    ElMessage.warning('请填写必填字段');
    return;
  }
  
  try {
    if (editingIdea.value) {
      await coreIdeasApi.update(props.topicId, editingIdea.value.id, {
        title: ideaForm.value.title,
        status: ideaForm.value.status,
        idea_body: ideaForm.value.ideaBody || undefined,
        motivation: ideaForm.value.motivation || undefined,
        evidence: ideaForm.value.evidence || undefined,
        impact: ideaForm.value.impact || undefined,
      });
      ElMessage.success('保存成功');
    } else {
      // 获取选中的提出人名字
      const selectedMember = topicMembers.value.find((m: any) => m.userId === ideaForm.value.proposerId);
      const proposerName = selectedMember?.userName || '';
      
      await coreIdeasApi.create(props.topicId, {
        title: ideaForm.value.title,
        proposer_id: ideaForm.value.proposerId,
        proposer_name: proposerName,
        idea_body: ideaForm.value.ideaBody || undefined,
        motivation: ideaForm.value.motivation || undefined,
        evidence: ideaForm.value.evidence || undefined,
        impact: ideaForm.value.impact || undefined,
      });
      ElMessage.success('创建成功');
    }
    
    showDialog.value = false;
    editingIdea.value = null;
    resetForm();
    await loadIdeas();
    emit('refresh');
  } catch (error) {
    ElMessage.error('操作失败');
  }
}

async function deleteIdea() {
  if (!editingIdea.value) return;
  
  try {
    await ElMessageBox.confirm('确定删除此算法思想？', '删除', { type: 'warning' });
    await coreIdeasApi.delete(props.topicId, editingIdea.value.id);
    ElMessage.success('已删除');
    showDialog.value = false;
    editingIdea.value = null;
    await loadIdeas();
    emit('refresh');
  } catch {}
}

function resetForm() {
  ideaForm.value = {
    title: '',
    proposerId: null,
    status: 'hypothesizing',
    ideaBody: '',
    motivation: '',
    evidence: '',
    impact: '',
  };
}

watch(showDialog, (val) => {
  if (!val) {
    editingIdea.value = null;
    resetForm();
  }
});

onMounted(async () => {
  await loadTopicMembers();
  await loadIdeas();
});

watch(() => props.topicId, async () => {
  await loadTopicMembers();
  await loadIdeas();
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
