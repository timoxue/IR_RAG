<template>
  <el-form :model="form" label-width="100px" @submit.prevent>
    <el-form-item label="知识库AID">
      <el-input v-model="form.kb_a_id" placeholder="kb_a_id" />
    </el-form-item>
    <el-form-item label="标准库BID">
      <el-input v-model="form.kb_b_id" placeholder="kb_b_id" />
    </el-form-item>
    <el-form-item label="问题">
      <el-input v-model="form.question" type="textarea" :rows="3" />
    </el-form-item>
    <el-form-item label="Prompt">
      <el-input v-model="form.prompt" type="textarea" :rows="3" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" :loading="loading" @click="ask">提问</el-button>
    </el-form-item>
  </el-form>

  <el-row :gutter="16">
    <el-col :span="12">
      <el-card header="初稿 (A为主)">
        <pre class="pre">{{ result?.initial }}</pre>
      </el-card>
    </el-col>
    <el-col :span="12">
      <el-card header="对齐后 (B校验)">
        <pre class="pre">{{ result?.aligned }}</pre>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import api from '../api'

const form = reactive({ kb_a_id: '', kb_b_id: '', question: '', prompt: '' })
const result = ref<any>(null)
const loading = ref(false)

async function ask() {
  loading.value = true
  try {
    const { data } = await api.post('/api/v1/qa/answer', form)
    result.value = data
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.pre { white-space: pre-wrap; }
</style>
