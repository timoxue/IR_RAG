<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card header="待审核">
        <el-select v-model="filter" placeholder="状态过滤" style="width:100%">
          <el-option label="全部" value="" />
          <el-option label="待审核" value="pending" />
          <el-option label="需修订" value="needs_revision" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button style="margin-top:8px" @click="load">刷新</el-button>
        <el-menu style="margin-top:8px" @select="onSelect">
          <el-menu-item v-for="t in tasks" :key="t.id" :index="String(t.id)">
            #{{ t.id }} | Q{{ t.question_id }} | {{ t.status }}
          </el-menu-item>
        </el-menu>
      </el-card>
    </el-col>
    <el-col :span="16">
      <el-card :header="detailHeader">
        <template v-if="detail">
          <el-row :gutter="16">
            <el-col :span="12">
              <h4>初稿</h4>
              <pre class="pre">{{ detail.initial_answer }}</pre>
            </el-col>
            <el-col :span="12">
              <h4>对齐后</h4>
              <pre class="pre">{{ detail.aligned_answer }}</pre>
            </el-col>
          </el-row>
          <el-divider />
          <h4>对齐信息</h4>
          <div v-if="conflicts && conflicts.length">
            <el-alert title="发现冲突" type="warning" show-icon />
            <el-timeline>
              <el-timeline-item v-for="(c, i) in conflicts" :key="i" :timestamp="c.type">
                {{ c.message }}
              </el-timeline-item>
            </el-timeline>
          </div>
          <pre class="pre">{{ detail.alignment }}</pre>
          <el-divider />
          <el-input v-model="comments" type="textarea" :rows="3" placeholder="审核意见" />
          <div style="margin-top:8px">
            <el-button type="success" @click="act('approve')">通过</el-button>
            <el-button type="warning" @click="act('request_changes')">退回修订</el-button>
            <el-button type="danger" @click="act('reject')">拒绝</el-button>
          </div>
          <el-divider />
          <h4>标注为标准回答</h4>
          <el-input v-model="topicKey" placeholder="topic_key（规范化主题键）" />
          <el-switch v-model="strong" active-text="强约束" style="margin-top:8px" />
          <div style="margin-top:8px">
            <el-button type="primary" @click="promote">保存为标准回答</el-button>
          </div>
          <div v-if="promoteResp" style="margin-top:8px">
            <el-alert :title="'Promote: ' + promoteResp" type="success" show-icon />
          </div>
        </template>
        <template v-else>
          <el-empty description="选择一个任务" />
        </template>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import api from '../api'

const tasks = ref<any[]>([])
const filter = ref('pending')
const selectedId = ref<number | null>(null)
const detail = ref<any>(null)
const comments = ref('')

const topicKey = ref('')
const strong = ref(false)
const promoteResp = ref('')

const conflicts = computed(() => {
  const al = detail.value?.alignment
  if (!al) return []
  if (al.conflicts) return al.conflicts
  if (al.raw) {
    try { const obj = JSON.parse(al.raw); return obj.conflicts || [] } catch { return [] }
  }
  return []
})

const detailHeader = computed(() => selectedId.value ? `任务 #${selectedId.value}` : '任务详情')

async function load() {
  const { data } = await api.get('/api/v1/reviews', { params: { status: filter.value || undefined } })
  tasks.value = data.tasks
}

async function onSelect(key: string) {
  selectedId.value = Number(key)
  const { data } = await api.get(`/api/v1/reviews/${selectedId.value}`)
  detail.value = data
}

async function act(action: 'approve'|'request_changes'|'reject') {
  if (!selectedId.value) return
  await api.post(`/api/v1/reviews/${selectedId.value}/${action}`, { comments: comments.value })
  await load()
}

async function promote() {
  if (!detail.value || !topicKey.value) return
  const content = detail.value.aligned_answer || detail.value.initial_answer || ''
  const { data } = await api.post('/api/v1/standards/promote', {
    topic_key: topicKey.value,
    content,
    strong_constraint: strong.value,
  })
  promoteResp.value = JSON.stringify(data)
}

load()
</script>

<style scoped>
.pre { white-space: pre-wrap; }
</style>
