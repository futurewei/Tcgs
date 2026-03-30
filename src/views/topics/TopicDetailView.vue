<template>
  <div v-loading="loading" class="topic-detail-page">
    <!-- Back Navigation -->
    <div class="flex items-center gap-3 mb-5">
      <el-button text class="back-btn" @click="router.back()">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>返回
      </el-button>
    </div>

    <div v-if="topic" class="space-y-5">
      <!-- ============ 顶部：课题基本信息 ============ -->
      <section class="tcgs-surface topic-header">
        <div class="header-main">
          <div class="header-info">
            <div class="title-row">
              <h1 class="topic-title">{{ topic.title }}</h1>
              <span :class="['priority-tag', `priority-${topic.urgency?.toLowerCase()}`]">{{ topic.urgency }}</span>
              <span class="type-badge">{{ typeLabel }}</span>
            </div>
            <p class="topic-id">编号: {{ topic.id }}</p>
          </div>
        <div class="header-result">
    <!-- 只有 ADMIN 可以变更课题状态 -->
    <el-dropdown v-if="canChangeResult" trigger="click" @command="onHeaderResultChange">
      <div class="header-result-clickable">
        <span :class="['result-badge', `result-${topic.result?.toLowerCase()}`]">
        {{ resultLabel }}
      </span>
      <el-icon class="ml-1"><ArrowDown /></el-icon>
    </div>

    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="OPEN">标记为进行中</el-dropdown-item>
        <el-dropdown-item command="SUCCESS">标记为已完成</el-dropdown-item>
        <el-dropdown-item command="UNSOLVABLE">标记为无法解决</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
  <!-- 非 ADMIN 用户只能查看状态 -->
  <span v-else :class="['result-badge', `result-${topic.result?.toLowerCase()}`]">
    {{ resultLabel }}
  </span>
</div>
	</div>
        
        <!-- DRI + 需求方 + 团队 信息 -->
        <div class="meta-row">
          <div class="meta-item">
            <span class="meta-label">DRI</span>
            <div class="dri-chip" v-if="driBinding?.slot">
              <span class="dri-dot"></span>
              <router-link :to="getDriProfileLink()" class="dri-name">{{ driSlotName }}</router-link>
              <span class="dri-badge">DRI</span>
            </div>
            <span v-else class="meta-empty">未分配</span>
            <el-button v-if="canChangeDri" size="small" text class="meta-action" @click="showChangeDRI = true">更换</el-button>
          </div>
          
          <div class="meta-divider"></div>
          
          <div class="meta-item">
            <span class="meta-label">需求方</span>
            <span class="meta-value">{{ requesterName }}</span>
          </div>
          
          <div class="meta-divider"></div>
          
          <div class="meta-item">
            <span class="meta-label">团队</span>
            <div class="team-avatars">
              <router-link
                v-for="b in teamBindings.slice(0, 5)"
                :key="b.id"
                :to="getBindingProfileLink(b)"
                class="team-avatar"
                :title="b.slot?.name + ' - 点击查看档案'"
              >{{ getInitials(b.slot?.name) }}</router-link>
              <div v-if="teamBindings.length > 5" class="team-avatar more">+{{ teamBindings.length - 5 }}</div>
            </div>
            <el-button v-if="authStore.isAdmin" size="small" text class="meta-action" @click="showAddBinding = true">添加</el-button>
          </div>

          <div class="meta-divider"></div>

          <div class="meta-item">
            <span class="meta-label">创建时间</span>
            <span class="meta-value">{{ formatDateTime(topic.created_at || topic.createdAt) }}</span>
          </div>

          <template v-if="topic.closed_at || topic.closedAt">
            <div class="meta-divider"></div>
            <div class="meta-item">
              <span class="meta-label">关闭时间</span>
              <span class="meta-value closed-time">{{ formatDateTime(topic.closed_at || topic.closedAt) }}</span>
            </div>
          </template>
        </div>
      </section>

      <!-- ============ 风险/阻塞区 ============ -->
      <section v-if="activeRisks.length > 0 || canEdit" class="tcgs-surface risks-section">
        <div class="section-header">
          <div class="section-title-group">
            <h2 class="section-title">风险/阻塞</h2>
            <span v-if="redRisks.length" class="risk-count risk-red">{{ redRisks.length }} 个阻塞</span>
            <span v-if="yellowRisks.length" class="risk-count risk-yellow">{{ yellowRisks.length }} 个风险</span>
          </div>
          <el-button v-if="canEdit" size="small" @click="showAddRisk = true">
            <el-icon class="mr-1"><Plus /></el-icon>添加风险
          </el-button>
        </div>
        
        <div v-if="activeRisks.length" class="risks-list">
          <div v-for="risk in activeRisks" :key="risk.id" class="risk-item">
            <div :class="['risk-indicator', `risk-${risk.level}`]"></div>
            <div class="risk-content">
              <div class="risk-meta">
                <span class="risk-type">{{ risk.blockerType }}</span>
                <span v-if="risk.blockerName" class="risk-blocker">{{ risk.blockerName }}</span>
              </div>
              <p class="risk-desc">{{ risk.description }}</p>
              <div class="risk-footer">
                <span v-if="risk.expectedResolveDate">预计解除: {{ formatDate(risk.expectedResolveDate) }}</span>
                <span v-if="risk.owner">Owner: {{ risk.owner.name }}</span>
              </div>
            </div>
            <div class="risk-actions">
              <el-button size="small" type="success" text @click="resolveRisk(risk)">标记解决</el-button>
              <el-button size="small" type="danger" text @click="deleteRisk(risk.id)">删除</el-button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">暂无风险/阻塞</div>
      </section>

      <!-- ============ 课题背景 & 用户视角目标 ============ -->
      <div class="context-grid">
        <section class="tcgs-surface context-card">
          <div class="context-header">
            <h3 class="context-title"><span class="context-tag why">WHY</span>课题背景</h3>
            <el-button v-if="canEdit" size="small" text @click="editField('background')">编辑</el-button>
          </div>
          <div v-if="topic.background" class="context-content rich-content" v-html="topic.background"></div>
          <p v-else class="context-placeholder">为什么要做？不做会怎样？</p>
        </section>
        
        <section class="tcgs-surface context-card">
          <div class="context-header">
            <h3 class="context-title"><span class="context-tag what">WHAT</span>用户视角目标</h3>
            <el-button v-if="canEdit" size="small" text @click="editField('userGoal')">编辑</el-button>
          </div>
          <div v-if="topic.userGoal || topic.user_goal" class="context-content rich-content" v-html="topic.userGoal || topic.user_goal"></div>
          <p v-else class="context-placeholder">用用户/业务语言描述目标</p>
        </section>
      </div>

      <!-- ============ Core Ideas 算法思想演进 ============ -->
      <CoreIdeasPanel 
        :topic-id="topicId"
        :stage-instances="stageInstances"
        :can-edit="canEdit"
        @refresh="refreshTopic"
      />

      <!-- ============ 主时间轴：Stage Instances ============ -->
      <section class="tcgs-surface timeline-section">
        <div class="section-header">
          <h2 class="section-title">算法演进时间轴</h2>
          <el-button v-if="canEdit" size="small" @click="showAddStage = true">
            <el-icon class="mr-1"><Plus /></el-icon>插入阶段
          </el-button>
        </div>
        
        <div class="timeline-container">
          <div class="timeline-track">
            <div v-for="(stage, idx) in stageInstances" :key="stage.id" class="timeline-item">
              <div
                :class="[
                  'stage-card',
                  stage.id === selectedStageId ? 'selected' : '',
                  `status-${stage.status}`
                ]"
                @click="selectStage(stage)"
              >
                <div :class="['stage-status-dot', `status-${stage.status}`]"></div>
                <p class="stage-name">{{ stage.name }}</p>
                <p class="stage-status-text">
                  {{ stage.status === 'done' ? '已完成' : stage.status === 'active' ? '进行中' : '待开始' }}
                </p>
                <div class="stage-counts">
                  <span v-if="getStageDeliverables(stage.id).length">📎 {{ getStageDeliverables(stage.id).length }}</span>
                  <span v-if="stage.techPoints?.length">🔧 {{ stage.techPoints.length }}</span>
                </div>
                <!-- 完成者信息 -->
                <div v-if="stage.status === 'done' && (stage.completedBy || stage.completed_by)" class="stage-completed-info">
                  <span class="completed-by-name">{{ stage.completedBy?.name || stage.completed_by?.name }}</span>
                  <span class="completed-at-time">{{ formatDate(stage.completedAt || stage.completed_at) }}</span>
                </div>
              </div>
              <div v-if="idx < stageInstances.length - 1" class="timeline-connector">
                <el-icon><Right /></el-icon>
              </div>
            </div>
          </div>
          
          <div v-if="stageInstances.length === 0" class="empty-state">
            暂无阶段，点击"插入阶段"开始
          </div>
        </div>
      </section>

      <!-- ============ 选中阶段的详情 ============ -->
      <section v-if="selectedStage" class="tcgs-surface stage-detail">
        <div class="section-header stage-detail-header">
          <div class="stage-info">
            <div class="stage-title-row">
              <h2 class="section-title">{{ selectedStage.name }}</h2>
              <span :class="['stage-badge', `status-${selectedStage.status}`]">
                {{ selectedStage.status === 'done' ? '已完成' : selectedStage.status === 'active' ? '进行中' : '待开始' }}
              </span>
            </div>
            <p v-if="selectedStage.description" class="stage-desc">{{ selectedStage.description }}</p>
          </div>
          <div class="stage-actions">
            <el-button v-if="canEdit && canMoveBack" size="small" @click="handleMoveBack">
              <el-icon class="mr-1"><ArrowLeft /></el-icon>上一阶段
            </el-button>
            <el-button v-if="canEdit && selectedStage.status === 'active'" type="primary" size="small" @click="handleMoveForward">
              完成并进入下一阶段<el-icon class="ml-1"><ArrowRight /></el-icon>
            </el-button>
            <el-button v-if="canEdit && selectedStage.status === 'done'" size="small" @click="handleReopenStage">重新打开</el-button>
            <el-button v-if="canEdit" size="small" @click="showEditStage = true">编辑阶段</el-button>
            <el-dropdown v-if="canEdit" trigger="click">
              <el-button size="small"><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="copyStage">复制阶段</el-dropdown-item>
                  <el-dropdown-item v-if="selectedStage.status === 'pending'" @click="activateStage">激活阶段</el-dropdown-item>
                  <el-dropdown-item divided type="danger" @click="deleteStage">删除阶段</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <div class="stage-content">
          <!-- 已完成阶段的完成信息 -->
          <div v-if="selectedStage.status === 'done' && selectedStage.completedBy" class="completion-info">
            <div class="completion-header">
              <el-icon class="completion-icon"><CircleCheck /></el-icon>
              <span class="completion-title">阶段已完成</span>
            </div>
            <div class="completion-meta">
              <div class="completion-item">
                <span class="completion-label">完成人:</span>
                <span class="completion-value">{{ selectedStage.completedBy?.name }}</span>
              </div>
              <div class="completion-item">
                <span class="completion-label">完成时间:</span>
                <span class="completion-value">{{ formatDate(selectedStage.completedAt) }}</span>
              </div>
            </div>
            <div v-if="selectedStage.completionNote" class="completion-note">
              <span class="note-label">完成说明:</span>
              <p class="note-text">{{ selectedStage.completionNote }}</p>
            </div>
            <div v-if="selectedStage.remainingIssues" class="remaining-issues">
              <span class="issues-label">遗留问题:</span>
              <p class="issues-text">{{ selectedStage.remainingIssues }}</p>
            </div>
          </div>

          <!-- 验收标准 -->
          <div class="criteria-grid">
            <!-- 阶段目标 -->
            <div class="objective-card">
              <div class="objective-header">
                <p class="objective-title">阶段目标（一句话）</p>
                <el-button v-if="canEdit" size="small" text @click="editStageField('objective')">编辑</el-button>
              </div>
              <p class="objective-text">{{ selectedStage.objective || '—' }}</p>
            </div>

            <!-- 成功判据 -->
            <div class="criteria-card success">
              <div class="criteria-header">
                <p class="criteria-title">✓ 成功判据</p>
                <el-button v-if="canEdit" size="small" text @click="editCriteria('success')">
                  <el-icon class="mr-1"><Plus /></el-icon>添加
                </el-button>
              </div>
              <div class="criteria-list">
                <div v-for="item in successCriteria" :key="item.id" class="criteria-item">
                  <el-checkbox v-model="item.checked" :disabled="!canEdit" @change="updateCriteriaItem('success', item)" />
                  <span :class="['criteria-text', item.checked ? 'checked' : '']">
                    {{ item.text }}
                    <span v-if="item.required" class="required-badge">必须</span>
                  </span>
                  <el-button v-if="canEdit" size="small" type="danger" text @click="removeCriteriaItem('success', item.id)">×</el-button>
                </div>
                <p v-if="!successCriteria.length" class="criteria-empty">点击添加可量化的成功判据</p>
              </div>
            </div>

            <!-- 失败判据 -->
            <div class="criteria-card failure">
              <div class="criteria-header">
                <p class="criteria-title">✗ 失败判据</p>
                <el-button v-if="canEdit" size="small" text @click="editCriteria('failure')">
                  <el-icon class="mr-1"><Plus /></el-icon>添加
                </el-button>
              </div>
              <div class="criteria-list">
                <div v-for="item in failureCriteria" :key="item.id" class="criteria-item">
                  <el-checkbox v-model="item.checked" :disabled="!canEdit" @change="updateCriteriaItem('failure', item)" />
                  <span :class="['criteria-text', item.checked ? 'checked' : '']">{{ item.text }}</span>
                  <el-button v-if="canEdit" size="small" type="danger" text @click="removeCriteriaItem('failure', item.id)">×</el-button>
                </div>
                <p v-if="!failureCriteria.length" class="criteria-empty">什么情况下判定为失败/无法解决？</p>
              </div>
            </div>
          </div>

          <!-- 交付物 -->
          <div class="deliverables-section">
            <div class="deliverables-header">
              <h3 class="deliverables-title">📎 交付物</h3>
              <el-button v-if="canEdit" size="small" @click="showAddDeliverable = true">
                <el-icon class="mr-1"><Plus /></el-icon>添加交付物
              </el-button>
            </div>
            
            <div v-if="requiredOutputs.length" class="outputs-checklist">
              <p class="outputs-title">📋 本阶段输出物清单</p>
              <div class="outputs-list">
                <div v-for="out in requiredOutputs" :key="out.id" class="output-item">
                  <el-checkbox v-model="out.delivered" :disabled="!canEdit" @change="updateOutputDelivered(out)" />
                  <span :class="['output-name', out.delivered ? 'delivered' : '']">{{ out.name }}</span>
                  <span :class="['output-badge', out.required ? 'required' : 'optional']">{{ out.required ? '必交' : '选交' }}</span>
                </div>
              </div>
            </div>
            
            <div class="deliverables-grid">
              <div v-for="d in stageDeliverables" :key="d.id" class="deliverable-card">
                <div :class="['deliverable-icon', `category-${d.category || 'link'}`]">
                  <el-icon :size="18"><component :is="getCategoryIcon(d.category)" /></el-icon>
                </div>
                <div class="deliverable-info">
                  <a :href="d.url" target="_blank" class="deliverable-name">{{ d.name }}</a>
                  <p class="deliverable-meta">{{ d.createdBy?.name }} • {{ formatDate(d.createdAt || d.created_at) }}</p>
                </div>
                <el-button v-if="canEdit" class="deliverable-delete" size="small" type="danger" text @click="deleteDeliverable(d.id)">删除</el-button>
              </div>
            </div>
            
            <div v-if="!stageDeliverables.length" class="deliverables-empty">
              <p class="empty-text">暂无交付物</p>
              <p class="empty-hint">完成阶段前需要上传对应交付物</p>
            </div>
          </div>

          <!-- 评审意见 -->
          <div v-if="selectedStage?.requireReview" class="reviews-section">
            <div class="reviews-header">
              <h3 class="reviews-title">📝 评审意见</h3>
            </div>

            <div class="reviews-list">
              <div v-for="review in stageReviews" :key="review.id" class="review-item">
                <div class="review-content">
                  <div class="review-meta">
                    <span class="review-author">{{ review.createdBy?.name || '未知用户' }}</span>
                    <span class="review-dot">·</span>
                    <span class="review-time">{{ formatDateTime(review.createdAt) }}</span>
                  </div>
                  <p class="review-text">{{ review.content }}</p>
                </div>
                <el-button
                  v-if="canDeleteReview(review)"
                  size="small"
                  type="danger"
                  text
                  @click="deleteReview(review.id)"
                >删除</el-button>
              </div>
              <div v-if="!stageReviews.length" class="reviews-empty">
                <p class="empty-text">暂无评审意见</p>
              </div>
            </div>

            <div class="review-input">
              <el-input
                v-model="newReviewContent"
                type="textarea"
                :rows="2"
                placeholder="写下你的评审意见..."
              />
              <el-button
                type="primary"
                :disabled="!newReviewContent.trim()"
                @click="submitReview"
              >提交评审</el-button>
            </div>
          </div>

          <!-- 技术点拆解 -->
          <div class="techpoints-section">
            <div class="techpoints-header">
              <h3 class="techpoints-title">🔧 技术点拆解</h3>
              <el-button v-if="canEdit" size="small" type="primary" plain @click="showAddTechPoint = true">
                <el-icon class="mr-1"><Plus /></el-icon>添加技术点
              </el-button>
            </div>
            
            <div class="techpoints-list">
              <div v-for="tp in stageTechPoints" :key="tp.id" class="techpoint-card">
                <div class="techpoint-main">
                  <div class="techpoint-header">
                    <h4 class="techpoint-name">{{ tp.name }}</h4>
                    <span :class="['techpoint-status', `status-${tp.status}`]">
                      {{ tp.status === 'completed' ? '已完成' : tp.status === 'in_progress' ? '进行中' : '草稿' }}
                    </span>
                  </div>
                  <p v-if="tp.description" class="techpoint-desc">{{ tp.description }}</p>
                  
                  <div class="techpoint-authors">
                    <div class="author-item">
                      <span class="author-label">第一作者:</span>
                      <span class="author-name primary">{{ tp.firstAuthor?.name || '未指定' }}</span>
                    </div>
                    <div v-if="tp.contributors?.length" class="author-item">
                      <span class="author-label">贡献者:</span>
                      <span class="author-name">{{ tp.contributors.map(c => c.userName || c.user_name).join(', ') }}</span>
                    </div>
                  </div>
                  
                  <div v-if="tp.hypothesis" class="techpoint-hypothesis">
                    <span class="hypothesis-label">假设:</span>{{ tp.hypothesis }}
                  </div>
                </div>
                <el-button v-if="canEdit" size="small" text @click="editTechPoint(tp)">编辑</el-button>
              </div>
              
              <div v-if="!stageTechPoints.length" class="techpoints-empty">
                <p class="empty-text">暂无技术点</p>
                <p class="empty-hint">技术点是可追溯成果的最小单元</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Dialogs -->
    <ChangeDRIDialog v-model="showChangeDRI" :topic="topic" :bindings="normalizedBindings" @changed="refreshTopic" />
    <AddBindingDialog v-model="showAddBinding" :topic-id="topicId" @created="afterBindingChanged" />
    <AddDeliverableDialog v-model="showAddDeliverable" :topic-id="topicId" :stage-id="selectedStageId" @created="refreshTopic" />
    
    <!-- Edit Field Dialog -->
    <el-dialog v-model="showFieldEdit" :title="fieldEditTitle" width="800px" top="5vh">
      <RichEditor v-model="fieldEditValue" :placeholder="fieldEditPlaceholder" folder="topic-content" />
      <template #footer>
        <el-button @click="showFieldEdit = false">取消</el-button>
        <el-button type="primary" @click="saveFieldEdit">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- Add Stage Dialog -->
    <el-dialog v-model="showAddStage" title="添加阶段" width="500px">
      <el-form :model="newStageForm" label-position="top">
        <el-form-item label="阶段名称" required>
          <el-input v-model="newStageForm.name" placeholder="如：算法选型、台架验证" />
        </el-form-item>
        <el-form-item label="阶段描述">
          <el-input v-model="newStageForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="插入位置">
          <el-select v-model="newStageForm.insertAfterId" class="w-full" placeholder="选择位置">
            <el-option :value="null" label="插入到开头" />
            <el-option v-for="s in stageInstances" :key="s.id" :value="s.id" :label="`在「${s.name}」之后`" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="newStageForm.requireReview">评审内容</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddStage = false">取消</el-button>
        <el-button type="primary" @click="createStage">创建</el-button>
      </template>
    </el-dialog>
    
    <!-- Add TechPoint Dialog -->
    <el-dialog v-model="showAddTechPoint" title="添加技术点" width="550px">
      <el-form :model="newTechPointForm" label-position="top">
        <el-form-item label="技术点名称" required>
          <el-input v-model="newTechPointForm.name" placeholder="技术点名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newTechPointForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="第一作者" required>
          <el-select v-model="newTechPointForm.firstAuthorId" class="w-full" filterable placeholder="选择第一作者">
            <el-option 
              v-for="u in usersStore.users.filter(u => !['CUSTOMER_INTERNAL', 'CUSTOMER_EXTERNAL'].includes(u.role))" 
              :key="u.id" 
              :value="u.id" 
              :label="u.name"
            >
              <div class="flex items-center justify-between">
                <span>{{ u.name }}</span>
                <el-tag size="small" type="info">{{ u.role }}</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="技术假设">
          <el-input v-model="newTechPointForm.hypothesis" type="textarea" :rows="2" placeholder="假设 X 成立，则..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTechPoint = false">取消</el-button>
        <el-button type="primary" @click="createTechPoint">创建</el-button>
      </template>
    </el-dialog>

    <!-- Edit TechPoint Dialog -->
    <el-dialog v-model="showEditTechPoint" title="编辑技术点" width="600px">
      <el-form :model="editTechPointForm" label-position="top">
        <el-form-item label="技术点名称" required>
          <el-input v-model="editTechPointForm.name" placeholder="技术点名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editTechPointForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="技术假设">
          <el-input v-model="editTechPointForm.hypothesis" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="方法">
          <el-input v-model="editTechPointForm.approach" type="textarea" :rows="3" placeholder="采用什么方法验证假设？" />
        </el-form-item>
        <el-form-item label="结论">
          <el-input v-model="editTechPointForm.conclusion" type="textarea" :rows="3" placeholder="最终结论是什么？" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editTechPointForm.status" class="w-full">
            <el-option value="draft" label="草稿" />
            <el-option value="in_progress" label="进行中" />
            <el-option value="completed" label="已完成" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="danger" text @click="deleteTechPoint">删除技术点</el-button>
        <div class="flex-1"></div>
        <el-button @click="showEditTechPoint = false">取消</el-button>
        <el-button type="primary" @click="saveTechPointEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Edit Stage Dialog -->
    <el-dialog v-model="showEditStage" title="编辑阶段" width="550px">
      <el-form :model="editStageForm" label-position="top">
        <el-form-item label="阶段名称">
          <el-input v-model="editStageForm.name" />
        </el-form-item>
        <el-form-item label="阶段描述">
          <el-input v-model="editStageForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="阶段目标">
          <el-input v-model="editStageForm.objective" type="textarea" :rows="2" placeholder="一句话描述这个阶段要达成什么" />
        </el-form-item>
        <el-form-item label="阶段结论">
          <el-input v-model="editStageForm.conclusion" type="textarea" :rows="3" placeholder="阶段结束后的总结" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditStage = false">取消</el-button>
        <el-button type="primary" @click="saveStageEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Add Risk Dialog -->
    <el-dialog v-model="showAddRisk" title="添加风险/阻塞" width="500px">
      <el-form :model="newRiskForm" label-position="top">
        <el-form-item label="风险等级" required>
          <el-radio-group v-model="newRiskForm.level">
            <el-radio-button value="red">🔴 阻塞</el-radio-button>
            <el-radio-button value="yellow">🟡 风险</el-radio-button>
            <el-radio-button value="green">🟢 已解除</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="阻塞类型" required>
          <el-select v-model="newRiskForm.blockerType" class="w-full">
            <el-option value="需求" label="需求" />
            <el-option value="资源" label="资源" />
            <el-option value="技术" label="技术" />
            <el-option value="外部依赖" label="外部依赖" />
            <el-option value="其他" label="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="阻塞方（可选）">
          <el-input v-model="newRiskForm.blockerName" placeholder="谁/什么在阻塞？" />
        </el-form-item>
        <el-form-item label="描述" required>
          <el-input v-model="newRiskForm.description" type="textarea" :rows="3" placeholder="详细描述风险或阻塞" />
        </el-form-item>
        <el-form-item label="预计解除时间">
          <el-date-picker v-model="newRiskForm.expectedResolveDate" type="date" class="w-full" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="Owner">
          <el-select v-model="newRiskForm.ownerId" class="w-full" filterable clearable placeholder="选择负责人">
            <el-option v-for="u in usersStore.users" :key="u.id" :value="u.id" :label="u.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRisk = false">取消</el-button>
        <el-button type="primary" @click="createRisk">添加</el-button>
      </template>
    </el-dialog>

    <!-- Add Criteria Dialog -->
    <el-dialog v-model="showAddCriteria" :title="criteriaType === 'success' ? '添加成功判据' : '添加失败判据'" width="450px">
      <el-form :model="newCriteriaForm" label-position="top">
        <el-form-item label="判据内容" required>
          <el-input v-model="newCriteriaForm.text" type="textarea" :rows="2" placeholder="可量化、可验证的判据" />
        </el-form-item>
        <el-form-item v-if="criteriaType === 'success'">
          <el-checkbox v-model="newCriteriaForm.required">标记为必须达成</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCriteria = false">取消</el-button>
        <el-button type="primary" @click="addCriteriaItem">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ArrowDown } from '@element-plus/icons-vue';
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowLeft, ArrowRight, Plus, Right, MoreFilled, CircleCheck, Document, VideoPlay, Folder, Link, DataLine} from '@element-plus/icons-vue';
import dayjs from 'dayjs';

import { useTopicsStore } from '@/stores/topics';
import { useCapacityStore } from '@/stores/capacity';
import { useUsersStore } from '@/stores/users';
import { useAuthStore } from '@/stores/auth';
import { topicsApi, riskApi } from '@/api';
import type { Binding, Risk, Topic } from '@/types';

import ChangeDRIDialog from '@/components/topic/ChangeDRIDialog.vue';
import AddBindingDialog from '@/components/topic/AddBindingDialog.vue';
import AddDeliverableDialog from '@/components/topic/AddDeliverableDialog.vue';
import RichEditor from '@/components/common/RichEditor.vue';
import CoreIdeasPanel from '@/components/topics/CoreIdeasPanel.vue';
const route = useRoute();
const router = useRouter();
const topicsStore = useTopicsStore();
const capacityStore = useCapacityStore();
const usersStore = useUsersStore();
const authStore = useAuthStore();

const topicId = computed(() => Number(route.params.id));
const topic = computed(() => topicsStore.currentTopic as Topic | null);
const loading = computed(() => topicsStore.loading);

// Dialogs
const showChangeDRI = ref(false);
const showAddBinding = ref(false);
const showFieldEdit = ref(false);
const showAddStage = ref(false);
const showEditStage = ref(false);
const showAddDeliverable = ref(false);
const showAddTechPoint = ref(false);
const showEditTechPoint = ref(false);
const showAddRisk = ref(false);
const showAddCriteria = ref(false);

// Selected stage
const selectedStageId = ref<number | null>(null);

// Edit tech point
const editingTechPointId = ref<number | null>(null);
const editTechPointForm = ref({
  name: '',
  description: '',
  hypothesis: '',
  approach: '',
  conclusion: '',
  status: 'draft',
});

// Field edit
const editingField = ref<'background' | 'userGoal'>('background');
const fieldEditValue = ref('');

// Criteria edit
const criteriaType = ref<'success' | 'failure'>('success');
const newCriteriaForm = ref({ text: '', required: true });

// Risk
const risks = ref<Risk[]>([]);
const newRiskForm = ref({
  level: 'yellow',
  blockerType: '需求',
  blockerName: '',
  description: '',
  expectedResolveDate: null as Date | null,
  ownerId: null as number | null,
});

// New stage form
const newStageForm = ref({ name: '', description: '', insertAfterId: null as number | null, requireReview: false });

// Edit stage form
const editStageForm = ref({ name: '', description: '', objective: '', conclusion: '' });

// New tech point form
const newTechPointForm = ref({ name: '', description: '', firstAuthorId: null as number | null, hypothesis: '' });

// Review
const newReviewContent = ref('');

// Computed
const typeLabel = computed(() => topic.value?.type === 'UNCERTAINTY' ? '不确定性' : '演进');
const resultLabel = computed(() => topic.value?.result === 'SUCCESS' ? '已完成' : topic.value?.result === 'UNSOLVABLE' ? '无法解决' : '进行中');

const requesterName = computed(() => {
  const t: any = topic.value;
  return t?.requesterName ?? t?.requester_name ?? '';
});

// 所有登录用户（非 CUSTOMER）都可以编辑课题内容（背景、目标、风险、演进等）
const canEdit = computed(() => authStore.canEditTopic);
// 只有 ADMIN 可以变更课题状态（标记已解决/无法完成）
const canChangeResult = computed(() => authStore.isAdmin);

const normalizedBindings = computed<Binding[]>(() => {
  const t: any = topic.value;
  return (t?.bindings || []).map((b: any) => ({
    ...b,
    topicId: b.topic_id ?? b.topicId,
    slotId: b.slot_id ?? b.slotId,
    isDri: b.is_dri ?? b.isDri ?? false,
    isForced: b.is_forced ?? b.isForced ?? false,
    createdAt: b.created_at ?? b.createdAt,
    updatedAt: b.updated_at ?? b.updatedAt,
  }));
});

const driBinding = computed(() => normalizedBindings.value.find(b => b.isDri));
const driSlotName = computed(() => driBinding.value?.slot?.name || '');
const teamBindings = computed(() => normalizedBindings.value.filter(b => !b.isDri));

const canChangeDri = computed(() => {
  if (authStore.isAdmin) return true;
  const driUserId = driBinding.value?.slot?.userId;
  return driUserId && driUserId === authStore.user?.id;
});

const stageInstances = computed(() => {
  const t: any = topic.value;
  return (t?.stageInstances || t?.stage_instances || []).map((s: any) => ({
    ...s,
    topicId: s.topic_id ?? s.topicId,
    completedAt: s.completed_at ?? s.completedAt,
    completedBy: s.completed_by ?? s.completedBy,
    completedById: s.completed_by_id ?? s.completedById,
    requireReview: s.require_review ?? s.requireReview ?? false,
    reviews: s.reviews ?? [],
    techPoints: (s.tech_points ?? s.techPoints ?? []).map((tp: any) => ({
      ...tp,
      stageId: tp.stage_id ?? tp.stageId,
      firstAuthorId: tp.first_author_id ?? tp.firstAuthorId,
      firstAuthor: tp.first_author ?? tp.firstAuthor,
    })),
    successCriteria: s.success_criteria ?? s.successCriteria,
    failureCriteria: s.failure_criteria ?? s.failureCriteria,
    requiredOutputs: s.required_outputs ?? s.requiredOutputs,
  }));
});

const selectedStage = computed(() => stageInstances.value.find((s: any) => s.id === selectedStageId.value) || null);
const stageTechPoints = computed(() => selectedStage.value?.techPoints || []);

const allDeliverables = computed(() => {
  const t: any = topic.value;
  return (t?.deliverables || []).map((d: any) => ({
    ...d,
    topicId: d.topic_id ?? d.topicId,
    stageInstanceId: d.stage_instance_id ?? d.stageInstanceId,
    techPointId: d.tech_point_id ?? d.techPointId,
    createdById: d.created_by_id ?? d.createdById,
    createdBy: d.created_by ?? d.createdBy,
    createdAt: d.created_at ?? d.createdAt,
  }));
});

const stageDeliverables = computed(() => {
  if (!selectedStageId.value) return [];
  return allDeliverables.value.filter((d: any) => d.stageInstanceId === selectedStageId.value);
});

const stageReviews = computed(() => {
  if (!selectedStage.value) return [];
  return selectedStage.value.reviews || [];
});

function getStageDeliverables(stageId: number) {
  return allDeliverables.value.filter((d: any) => d.stageInstanceId === stageId);
}

// Criteria
const successCriteria = computed(() => {
  const criteria = selectedStage.value?.successCriteria;
  if (!criteria) return [];
  if (Array.isArray(criteria)) return criteria;
  return [];
});

const failureCriteria = computed(() => {
  const criteria = selectedStage.value?.failureCriteria;
  if (!criteria) return [];
  if (Array.isArray(criteria)) return criteria;
  return [];
});

const requiredOutputs = computed(() => {
  const outputs = selectedStage.value?.requiredOutputs;
  if (!outputs) return [];
  if (Array.isArray(outputs)) return outputs;
  return [];
});

// Can move back
const canMoveBack = computed(() => {
  if (!selectedStage.value) return false;
  const currentIdx = stageInstances.value.findIndex((s: any) => s.id === selectedStageId.value);
  return currentIdx > 0;
});

// Risks
const activeRisks = computed(() => risks.value.filter(r => !r.isResolved));
const redRisks = computed(() => activeRisks.value.filter(r => r.level === 'red'));
const yellowRisks = computed(() => activeRisks.value.filter(r => r.level === 'yellow'));

// Field edit
const fieldEditTitle = computed(() => editingField.value === 'background' ? '编辑课题背景' : '编辑用户视角目标');
const fieldEditPlaceholder = computed(() => editingField.value === 'background' ? '为什么要做？不做会怎样？' : '用用户/业务语言描述目标');

// Helpers
function getInitials(name?: string) {
  return name ? name.slice(0, 2).toUpperCase() : '??';
}

function getDriProfileLink() {
  const slot = driBinding.value?.slot;
  if (!slot) return '#';
  if (slot.userId) return `/profile/user/${slot.userId}`;
  return `/profile/slot/${slot.id}`;
}

function getBindingProfileLink(binding: any) {
  const slot = binding?.slot;
  if (!slot) return '#';
  if (slot.userId) return `/profile/user/${slot.userId}`;
  return `/profile/slot/${slot.id}`;
}

function formatDate(date?: string) {
  return date ? dayjs(date).format('MM-DD HH:mm') : '';
}

function formatDateTime(date?: string) {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '';
}

function getCategoryIcon(category?: string) {
  const icons: Record<string, any> = {
    document: Document,
    video: VideoPlay,
    data: DataLine,
    code: Folder,
    link: Link,
  };
  return icons[category || 'link'] || Link;
}

// Stage selection
function selectStage(stage: any) {
  selectedStageId.value = stage.id;
}

async function onHeaderResultChange(result: 'OPEN' | 'SUCCESS' | 'UNSOLVABLE') {
  if (!topic.value) return;
  try {
    await topicsStore.updateTopic(topic.value.id, { result });
    ElMessage.success('课题状态已更新');
    await refreshTopic();
  } catch (e: any) {
    console.error(e);
    ElMessage.error(e?.response?.data?.detail || '更新失败');
  }
}

// Refresh
async function refreshTopic() {
  await topicsStore.fetchTopic(topicId.value);
  await loadRisks();
}

async function afterBindingChanged() {
  await refreshTopic();
}

// Field edit
function editField(field: 'background' | 'userGoal') {
  editingField.value = field;
  const t: any = topic.value;
  fieldEditValue.value = field === 'background' ? (t?.background || '') : (t?.userGoal || t?.user_goal || '');
  showFieldEdit.value = true;
}

async function saveFieldEdit() {
  try {
    const data: any = {};
    if (editingField.value === 'background') {
      data.background = fieldEditValue.value;
    } else {
      data.user_goal = fieldEditValue.value;
    }
    await topicsApi.update(topicId.value, data);
    await refreshTopic();
    showFieldEdit.value = false;
    ElMessage.success('保存成功');
  } catch {
    ElMessage.error('保存失败');
  }
}

// Stage actions
async function createStage() {
  if (!newStageForm.value.name) {
    ElMessage.warning('请输入阶段名称');
    return;
  }
  try {
    await topicsApi.createStageInstance(topicId.value, {
      name: newStageForm.value.name,
      description: newStageForm.value.description,
      insertAfterId: newStageForm.value.insertAfterId || undefined,
      requireReview: newStageForm.value.requireReview,
    });
    await refreshTopic();
    showAddStage.value = false;
    newStageForm.value = { name: '', description: '', insertAfterId: null, requireReview: false };
    ElMessage.success('阶段创建成功');
    await refreshTopic();
} catch (err: any) {
      console.error('Create stage error:', err);
      ElMessage.error(err?.response?.data?.detail || err?.message || '创建失败');
  }
}

async function activateStage() {
  if (!selectedStageId.value) return;
  try {
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, { status: 'active' });
    await refreshTopic();
    ElMessage.success('阶段已激活');
  } catch {
    ElMessage.error('操作失败');
  }
}

async function handleMoveForward() {
  if (!selectedStageId.value) return;
  const undelivered = requiredOutputs.value.filter((o: any) => o.required && !o.delivered);
  if (undelivered.length > 0) {
    ElMessage.warning(`还有 ${undelivered.length} 个必交输出物未交付`);
    return;
  }
  try {
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, { status: 'done' });
    const currentIdx = stageInstances.value.findIndex((s: any) => s.id === selectedStageId.value);
    const nextStage = stageInstances.value[currentIdx + 1];
    
    if (nextStage && nextStage.status === 'pending') {
      await topicsApi.updateStageInstance(topicId.value, nextStage.id, { status: 'active' });
      selectedStageId.value = nextStage.id;
      ElMessage.success('阶段已完成，已进入下一阶段');
    } else if (nextStage) {
      selectedStageId.value = nextStage.id;
      ElMessage.success('阶段已完成');
    } else {
      ElMessage.success('阶段已完成（这是最后一个阶段）');
    }
    await refreshTopic();
  } catch {
    ElMessage.error('操作失败');
  }
}

async function handleMoveBack() {
  if (!selectedStageId.value) return;
  try {
    const currentIdx = stageInstances.value.findIndex((s: any) => s.id === selectedStageId.value);
    if (currentIdx > 0) {
      const prevStage = stageInstances.value[currentIdx - 1];
      await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, { status: 'pending' });
      await topicsApi.updateStageInstance(topicId.value, prevStage.id, { status: 'active' });
      selectedStageId.value = prevStage.id;
      await refreshTopic();
      ElMessage.success('已回退到上一阶段');
    }
  } catch {
    ElMessage.error('操作失败');
  }
}

async function handleReopenStage() {
  if (!selectedStageId.value) return;
  try {
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, { status: 'active' });
    await refreshTopic();
    ElMessage.success('阶段已重新打开');
  } catch {
    ElMessage.error('操作失败');
  }
}

async function copyStage() {
  if (!selectedStageId.value) return;
  try {
    await topicsApi.copyStageInstance(topicId.value, selectedStageId.value);
    await refreshTopic();
    ElMessage.success('阶段已复制');
  } catch {
    ElMessage.error('复制失败');
  }
}

async function deleteStage() {
  if (!selectedStageId.value) return;
  try {
    await ElMessageBox.confirm('确定删除此阶段？', '删除阶段', { type: 'warning' });
    await topicsApi.deleteStageInstance(topicId.value, selectedStageId.value);
    selectedStageId.value = null;
    await refreshTopic();
    ElMessage.success('阶段已删除');
  } catch {}
}

// Edit stage
function editStageField(field: string) {
  if (!selectedStage.value) return;
  editStageForm.value = {
    name: selectedStage.value.name,
    description: selectedStage.value.description || '',
    objective: selectedStage.value.objective || '',
    conclusion: selectedStage.value.conclusion || '',
  };
  showEditStage.value = true;
}

async function saveStageEdit() {
  if (!selectedStageId.value) return;
  try {
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, {
      name: editStageForm.value.name,
      description: editStageForm.value.description,
      objective: editStageForm.value.objective,
      conclusion: editStageForm.value.conclusion,
    });
    await refreshTopic();
    showEditStage.value = false;
    ElMessage.success('保存成功');
  } catch {
    ElMessage.error('保存失败');
  }
}

// Criteria
function editCriteria(type: 'success' | 'failure') {
  criteriaType.value = type;
  newCriteriaForm.value = { text: '', required: true };
  showAddCriteria.value = true;
}

async function addCriteriaItem() {
  if (!newCriteriaForm.value.text || !selectedStageId.value) return;
  
  const newItem = {
    id: Date.now().toString(),
    text: newCriteriaForm.value.text,
    checked: false,
    required: newCriteriaForm.value.required,
  };
  
  const currentList = criteriaType.value === 'success' ? [...successCriteria.value] : [...failureCriteria.value];
  currentList.push(newItem);
  
  try {
    const data: any = {};
    if (criteriaType.value === 'success') {
      data.success_criteria = currentList;
    } else {
      data.failure_criteria = currentList;
    }
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, data);
    await refreshTopic();
    showAddCriteria.value = false;
    ElMessage.success('已添加');
  } catch {
    ElMessage.error('添加失败');
  }
}

async function updateCriteriaItem(type: 'success' | 'failure', item: any) {
  if (!selectedStageId.value) return;
  const list = type === 'success' ? [...successCriteria.value] : [...failureCriteria.value];
  const idx = list.findIndex((i: any) => i.id === item.id);
  if (idx >= 0) {
    list[idx] = { ...item };
  }
  
  try {
    const data: any = {};
    if (type === 'success') {
      data.success_criteria = list;
    } else {
      data.failure_criteria = list;
    }
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, data);
    await refreshTopic();
  } catch {
    ElMessage.error('更新失败');
  }
}

async function removeCriteriaItem(type: 'success' | 'failure', itemId: string) {
  if (!selectedStageId.value) return;
  const list = type === 'success' ? successCriteria.value.filter((i: any) => i.id !== itemId) : failureCriteria.value.filter((i: any) => i.id !== itemId);
  
  try {
    const data: any = {};
    if (type === 'success') {
      data.success_criteria = list;
    } else {
      data.failure_criteria = list;
    }
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, data);
    await refreshTopic();
    ElMessage.success('已删除');
  } catch {
    ElMessage.error('删除失败');
  }
}

async function updateOutputDelivered(out: any) {
  if (!selectedStageId.value) return;
  const list = [...requiredOutputs.value];
  const idx = list.findIndex((i: any) => i.id === out.id);
  if (idx >= 0) {
    list[idx] = { ...out };
  }
  
  try {
    await topicsApi.updateStageInstance(topicId.value, selectedStageId.value, { required_outputs: list });
    await refreshTopic();
  } catch {
    ElMessage.error('更新失败');
  }
}

// Tech points
async function createTechPoint() {
  if (!newTechPointForm.value.name || !newTechPointForm.value.firstAuthorId || !selectedStageId.value) {
    ElMessage.warning('请填写必填字段');
    return;
  }
  try {
    await topicsApi.createTechPoint(topicId.value, selectedStageId.value, {
      name: newTechPointForm.value.name,
      description: newTechPointForm.value.description,
      firstAuthorId: newTechPointForm.value.firstAuthorId,
      hypothesis: newTechPointForm.value.hypothesis,
    });
    await refreshTopic();
    showAddTechPoint.value = false;
    newTechPointForm.value = { name: '', description: '', firstAuthorId: null, hypothesis: '' };
    ElMessage.success('技术点创建成功');
  } catch {
    ElMessage.error('创建失败');
  }
}

function editTechPoint(tp: any) {
  editingTechPointId.value = tp.id;
  editTechPointForm.value = {
    name: tp.name || '',
    description: tp.description || '',
    hypothesis: tp.hypothesis || '',
    approach: tp.approach || '',
    conclusion: tp.conclusion || '',
    status: tp.status || 'draft',
  };
  showEditTechPoint.value = true;
}

async function saveTechPointEdit() {
  if (!editingTechPointId.value || !selectedStageId.value) return;
  try {
    await topicsApi.updateTechPoint(topicId.value, selectedStageId.value, editingTechPointId.value, {
      name: editTechPointForm.value.name,
      description: editTechPointForm.value.description,
      hypothesis: editTechPointForm.value.hypothesis,
      approach: editTechPointForm.value.approach,
      conclusion: editTechPointForm.value.conclusion,
      status: editTechPointForm.value.status,
    });
    await refreshTopic();
    showEditTechPoint.value = false;
    ElMessage.success('保存成功');
  } catch {
    ElMessage.error('保存失败');
  }
}

async function deleteTechPoint() {
  if (!editingTechPointId.value || !selectedStageId.value) return;
  try {
    await ElMessageBox.confirm('确定删除此技术点？删除后无法恢复。', '删除技术点', { type: 'warning' });
    await topicsApi.deleteTechPoint(topicId.value, selectedStageId.value, editingTechPointId.value);
    await refreshTopic();
    showEditTechPoint.value = false;
    ElMessage.success('已删除');
  } catch {}
}

// Deliverables
async function deleteDeliverable(id: number) {
  try {
    await ElMessageBox.confirm('确定删除此交付物？', '删除', { type: 'warning' });
    await topicsApi.deleteDeliverable(id);
    await refreshTopic();
    ElMessage.success('已删除');
  } catch {}
}

// Reviews
function canDeleteReview(review: any) {
  return authStore.isAdmin || review.createdBy?.id === authStore.user?.id;
}

async function submitReview() {
  if (!newReviewContent.value.trim() || !selectedStageId.value) return;
  try {
    await topicsApi.addStageReview(topicId.value, selectedStageId.value, newReviewContent.value);
    newReviewContent.value = '';
    await refreshTopic();
    ElMessage.success('评审意见已提交');
  } catch {
    ElMessage.error('提交失败');
  }
}

async function deleteReview(reviewId: number) {
  if (!selectedStageId.value) return;
  try {
    await ElMessageBox.confirm('确定删除此评审意见？', '删除', { type: 'warning' });
    await topicsApi.deleteStageReview(topicId.value, selectedStageId.value, reviewId);
    await refreshTopic();
    ElMessage.success('已删除');
  } catch {}
}

// Risks
async function loadRisks() {
  try {
    risks.value = await riskApi.list(topicId.value);
  } catch {
    console.error('Failed to load risks');
  }
}

async function createRisk() {
  if (!newRiskForm.value.description || !newRiskForm.value.blockerType) {
    ElMessage.warning('请填写必填字段');
    return;
  }
  try {
    await riskApi.create({
      topicId: topicId.value,
      stageInstanceId: selectedStageId.value || undefined,
      level: newRiskForm.value.level,
      blockerType: newRiskForm.value.blockerType,
      blockerName: newRiskForm.value.blockerName || undefined,
      description: newRiskForm.value.description,
      expectedResolveDate: newRiskForm.value.expectedResolveDate?.toISOString(),
      ownerId: newRiskForm.value.ownerId || undefined,
    });
    await loadRisks();
    showAddRisk.value = false;
    newRiskForm.value = { level: 'yellow', blockerType: '需求', blockerName: '', description: '', expectedResolveDate: null, ownerId: null };
    ElMessage.success('风险已添加');
  } catch {
    ElMessage.error('添加失败');
  }
}

async function resolveRisk(risk: Risk) {
  try {
    const note = await ElMessageBox.prompt('请输入解决说明（可选）', '标记解决', { inputPlaceholder: '如何解决的？' });
    await riskApi.resolve(risk.id, note.value || undefined);
    await loadRisks();
    ElMessage.success('风险已标记解决');
  } catch {}
}

async function deleteRisk(id: number) {
  try {
    await ElMessageBox.confirm('确定删除此风险？', '删除', { type: 'warning' });
    await riskApi.delete(id);
    await loadRisks();
    ElMessage.success('已删除');
  } catch {}
}

// Init
onMounted(async () => {
  await topicsStore.fetchTopic(topicId.value);
  await capacityStore.fetchSlots();
  await usersStore.fetchUsers();
  await loadRisks();
  
  if (stageInstances.value.length > 0 && !selectedStageId.value) {
    selectedStageId.value = stageInstances.value[0].id;
  }
});

watch(topicId, async (id) => {
  if (id) {
    await topicsStore.fetchTopic(id);
    await loadRisks();
  }
});
</script>

<style scoped>
/* ============ Page Layout ============ */
.topic-detail-page {
  padding: var(--space-5);
  max-width: 1200px;
  margin: 0 auto;
}
.header-result-clickable {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.back-btn {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}
.back-btn:hover {
  color: var(--color-primary);
}

/* ============ Topic Header ============ */
.topic-header {
  padding: var(--space-5);
}
.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
}
.title-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}
.topic-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}
.topic-id {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}

/* Priority Tags */
.priority-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}
.priority-p0 {
  background: var(--color-priority-p0-bg);
  color: var(--color-priority-p0);
  border: 1px solid var(--color-priority-p0-border);
}
.priority-p1 {
  background: var(--color-priority-p1-bg);
  color: var(--color-priority-p1);
  border: 1px solid var(--color-priority-p1-border);
}
.priority-p2 {
  background: var(--color-priority-p2-bg);
  color: var(--color-priority-p2);
  border: 1px solid var(--color-priority-p2-border);
}

.type-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  background: var(--color-neutral-100);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-light);
}

/* Result Badge */
.result-badge {
  display: inline-flex;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}
.result-success {
  background: var(--color-stage-done-bg);
  color: var(--color-stage-done);
  border: 1px solid var(--color-stage-done-border);
}
.result-unsolvable {
  background: var(--color-danger-50);
  color: var(--color-danger-600);
  border: 1px solid var(--color-danger-100);
}
.result-ongoing {
  background: var(--color-neutral-100);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-light);
}

/* Meta Row */
.meta-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}
.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.meta-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
.meta-value {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}
.meta-empty {
  font-size: var(--text-sm);
  color: var(--color-text-disabled);
}
.meta-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border-light);
}
.meta-action {
  color: var(--color-primary);
  font-size: var(--text-xs);
}
.closed-time {
  color: var(--color-success-600);
}

/* DRI Chip */
.dri-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 3px 10px;
  background: var(--color-dri-bg);
  border: 1px solid var(--color-dri-border);
  border-radius: var(--radius-md);
}
.dri-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-dri);
}
.dri-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-dri);
  text-decoration: none;
}
.dri-name:hover {
  text-decoration: underline;
}
.dri-badge {
  font-size: 9px;
  font-weight: var(--font-semibold);
  color: var(--color-dri);
  background: rgba(82, 106, 131, 0.15);
  padding: 1px 4px;
  border-radius: 3px;
  letter-spacing: 0.5px;
}

/* Team Avatars */
.team-avatars {
  display: flex;
  margin-left: -4px;
}
.team-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-neutral-200);
  border: 2px solid var(--color-bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  text-decoration: none;
  margin-left: -4px;
  transition: var(--transition-fast);
}
.team-avatar:hover {
  z-index: 1;
  box-shadow: 0 0 0 2px var(--color-primary-100);
}
.team-avatar.more {
  background: var(--color-neutral-300);
}

/* ============ Risks Section ============ */
.risks-section {
  overflow: hidden;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}
.section-title-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.section-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}
.risk-count {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}
.risk-count.risk-red {
  background: var(--color-danger-50);
  color: var(--color-danger-600);
}
.risk-count.risk-yellow {
  background: var(--color-warning-50);
  color: var(--color-warning-600);
}

/* 用原生 CSS 实现 Tailwind 的 divide-y（只对直接子元素生效） */
.risks-list > * + * {
  border-top: 1px solid var(--color-border-light);
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
}

.risk-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.risk-indicator.risk-red { background: var(--color-stage-blocked); }
.risk-indicator.risk-yellow { background: var(--color-warning-500); }
.risk-indicator.risk-green { background: var(--color-stage-done); }

.risk-content {
  flex: 1;
  min-width: 0;
}
.risk-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}
.risk-type {
  font-size: var(--text-xs);
  padding: 2px 6px;
  background: var(--color-neutral-100);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
}
.risk-blocker {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
.risk-desc {
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
}
.risk-footer {
  display: flex;
  gap: var(--space-4);
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}
.risk-actions {
  display: flex;
  gap: var(--space-1);
}

/* ============ Context Grid ============ */
.context-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}
@media (max-width: 1024px) {
  .context-grid {
    grid-template-columns: 1fr;
  }
}
.context-card {
  padding: var(--space-4);
}
.context-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}
.context-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
.context-tag {
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  padding: 1px 4px;
  border-radius: 3px;
  margin-right: var(--space-1);
}
.context-tag.why {
  background: var(--color-warning-100);
  color: var(--color-warning-600);
}
.context-tag.what {
  background: var(--color-primary-100);
  color: var(--color-primary);
}
.context-content {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}
.context-placeholder {
  font-size: var(--text-sm);
  color: var(--color-text-disabled);
  font-style: italic;
  margin: 0;
}

/* ============ Timeline Section ============ */
.timeline-section {
  overflow: hidden;
}
.timeline-container {
  padding: var(--space-4);
}
.timeline-track {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-2);
}
.timeline-item {
  display: flex;
  align-items: center;
}
.timeline-connector {
  padding: 0 var(--space-2);
  color: var(--color-text-disabled);
}

.stage-card {
  position: relative;
  min-width: 160px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border-default);
  background: var(--color-bg-elevated);
  cursor: pointer;
  transition: var(--transition-fast);
}
.stage-card:hover {
  border-color: var(--color-border-hover);
}
.stage-card.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-50);
  box-shadow: var(--shadow-sm);
}
.stage-card.status-done {
  border-color: var(--color-stage-done-border);
  background: var(--color-stage-done-bg);
}
.stage-card.status-active {
  border-color: var(--color-stage-active-border);
  background: var(--color-stage-active-bg);
}

.stage-status-dot {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--color-bg-elevated);
}
.stage-status-dot.status-done { background: var(--color-stage-done); }
.stage-status-dot.status-active { background: var(--color-stage-active); }
.stage-status-dot.status-pending { background: var(--color-neutral-300); }

.stage-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.stage-status-text {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0 0;
}
.stage-counts {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-disabled);
}

/* 阶段完成者信息 */
.stage-completed-info {
  margin-top: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px dashed var(--color-border-light);
  font-size: 10px;
  color: var(--color-text-tertiary);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stage-completed-info .completed-by-name {
  color: var(--color-stage-done);
  font-weight: var(--font-medium);
}
.stage-completed-info .completed-at-time {
  color: var(--color-text-disabled);
}

/* ============ Stage Detail ============ */
.stage-detail {
  overflow: hidden;
}
.stage-detail-header {
  flex-wrap: wrap;
  gap: var(--space-3);
}
.stage-info {
  flex: 1;
  min-width: 200px;
}
.stage-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.stage-badge {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}
.stage-badge.status-done {
  background: var(--color-stage-done-bg);
  color: var(--color-stage-done);
}
.stage-badge.status-active {
  background: var(--color-stage-active-bg);
  color: var(--color-stage-active);
}
.stage-badge.status-pending {
  background: var(--color-neutral-100);
  color: var(--color-text-tertiary);
}
.stage-desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: var(--space-1) 0 0 0;
}
.stage-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.stage-content {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ============ Completion Info ============ */
.completion-info {
  padding: var(--space-4);
  background: var(--color-stage-done-bg);
  border: 1px solid var(--color-stage-done-border);
  border-radius: var(--radius-md);
}
.completion-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}
.completion-icon {
  color: var(--color-stage-done);
}
.completion-title {
  font-weight: var(--font-medium);
  color: var(--color-stage-done);
}
.completion-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  font-size: var(--text-sm);
}
.completion-item {
  display: flex;
  gap: var(--space-2);
}
.completion-label {
  color: var(--color-text-tertiary);
}
.completion-value {
  color: var(--color-text-primary);
}
.completion-note, .remaining-issues {
  margin-top: var(--space-2);
}
.note-label, .issues-label {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}
.note-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: var(--space-1) 0 0 0;
}
.issues-label {
  color: var(--color-warning-600);
}
.issues-text {
  font-size: var(--text-sm);
  color: var(--color-warning-700);
  margin: var(--space-1) 0 0 0;
}

/* ============ Criteria Grid ============ */
.criteria-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}
.criteria-grid > .objective-card {
  grid-column: span 2;
}
@media (max-width: 1024px) {
  .criteria-grid {
    grid-template-columns: 1fr;
  }
  .criteria-grid > .objective-card {
    grid-column: span 1;
  }
}

.objective-card {
  padding: var(--space-4);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
}
.objective-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}
.objective-title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
  margin: 0;
}
.objective-text {
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  margin: 0;
}

.criteria-card {
  padding: var(--space-4);
  border-radius: var(--radius-md);
}
.criteria-card.success {
  background: var(--color-stage-done-bg);
}
.criteria-card.failure {
  background: var(--color-danger-50);
}
.criteria-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}
.criteria-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  margin: 0;
}
.criteria-card.success .criteria-title {
  color: var(--color-stage-done);
}
.criteria-card.failure .criteria-title {
  color: var(--color-danger-600);
}
.criteria-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.criteria-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
}
.criteria-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  flex: 1;
}
.criteria-text.checked {
  text-decoration: line-through;
  color: var(--color-text-disabled);
}
.required-badge {
  font-size: var(--text-xs);
  padding: 1px 4px;
  background: var(--color-danger-100);
  color: var(--color-danger-600);
  border-radius: var(--radius-xs);
  margin-left: var(--space-1);
}
.criteria-empty {
  font-size: var(--text-xs);
  font-style: italic;
  margin: 0;
}
.criteria-card.success .criteria-empty {
  color: var(--color-success-600);
}
.criteria-card.failure .criteria-empty {
  color: var(--color-danger-500);
}

/* ============ Deliverables Section ============ */
.deliverables-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-5);
}
.deliverables-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
.deliverables-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.outputs-checklist {
  padding: var(--space-3);
  background: var(--color-warning-50);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
}
.outputs-title {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--color-warning-700);
  margin: 0 0 var(--space-2) 0;
}
.outputs-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.output-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
}
.output-name {
  color: var(--color-text-secondary);
}
.output-name.delivered {
  color: var(--color-text-disabled);
  text-decoration: line-through;
}
.output-badge {
  font-size: var(--text-xs);
  padding: 1px 4px;
  border-radius: var(--radius-xs);
}
.output-badge.required {
  background: var(--color-danger-100);
  color: var(--color-danger-600);
}
.output-badge.optional {
  background: var(--color-neutral-100);
  color: var(--color-text-tertiary);
}

.deliverables-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}
@media (max-width: 768px) {
  .deliverables-grid {
    grid-template-columns: 1fr;
  }
}
.deliverable-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
  transition: var(--transition-fast);
}
.deliverable-card:hover {
  background: var(--color-neutral-100);
}
.deliverable-card:hover .deliverable-delete {
  opacity: 1;
}
.deliverable-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.deliverable-icon.category-document { background: var(--color-primary-100); color: var(--color-primary); }
.deliverable-icon.category-video { background: #F3E8FF; color: #9333EA; }
.deliverable-icon.category-data { background: var(--color-success-100); color: var(--color-success-600); }
.deliverable-icon.category-code { background: var(--color-warning-100); color: var(--color-warning-600); }
.deliverable-icon.category-link { background: var(--color-neutral-100); color: var(--color-text-secondary); }

.deliverable-info {
  flex: 1;
  min-width: 0;
}
.deliverable-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  text-decoration: none;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.deliverable-name:hover {
  color: var(--color-primary);
}
.deliverable-meta {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0 0;
}
.deliverable-delete {
  opacity: 0;
  transition: var(--transition-fast);
}

.deliverables-empty {
  text-align: center;
  padding: var(--space-5);
  border: 2px dashed var(--color-border-light);
  border-radius: var(--radius-md);
}
.empty-text {
  font-size: var(--text-sm);
  color: var(--color-text-disabled);
  margin: 0;
}
.empty-hint {
  font-size: var(--text-xs);
  color: var(--color-text-disabled);
  margin: var(--space-1) 0 0 0;
}

/* ============ Reviews Section ============ */
.reviews-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-5);
}
.reviews-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
.reviews-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}
.reviews-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.review-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
}
.review-content {
  flex: 1;
}
.review-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
}
.review-author {
  font-weight: var(--font-medium);
  color: var(--color-primary);
}
.review-dot {
  color: var(--color-text-disabled);
}
.review-time {
  color: var(--color-text-tertiary);
}
.review-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: 0;
  white-space: pre-wrap;
}
.reviews-empty {
  text-align: center;
  padding: var(--space-4);
}
.review-input {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}
.review-input .el-textarea {
  flex: 1;
}

/* ============ Tech Points Section ============ */
.techpoints-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-5);
}
.techpoints-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
.techpoints-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}
.techpoints-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.techpoint-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-4);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-md);
  transition: var(--transition-fast);
}
.techpoint-card:hover {
  border-color: var(--color-border-hover);
}
.techpoint-main {
  flex: 1;
  min-width: 0;
}
.techpoint-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}
.techpoint-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  margin: 0;
}
.techpoint-status {
  font-size: var(--text-xs);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}
.techpoint-status.status-completed {
  background: var(--color-stage-done-bg);
  color: var(--color-stage-done);
}
.techpoint-status.status-in_progress {
  background: var(--color-stage-active-bg);
  color: var(--color-stage-active);
}
.techpoint-status.status-draft {
  background: var(--color-neutral-100);
  color: var(--color-text-tertiary);
}
.techpoint-desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-2) 0;
}
.techpoint-authors {
  display: flex;
  gap: var(--space-4);
  font-size: var(--text-xs);
}
.author-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
.author-label {
  color: var(--color-text-tertiary);
}
.author-name {
  color: var(--color-text-secondary);
}
.author-name.primary {
  font-weight: var(--font-semibold);
  color: var(--color-primary);
}
.techpoint-hypothesis {
  margin-top: var(--space-2);
  padding: var(--space-2);
  background: var(--color-warning-50);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--color-warning-700);
}
.hypothesis-label {
  font-weight: var(--font-medium);
  margin-right: var(--space-1);
}
.techpoints-empty {
  text-align: center;
  padding: var(--space-5);
}

/* ============ Empty State ============ */
.empty-state {
  text-align: center;
  padding: var(--space-5);
  color: var(--color-text-disabled);
  font-size: var(--text-sm);
}

/* ============ Rich Content ============ */
.rich-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
  margin: var(--space-2) 0;
}
.rich-content :deep(p) {
  margin: 0 0 var(--space-2) 0;
}
.rich-content :deep(p:last-child) {
  margin-bottom: 0;
}
.rich-content :deep(ul),
.rich-content :deep(ol) {
  margin: 0 0 var(--space-2) 0;
  padding-left: var(--space-4);
}
.rich-content :deep(a) {
  color: var(--color-primary);
}
.rich-content :deep(code) {
  background: var(--color-neutral-100);
  padding: 1px 4px;
  border-radius: var(--radius-xs);
  font-size: 0.9em;
}
.rich-content :deep(pre) {
  background: var(--color-neutral-100);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  overflow-x: auto;
}
.rich-content :deep(blockquote) {
  border-left: 3px solid var(--color-border-default);
  padding-left: var(--space-3);
  margin: var(--space-2) 0;
  color: var(--color-text-secondary);
}

/* ============ Utilities ============ */
.space-y-5 > * + * {
  margin-top: var(--space-5);
}
.flex-1 {
  flex: 1;
}
.w-full {
  width: 100%;
}
</style>
