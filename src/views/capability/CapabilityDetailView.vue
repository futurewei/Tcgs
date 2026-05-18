<template>
  <div v-if="detailLoading" class="loading-state">
    <el-icon class="is-loading"><Loading /></el-icon>
    <span>加载中...</span>
  </div>

  <div v-else-if="!cap" class="empty-state tcgs-surface">
    <h3>能力不存在</h3>
    <el-button @click="router.push('/capabilities')">返回列表</el-button>
  </div>

  <div v-else class="capability-detail-page">
    <!-- Header -->
    <div class="detail-header">
      <el-button text :icon="ArrowLeft" @click="router.push('/capabilities')">返回</el-button>
      <h1 class="detail-title">{{ cap.name }}</h1>
      <el-button v-if="!editingBasic" size="small" @click="editingBasic = true">编辑信息</el-button>
    </div>

    <!-- Edit Basic Info -->
    <section v-if="editingBasic" class="detail-section tcgs-surface">
      <el-form :model="editForm" label-position="top" class="edit-form">
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="名称"><el-input v-model="editForm.name" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="产品线">
            <el-select v-model="editForm.productLine" style="width:100%">
              <el-option v-for="pl in PRODUCT_LINES" :key="pl.value" :label="pl.label" :value="pl.value" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="风险">
            <el-select v-model="editForm.riskStatus" style="width:100%">
              <el-option v-for="rs in RISK_STATUSES" :key="rs.value" :label="rs.label" :value="rs.value" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="Owner">
            <el-select v-model="editForm.ownerId" filterable clearable style="width:100%">
              <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="备份Owner">
            <el-select v-model="editForm.backupOwnerId" filterable clearable style="width:100%">
              <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="责任田">
            <el-select v-model="editRespFieldId" filterable clearable style="width:100%" @change="onDetailRespChange">
              <el-option v-for="rf in respFields" :key="rf.id" :label="rf.name" :value="rf.id">
                <span>{{ rf.name }}</span>
                <span v-if="rf.ownerName" style="font-size:12px;color:var(--color-text-muted)"> — {{ rf.ownerName }}</span>
              </el-option>
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-form-item label="分类">
          <el-tree-select v-model="editForm.categoryId" :data="categoryTree" :props="{label:'name',value:'id',children:'children'}" placeholder="选择分类" check-strictly filterable style="width:100%" />
        </el-form-item>
        <el-form-item label="简介"><el-input v-model="editForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSaveBasic">保存</el-button>
        <el-button @click="editingBasic = false">取消</el-button>
      </el-form>
    </section>

    <!-- Read-only Basic Info -->
    <section v-else class="detail-section tcgs-surface info-bar">
      <div class="info-bar-row">
        <span v-if="cap.categoryPath" class="info-badge info-badge--cat">{{ cap.categoryPath }}</span>
        <span class="info-badge">{{ PRODUCT_LINE_LABELS[cap.productLine] || cap.productLine }}</span>
        <span :class="['info-badge', `info-badge--${(cap.riskStatus||'normal').toLowerCase()}`]">{{ RISK_LABELS[cap.riskStatus] || cap.riskStatus }}</span>
        <span class="info-badge info-badge--owner">{{ cap.owner?.name || '未指定' }}</span>
        <span v-if="cap.responsibilityFieldName" class="info-badge info-badge--resp">{{ cap.responsibilityFieldName }}</span>
      </div>
      <p v-if="cap.description" class="info-desc">{{ cap.description }}</p>
    </section>

    <!-- ==================== Generation Swiper ==================== -->
    <section class="detail-section">
      <div class="section-header">
        <h2 class="section-title">
          能力代际
          <span class="gen-count-badge">{{ sortedGenerations.length }}</span>
        </h2>
        <el-button size="small" type="primary" :icon="Plus" @click="openGenDialog()">新增代际</el-button>
      </div>

      <!-- Horizontal generation cards -->
      <div v-if="sortedGenerations.length" class="gen-swiper-wrapper">
        <div class="gen-swiper">
          <div
            v-for="gen in sortedGenerations"
            :key="gen.id"
            :class="['gen-swiper-card', { 'gen-swiper-card--active': activeGenId === gen.id }]"
            @click="selectGen(gen.id)"
          >
            <div class="gen-swiper-code">{{ gen.generationCode }}</div>
            <div class="gen-swiper-name">{{ gen.name }}</div>
            <div class="gen-swiper-tags">
              <span :class="['tag', `tag--${(gen.status||'').toLowerCase()}`]">{{ GEN_STATUS_LABELS[gen.status] || gen.status }}</span>
              <span class="tag tag--maturity">{{ MATURITY_LABELS[gen.maturityLevel] || gen.maturityLevel }}</span>
            </div>
            <div class="gen-swiper-stats">
              <span>课题 {{ gen.relatedTopics?.length || 0 }}</span>
              <span>问题 {{ gen.relatedIssues?.length || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="empty-block">暂无代际。点击「新增代际」创建第一个版本。</div>

      <!-- Selected Generation Detail -->
      <div v-if="activeGen" class="gen-detail">
        <div class="gen-detail-header">
          <div>
            <span class="gen-detail-code">{{ activeGen.generationCode }}</span>
            <span class="gen-detail-name">{{ activeGen.name }}</span>
            <span v-if="activeGen.version" class="gen-detail-version">{{ activeGen.version }}</span>
          </div>
          <div class="gen-detail-badges">
            <span :class="['gen-detail-badge', `gen-detail-badge--${(activeGen.status||'').toLowerCase()}`]">{{ GEN_STATUS_LABELS[activeGen.status] || activeGen.status }}</span>
            <span class="gen-detail-badge gen-detail-badge--maturity">{{ MATURITY_LABELS[activeGen.maturityLevel] || activeGen.maturityLevel }}</span>
            <span v-if="activeGen.owner" class="gen-detail-badge gen-detail-badge--owner">Owner: {{ activeGen.owner.name }}</span>
            <el-dropdown trigger="click" :teleported="true">
              <el-button text size="small">操作 ▾</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="setProductionGen(activeGen.id)">设为量产版本</el-dropdown-item>
                  <el-dropdown-item @click="setResearchGen(activeGen.id)">设为研发版本</el-dropdown-item>
                  <el-dropdown-item @click="openGenDialog(activeGen)">编辑代际</el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" divided @click="deleteGeneration(activeGen.id)">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <div class="gen-detail-body">
          <div class="gen-detail-left">
            <p v-if="activeGen.description" class="gen-detail-desc">{{ activeGen.description }}</p>
            <p v-if="activeGen.keyImprovements" class="gen-detail-improve">关键提升：{{ activeGen.keyImprovements }}</p>
            <div class="gen-detail-dates" v-if="activeGen.startDate || activeGen.targetDate">
              <span v-if="activeGen.startDate">开始：{{ activeGen.startDate }}</span>
              <span v-if="activeGen.targetDate">目标：{{ activeGen.targetDate }}</span>
              <span v-if="activeGen.releaseDate">发布：{{ activeGen.releaseDate }}</span>
            </div>

            <!-- Generation Topics -->
            <div class="gen-detail-subsection">
              <div class="gen-subsection-header">
                <h4>关联课题 ({{ activeGen.relatedTopics?.length || 0 }})</h4>
                <el-button text size="small" type="primary" @click="openGenTopicDialog">编辑</el-button>
              </div>
              <div v-if="!activeGen.relatedTopics?.length" class="empty-block">暂无</div>
              <div v-else class="gen-topics-grid">
                <div v-for="t in activeGen.relatedTopics" :key="t.id" class="gen-topic-card" @click="goToTopic(t.id)">
                  <div class="gen-topic-title">{{ t.title }}</div>
                  <span v-if="t.urgency" class="tag tag--topic">{{ t.urgency }}</span>
                </div>
              </div>
            </div>

            <!-- Generation Issues -->
            <div class="gen-detail-subsection">
              <div class="gen-subsection-header">
                <h4>关联交付问题 ({{ activeGen.relatedIssues?.length || 0 }})</h4>
                <el-button text size="small" type="primary" @click="openGenIssueDialog">编辑</el-button>
              </div>
              <div v-if="!activeGen.relatedIssues?.length" class="empty-block">暂无</div>
              <div v-else>
                <div v-for="i in activeGen.relatedIssues" :key="i.id" class="gen-issue-row">
                  <span>{{ i.title }}</span>
                  <div class="gen-issue-tags">
                    <span class="tag tag--p0" v-if="i.priority==='P0'">P0</span>
                    <span class="tag tag--p1" v-else-if="i.priority==='P1'">P1</span>
                    <span class="tag">{{ i.status }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Gap Analysis -->
    <section class="detail-section tcgs-surface">
      <div class="section-header">
        <h2 class="section-title">能力缺口分析</h2>
        <el-button size="small" @click="editingGap = !editingGap">{{ editingGap ? '取消' : '编辑' }}</el-button>
      </div>
      <div v-if="!editingGap">
        <div v-if="!cap.capabilityGaps && !cap.gapActions" class="empty-block">暂无缺口分析</div>
        <div v-else>
          <div v-if="cap.capabilityGaps" class="gap-block">
            <h4>当前短板</h4>
            <pre>{{ cap.capabilityGaps }}</pre>
          </div>
          <div v-if="cap.gapActions" class="gap-block">
            <h4>改进行动</h4>
            <pre>{{ cap.gapActions }}</pre>
          </div>
        </div>
      </div>
      <div v-else>
        <el-input v-model="editForm.capabilityGaps" type="textarea" :rows="3" placeholder="当前能力短板..." style="margin-bottom:var(--space-3)" />
        <el-input v-model="editForm.gapActions" type="textarea" :rows="3" placeholder="改进行动建议..." />
        <el-button type="primary" :loading="saving" style="margin-top:var(--space-3)" @click="handleSaveGap">保存</el-button>
      </div>
    </section>

    <!-- Knowledge -->
    <section class="detail-section tcgs-surface">
      <div class="section-header">
        <h2 class="section-title">知识沉淀</h2>
        <el-button size="small" @click="editingKnowledge = !editingKnowledge">{{ editingKnowledge ? '取消' : '编辑' }}</el-button>
      </div>
      <div v-if="!editingKnowledge">
        <div v-if="!cap.knowledgeRecords && !linkedWikiPages.length" class="empty-block">暂无</div>
        <pre v-if="cap.knowledgeRecords" class="knowledge-text">{{ cap.knowledgeRecords }}</pre>
        <div v-if="linkedWikiPages.length" class="linked-wiki">
          <span class="linked-label">关联知识库：</span>
          <a v-for="wp in linkedWikiPages" :key="wp.id" :href="`/wiki/pages/${wp.id}`" target="_blank" class="wiki-link">{{ wp.title }}</a>
        </div>
      </div>
      <div v-else>
        <el-input v-model="editForm.knowledgeRecords" type="textarea" :rows="4" placeholder="技术文档、复盘、testcase、FAQ..." />
        <div style="margin-top:var(--space-3)">
          <span style="font-size:var(--text-sm);color:var(--color-text-secondary);margin-bottom:4px;display:block">关联知识库文章</span>
          <el-select v-model="selectedWikiIds" multiple filterable placeholder="选择文章..." style="width:100%">
            <el-option v-for="wp in allWikiPages" :key="wp.id" :label="wp.title" :value="wp.id" />
          </el-select>
        </div>
        <el-button type="primary" :loading="saving" style="margin-top:var(--space-3)" @click="handleSaveKnowledge">保存</el-button>
      </div>
    </section>

    <!-- Gen Topic Edit Dialog -->
    <el-dialog v-model="genTopicDialogVisible" title="编辑代际关联课题" width="500px">
      <el-select v-model="editGenTopicIds" multiple filterable placeholder="选择课题..." style="width:100%">
        <el-option v-for="t in allTopics" :key="t.id" :label="t.title" :value="t.id" />
      </el-select>
      <template #footer>
        <el-button @click="genTopicDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="genSaving" @click="saveGenTopics">保存</el-button>
      </template>
    </el-dialog>

    <!-- Gen Issue Edit Dialog -->
    <el-dialog v-model="genIssueDialogVisible" title="编辑代际关联交付问题" width="500px">
      <el-select v-model="editGenIssueIds" multiple filterable placeholder="选择问题..." style="width:100%">
        <el-option v-for="i in allIssues" :key="i.id" :label="i.title" :value="i.id" />
      </el-select>
      <template #footer>
        <el-button @click="genIssueDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="genSaving" @click="saveGenIssues">保存</el-button>
      </template>
    </el-dialog>

    <!-- Generation Dialog -->
    <el-dialog v-model="genDialogVisible" :title="editingGenId?'编辑代际':'新增代际'" width="560px" destroy-on-close @closed="resetGenForm">
      <el-form :model="genForm" label-position="top">
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="代号" required><el-input v-model="genForm.generationCode" placeholder="Gen1" maxlength="20"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="版本"><el-input v-model="genForm.version" placeholder="v1.0" maxlength="50"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="状态">
            <el-select v-model="genForm.status" style="width:100%">
              <el-option v-for="s in GEN_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value"/>
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-form-item label="名称" required><el-input v-model="genForm.name" placeholder="例：基础AR铆钉" maxlength="200"/></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="成熟度">
            <el-select v-model="genForm.maturityLevel" style="width:100%">
              <el-option v-for="ml in MATURITY_LEVELS" :key="ml.value" :label="ml.label" :value="ml.value"/>
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="Owner">
            <el-select v-model="genForm.ownerId" filterable clearable style="width:100%">
              <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id"/>
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="开始"><el-input v-model="genForm.startDate" type="date"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="目标"><el-input v-model="genForm.targetDate" type="date"/></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="发布"><el-input v-model="genForm.releaseDate" type="date"/></el-form-item></el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="genForm.description" type="textarea" :rows="2" placeholder="代际简介..."/></el-form-item>
        <el-form-item label="关键提升"><el-input v-model="genForm.keyImprovements" type="textarea" :rows="2" placeholder="相比上一代的关键提升..."/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="genSaving" @click="saveGeneration">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { ArrowLeft, Plus, Loading } from '@element-plus/icons-vue';
import { useCapabilitiesStore } from '@/stores/capabilities';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';
import { useTopicsStore } from '@/stores/topics';
import { capabilitiesApi } from '@/api/capabilities';
import { responsibilityApi, type ResponsibilityField } from '@/api/responsibility';
import { wikiApi } from '@/api/wiki';

const route = useRoute();
const router = useRouter();
const capabilitiesStore = useCapabilitiesStore();
const usersStore = useUsersStore();
const authStore = useAuthStore();
const topicsStore = useTopicsStore();

const PRODUCT_LINES = [
  { value: 'HUD', label: 'HUD' }, { value: 'LIGHT', label: '车灯' },
  { value: 'PROJECTION', label: '投影' }, { value: 'ALL', label: '全部' },
];
const PRODUCT_LINE_LABELS: Record<string,string> = { ALL:'全部', HUD:'HUD', LIGHT:'车灯', PROJECTION:'投影' };
const MATURITY_LEVELS = [
  { value:'L1',label:'L1 idea/prototype'},{value:'L2',label:'L2 testcase验证'},
  { value:'L3',label:'L3 cpp工程化'},{value:'L4',label:'L4 首车型陪跑'},{value:'L5',label:'L5 平台化复用'},
];
const MATURITY_LABELS: Record<string,string> = Object.fromEntries(MATURITY_LEVELS.map(m=>[m.value,m.label]));
const RISK_STATUSES = [
  { value:'NORMAL',label:'正常'},{value:'WATCH',label:'关注'},{value:'HIGH_RISK',label:'高风险'},
];
const RISK_LABELS: Record<string,string> = { NORMAL:'正常',WATCH:'关注',HIGH_RISK:'高风险' };
const GEN_STATUS_LABELS: Record<string,string> = {
  PLANNING:'规划中',RESEARCHING:'研究中',ENGINEERING:'工程化',PILOT:'试用',PRODUCTION:'量产',ARCHIVED:'已归档',
};
const GEN_STATUS_OPTIONS = [
  { value:'PLANNING',label:'规划中'},{value:'RESEARCHING',label:'研究中'},{value:'ENGINEERING',label:'工程化'},
  { value:'PILOT',label:'试用'},{value:'PRODUCTION',label:'量产'},{value:'ARCHIVED',label:'已归档'},
];

const cap = computed(() => capabilitiesStore.currentCapability);
const detailLoading = computed(() => capabilitiesStore.detailLoading);
const users = computed(() => usersStore.users);
const categoryTree = ref<any[]>([]);
const respFields = ref<ResponsibilityField[]>([]);
const editRespFieldId = ref<number|null>(null);

const editingBasic = ref(false);
const editingGap = ref(false);
const editingKnowledge = ref(false);
const saving = ref(false);

const editForm = reactive({
  name:'',description:'',categoryId:undefined as number|undefined,productLine:'',
  riskStatus:'',ownerId:undefined as number|undefined,backupOwnerId:undefined as number|undefined,
  responsibilityFieldName:'',capabilityGaps:'',gapActions:'',knowledgeRecords:'',
});

const selectedWikiIds = ref<number[]>([]);
const allWikiPages = ref<{id:number;title:string}[]>([]);
const linkedWikiPages = computed(()=>allWikiPages.value.filter(wp=>selectedWikiIds.value.includes(wp.id)));

function syncEditForm(){
  if(!cap.value)return;
  editForm.name=cap.value.name;editForm.description=cap.value.description||'';
  editForm.categoryId=cap.value.categoryId;editForm.productLine=cap.value.productLine;
  editForm.riskStatus=cap.value.riskStatus;editForm.ownerId=cap.value.ownerId;
  editForm.backupOwnerId=cap.value.backupOwnerId;
  editForm.responsibilityFieldName=cap.value.responsibilityFieldName||'';
  editRespFieldId.value=cap.value.responsibilityFieldId||null;
  editForm.capabilityGaps=cap.value.capabilityGaps||'';
  editForm.gapActions=cap.value.gapActions||'';
  editForm.knowledgeRecords=cap.value.knowledgeRecords||'';
  selectedWikiIds.value=cap.value.knowledgeWikiPageIds?cap.value.knowledgeWikiPageIds.split(',').map(Number).filter(Boolean):[];
}
watch(cap,()=>{syncEditForm()});

async function handleSaveBasic(){
  if(!cap.value)return;
  saving.value=true;
  try{
    await capabilitiesStore.updateCapability(cap.value.id,{
      name:editForm.name,description:editForm.description||undefined,
      categoryId:editForm.categoryId,productLine:editForm.productLine,
      riskStatus:editForm.riskStatus,ownerId:editForm.ownerId,
      backupOwnerId:editForm.backupOwnerId||undefined,
      responsibilityFieldId:editRespFieldId.value??undefined,
      responsibilityFieldName:editForm.responsibilityFieldName||undefined,
    });
    ElMessage.success('已更新');editingBasic.value=false;
  }catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
  finally{saving.value=false}
}

async function handleSaveGap(){
  if(!cap.value)return;
  saving.value=true;
  try{
    await capabilitiesStore.updateCapability(cap.value.id,{
      capabilityGaps:editForm.capabilityGaps||undefined,gapActions:editForm.gapActions||undefined,
    });
    ElMessage.success('缺口已更新');editingGap.value=false;
  }catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
  finally{saving.value=false}
}

async function handleSaveKnowledge(){
  if(!cap.value)return;
  saving.value=true;
  try{
    await capabilitiesStore.updateCapability(cap.value.id,{
      knowledgeRecords:editForm.knowledgeRecords||undefined,
      knowledgeWikiPageIds:selectedWikiIds.value.length?selectedWikiIds.value.join(','):undefined,
    });
    ElMessage.success('已更新');editingKnowledge.value=false;
  }catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
  finally{saving.value=false}
}

function onDetailRespChange(fieldId:number|null){
  if(!fieldId){editForm.responsibilityFieldName='';return}
  const rf=respFields.value.find(f=>f.id===fieldId);
  if(rf){editForm.responsibilityFieldName=rf.name;
    if(rf.ownerName&&users.value.length){
      const m=users.value.find(u=>u.name===rf.ownerName||u.name.includes(rf.ownerName)||rf.ownerName.includes(u.name));
      if(m)editForm.ownerId=m.id;
    }
  }
}

// ============ Generations ============
const activeGenId = ref<number|null>(null);
const genDialogVisible = ref(false);
const editingGenId = ref<number|null>(null);
const genSaving = ref(false);
const genForm = reactive({
  name:'',generationCode:'',version:'',status:'PLANNING',maturityLevel:'L1',
  ownerId:undefined as number|undefined,description:'',keyImprovements:'',
  startDate:'',targetDate:'',releaseDate:'',
});

const genTopicDialogVisible = ref(false);
const genIssueDialogVisible = ref(false);
const editGenTopicIds = ref<number[]>([]);
const editGenIssueIds = ref<number[]>([]);

const allTopics = ref<any[]>([]);
const allIssues = ref<any[]>([]);

const sortedGenerations = computed(()=>{
  if(!cap.value?.generations)return[];
  return [...cap.value.generations].sort((a,b)=>{
    const o:Record<string,number>={PRODUCTION:0,PILOT:1,ENGINEERING:2,RESEARCHING:3,PLANNING:4,ARCHIVED:5};
    return (o[a.status]??9)-(o[b.status]??9);
  });
});

const activeGen = computed(()=>{
  if(!activeGenId.value||!cap.value?.generations)return null;
  return cap.value.generations.find(g=>g.id===activeGenId.value)||null;
});

function selectGen(id:number){activeGenId.value=id}

function openGenDialog(gen?:any){
  if(gen){
    editingGenId.value=gen.id;
    genForm.name=gen.name;genForm.generationCode=gen.generationCode;genForm.version=gen.version||'';
    genForm.status=gen.status;genForm.maturityLevel=gen.maturityLevel;genForm.ownerId=gen.ownerId;
    genForm.description=gen.description||'';genForm.keyImprovements=gen.keyImprovements||'';
    genForm.startDate=gen.startDate||'';genForm.targetDate=gen.targetDate||'';genForm.releaseDate=gen.releaseDate||'';
  }else{editingGenId.value=null;resetGenForm()}
  genDialogVisible.value=true;
}

function resetGenForm(){
  genForm.name='';genForm.generationCode='';genForm.version='';genForm.status='PLANNING';
  genForm.maturityLevel='L1';genForm.ownerId=undefined;genForm.description='';genForm.keyImprovements='';
  genForm.startDate='';genForm.targetDate='';genForm.releaseDate='';
}

async function saveGeneration(){
  if(!cap.value||!genForm.name||!genForm.generationCode){ElMessage.warning('请填代号和名称');return}
  genSaving.value=true;
  try{
    if(editingGenId.value){
      await capabilitiesApi.updateGeneration(editingGenId.value,{
        name:genForm.name,generationCode:genForm.generationCode,version:genForm.version||undefined,
        status:genForm.status,maturityLevel:genForm.maturityLevel,ownerId:genForm.ownerId,
        description:genForm.description||undefined,keyImprovements:genForm.keyImprovements||undefined,
        startDate:genForm.startDate||undefined,targetDate:genForm.targetDate||undefined,
        releaseDate:genForm.releaseDate||undefined,
      });
    }else{
      await capabilitiesApi.createGeneration(cap.value.id,{
        name:genForm.name,generationCode:genForm.generationCode,version:genForm.version||undefined,
        status:genForm.status,maturityLevel:genForm.maturityLevel,ownerId:genForm.ownerId,
        description:genForm.description||undefined,keyImprovements:genForm.keyImprovements||undefined,
        startDate:genForm.startDate||undefined,targetDate:genForm.targetDate||undefined,
        releaseDate:genForm.releaseDate||undefined,
      });
    }
    genDialogVisible.value=false;
    await capabilitiesStore.fetchCapability(cap.value.id);
    if(!activeGenId.value&&cap.value.generations?.length)activeGenId.value=cap.value.generations[0].id;
  }catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
  finally{genSaving.value=false}
}

async function setProductionGen(genId:number){
  if(!cap.value)return;
  try{await capabilitiesStore.updateCapability(cap.value.id,{currentProductionGenerationId:genId});await capabilitiesStore.fetchCapability(cap.value.id)}
  catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
}

async function setResearchGen(genId:number){
  if(!cap.value)return;
  try{await capabilitiesStore.updateCapability(cap.value.id,{currentResearchGenerationId:genId});await capabilitiesStore.fetchCapability(cap.value.id)}
  catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
}

async function deleteGeneration(genId:number){
  try{await capabilitiesApi.deleteGeneration(genId);if(cap.value){await capabilitiesStore.fetchCapability(cap.value.id);if(activeGenId.value===genId)activeGenId.value=cap.value.generations?.[0]?.id||null}}
  catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
}

function goToTopic(id:number){router.push(`/topics/${id}`)}

function openGenTopicDialog(){
  if(!activeGen.value)return;
  editGenTopicIds.value = activeGen.value.relatedTopics?.map((t:any)=>t.id) || [];
  genTopicDialogVisible.value = true;
}

function openGenIssueDialog(){
  if(!activeGen.value)return;
  editGenIssueIds.value = activeGen.value.relatedIssues?.map((i:any)=>i.id) || [];
  genIssueDialogVisible.value = true;
}

async function saveGenTopics(){
  if(!activeGen.value)return;
  genSaving.value = true;
  try{
    await capabilitiesApi.updateGeneration(activeGen.value.id, { relatedTopicIds: editGenTopicIds.value });
    genTopicDialogVisible.value = false;
    if(cap.value) await capabilitiesStore.fetchCapability(cap.value.id);
  }catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
  finally{genSaving.value=false}
}

async function saveGenIssues(){
  if(!activeGen.value)return;
  genSaving.value = true;
  try{
    await capabilitiesApi.updateGeneration(activeGen.value.id, { relatedIssueIds: editGenIssueIds.value });
    genIssueDialogVisible.value = false;
    if(cap.value) await capabilitiesStore.fetchCapability(cap.value.id);
  }catch(e:any){ElMessage.error(e.response?.data?.detail||'操作失败')}
  finally{genSaving.value=false}
}

onMounted(async()=>{
  const id=Number(route.params.id);
  await capabilitiesStore.fetchCapability(id);
  syncEditForm();
  usersStore.fetchUsers(1,200);
  try{categoryTree.value=await capabilitiesApi.getCategoryTree()}catch{}
  try{const r=await responsibilityApi.getFields();respFields.value=r.fields||[]}catch{}
  try{const dirs=await wikiApi.listDirections();const ps:{id:number;title:string}[]=[];for(const d of dirs){if(d.pages)for(const p of d.pages)ps.push({id:p.id,title:p.title})};allWikiPages.value=ps}catch{}
  try{topicsStore.fetchTopics();allTopics.value=topicsStore.topics||[]}catch{}
  try{allIssues.value=await capabilitiesApi.listIssues()}catch{}
  if(cap.value?.generations?.length)activeGenId.value=cap.value.generations[0].id;
});
</script>

<style scoped>
.capability-detail-page{padding:var(--space-6);max-width:1200px;margin:0 auto;display:flex;flex-direction:column;gap:var(--space-4)}
.loading-state,.empty-state{display:flex;align-items:center;justify-content:center;padding:var(--space-16);gap:var(--space-2);color:var(--color-text-tertiary);flex-direction:column}
.detail-header{display:flex;align-items:center;gap:var(--space-3)}
.detail-title{font-size:var(--text-2xl);font-weight:var(--font-bold);margin:0;flex:1}
.detail-section.tcgs-surface{padding:var(--space-4);border:1px solid var(--color-border-subtle);border-radius:var(--radius-lg)}
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-3)}
.section-title{font-size:var(--text-lg);font-weight:var(--font-semibold);margin:0}
.gen-count-badge{font-size:var(--text-xs);color:var(--color-text-muted);margin-left:var(--space-1)}
.info-bar{padding:var(--space-3) var(--space-4)}
.info-bar-row{display:flex;gap:var(--space-2);flex-wrap:wrap;align-items:center}
.info-badge{font-size:var(--text-xs);padding:2px var(--space-2);border-radius:var(--radius-md);font-weight:var(--font-medium)}
.info-badge--cat{background:var(--color-bg-subtle);color:var(--color-text-secondary)}
.info-badge--owner{background:var(--color-primary-light);color:var(--color-primary)}
.info-badge--resp{background:#fef3c7;color:#92400e}
.info-badge--normal{background:var(--color-success-bg);color:var(--color-success-600)}
.info-badge--watch{background:var(--color-warning-bg);color:var(--color-warning-600)}
.info-badge--high_risk{background:var(--color-danger-bg);color:var(--color-danger-600)}
.info-desc{font-size:var(--text-sm);color:var(--color-text-secondary);margin:var(--space-2) 0 0 0}

/* Swiper */
.gen-swiper-wrapper{margin-bottom:var(--space-4)}
.gen-swiper{display:flex;gap:var(--space-3);overflow-x:auto;padding-bottom:var(--space-2);scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch}
.gen-swiper::-webkit-scrollbar{height:4px}
.gen-swiper::-webkit-scrollbar-thumb{background:var(--color-border);border-radius:4px}
.gen-swiper-card{flex:0 0 200px;padding:var(--space-3);border:1px solid var(--color-border-subtle);border-radius:var(--radius-lg);cursor:pointer;transition:all .2s;scroll-snap-align:start;background:var(--color-surface-primary)}
.gen-swiper-card:hover{border-color:var(--color-primary);transform:translateY(-2px);box-shadow:0 2px 8px rgba(0,0,0,.08)}
.gen-swiper-card--active{border-color:var(--color-primary);border-width:2px;background:var(--color-primary-light)}
.gen-swiper-code{font-size:var(--text-sm);font-weight:var(--font-bold);color:var(--color-primary)}
.gen-swiper-name{font-size:var(--text-base);font-weight:var(--font-semibold);margin:var(--space-1) 0}
.gen-swiper-tags{display:flex;gap:var(--space-1);margin:var(--space-2) 0;flex-wrap:wrap}
.gen-swiper-stats{display:flex;gap:var(--space-3);font-size:var(--text-xs);color:var(--color-text-muted)}

/* Tag utility */
.tag{font-size:var(--text-xs);padding:1px var(--space-2);border-radius:var(--radius-md);font-weight:var(--font-medium)}
.tag--planning{background:#f3f4f6;color:#6b7280}
.tag--researching{background:#ede9fe;color:#7c3aed}
.tag--engineering{background:#dbeafe;color:#2563eb}
.tag--pilot{background:#fefce8;color:#ca8a04}
.tag--production{background:#dcfce7;color:#16a34a}
.tag--archived{background:#f3f4f6;color:#9ca3af}
.tag--maturity{background:var(--color-primary-light);color:var(--color-primary)}
.tag--p0{background:#fee2e2;color:#dc2626}
.tag--p1{background:#fed7aa;color:#ea580c}
.tag--topic{background:var(--color-bg-subtle);color:var(--color-text-muted)}

/* Gen Detail */
.gen-detail{border:1px solid var(--color-border-subtle);border-radius:var(--radius-lg);overflow:hidden}
.gen-detail-header{display:flex;justify-content:space-between;align-items:center;padding:var(--space-3) var(--space-4);background:var(--color-bg-subtle);flex-wrap:wrap;gap:var(--space-2)}
.gen-detail-code{font-size:var(--text-sm);font-weight:var(--font-bold);color:var(--color-primary);margin-right:var(--space-2)}
.gen-detail-name{font-size:var(--text-base);font-weight:var(--font-semibold)}
.gen-detail-version{font-size:var(--text-xs);color:var(--color-text-muted);margin-left:var(--space-2)}
.gen-detail-badges{display:flex;gap:var(--space-2);align-items:center}
.gen-detail-badge{font-size:var(--text-xs);padding:2px var(--space-2);border-radius:var(--radius-md);font-weight:var(--font-medium)}
.gen-detail-badge--planning{background:#f3f4f6;color:#6b7280}
.gen-detail-badge--researching{background:#ede9fe;color:#7c3aed}
.gen-detail-badge--engineering{background:#dbeafe;color:#2563eb}
.gen-detail-badge--pilot{background:#fefce8;color:#ca8a04}
.gen-detail-badge--production{background:#dcfce7;color:#16a34a}
.gen-detail-badge--maturity{background:var(--color-primary-light);color:var(--color-primary)}
.gen-detail-badge--owner{background:var(--color-bg-subtle);color:var(--color-text-secondary)}
.gen-detail-body{padding:var(--space-4);display:flex;flex-direction:column;gap:var(--space-3)}
.gen-detail-desc{font-size:var(--text-sm);color:var(--color-text-secondary);margin:0}
.gen-detail-improve{font-size:var(--text-sm);color:var(--color-primary);margin:0}
.gen-detail-dates{display:flex;gap:var(--space-4);font-size:var(--text-xs);color:var(--color-text-muted)}
.gen-detail-subsection{margin-top:var(--space-3)}
.gen-subsection-header{display:flex;align-items:center;gap:var(--space-2)}
.gen-subsection-header h4{font-size:var(--text-sm);font-weight:var(--font-semibold);margin:0}
.gen-topics-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:var(--space-2);margin-top:var(--space-2)}
.gen-topic-card{padding:var(--space-2) var(--space-3);border:1px solid var(--color-border-subtle);border-radius:var(--radius-md);cursor:pointer;display:flex;justify-content:space-between;align-items:center}
.gen-topic-card:hover{border-color:var(--color-primary)}
.gen-topic-title{font-size:var(--text-sm);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gen-issue-row{display:flex;justify-content:space-between;align-items:center;padding:var(--space-2) 0;border-bottom:1px solid var(--color-border-subtle);font-size:var(--text-sm)}
.gen-issue-tags{display:flex;gap:var(--space-1)}

.empty-block{font-size:var(--text-sm);color:var(--color-text-muted);padding:var(--space-4) 0;text-align:center}
.gap-block{margin-bottom:var(--space-3)}
.gap-block h4{font-size:var(--text-sm);font-weight:var(--font-semibold);margin:0 0 var(--space-1) 0}
.gap-block pre{font-size:var(--text-sm);color:var(--color-text-secondary);white-space:pre-wrap;margin:0}
.knowledge-text{font-size:var(--text-sm);color:var(--color-text-secondary);white-space:pre-wrap;margin:0}
.linked-wiki{margin-top:var(--space-2)}
.linked-label{font-size:var(--text-sm);color:var(--color-text-secondary)}
.wiki-link{display:inline-block;font-size:var(--text-sm);color:var(--color-primary);padding:2px var(--space-2);margin:0 var(--space-2) var(--space-1) 0;background:var(--color-primary-light);border-radius:var(--radius-md);text-decoration:none}
.edit-form{display:flex;flex-direction:column;gap:var(--space-3)}
</style>
