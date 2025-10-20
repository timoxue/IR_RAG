<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card header="导入 知识库A">
        <input type="file" @change="e => upload(e, '/api/v1/imports/knowledge-a', { kb_a_id })" />
        <el-input v-model="kb_a_id" placeholder="kb_a_id" style="margin-top:8px" />
        <div style="margin-top:8px">
          <a :href="'/samples/knowledge_a.csv'" target="_blank">下载模板 knowledge_a.csv</a>
        </div>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card header="导入 标准库B">
        <input type="file" @change="e => upload(e, '/api/v1/imports/standards-b')" />
        <div style="margin-top:8px">
          <a :href="'/samples/standards_b.csv'" target="_blank">下载模板 standards_b.csv</a>
        </div>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card header="导入 待回答问题">
        <input type="file" @change="e => upload(e, '/api/v1/imports/questions', { kb_a_id, kb_b_id, generate, prompt })" />
        <div style="margin-top:8px">
          <el-input v-model="kb_a_id" placeholder="kb_a_id" />
          <el-input v-model="kb_b_id" placeholder="kb_b_id" style="margin-top:8px" />
          <el-switch v-model="generate" active-text="自动生成" style="margin-top:8px" />
          <el-input v-model="prompt" placeholder="prompt" style="margin-top:8px" />
          <div style="margin-top:8px">
            <a :href="'/samples/questions.csv'" target="_blank">下载模板 questions.csv</a>
          </div>
        </div>
      </el-card>
    </el-col>
  </el-row>

  <el-divider />
  <pre class="pre">{{ resp }}</pre>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '../api'

const resp = ref('')
const kb_a_id = ref('')
const kb_b_id = ref('')
const generate = ref(true)
const prompt = ref('')

async function upload(event: Event, url: string, params?: Record<string, any>) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  const form = new FormData()
  form.append('file', input.files[0])
  const { data } = await api.post(url, form, { params })
  resp.value = JSON.stringify(data, null, 2)
}
</script>

<style scoped>
.pre { white-space: pre-wrap; }
</style>
