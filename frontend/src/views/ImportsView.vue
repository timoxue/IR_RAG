<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card header="导入 知识库A（纯ZIP）">
        <div style="margin-bottom:8px">ZIP文件包：<input type="file" ref="zipOnlyFile" accept=".zip" /></div>
        <el-input v-model="kb_a_id" placeholder="kb_a_id" style="margin-top:8px" />
        <el-select v-model="default_category" placeholder="默认分类" style="margin-top:8px;width:100%">
          <el-option label="公告" value="announcement" />
          <el-option label="研报" value="research" />
          <el-option label="FAQ" value="faq" />
          <el-option label="政策" value="policy" />
          <el-option label="披露" value="disclosure" />
        </el-select>
        <el-button type="primary" size="small" style="margin-top:8px" @click="uploadZipOnly">上传</el-button>
        <div style="margin-top:8px;font-size:12px;color:#999">自动从文件名提取标题</div>
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card header="导入 知识库A（混合）">
        <div style="margin-bottom:8px">CSV元数据：<input type="file" ref="csvFile" accept=".csv,.xlsx" /></div>
        <div style="margin-bottom:8px">ZIP文件包：<input type="file" ref="zipFile" accept=".zip" /></div>
        <el-input v-model="kb_a_id" placeholder="kb_a_id" style="margin-top:8px" />
        <el-button type="primary" size="small" style="margin-top:8px" @click="uploadHybrid">上传</el-button>
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
const default_category = ref('announcement')

const csvFile = ref<HTMLInputElement | null>(null)
const zipFile = ref<HTMLInputElement | null>(null)
const zipOnlyFile = ref<HTMLInputElement | null>(null)

async function upload(event: Event, url: string, params?: Record<string, any>) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  const form = new FormData()
  form.append('file', input.files[0])
  const { data } = await api.post(url, form, { params })
  resp.value = JSON.stringify(data, null, 2)
}

async function uploadHybrid() {
  const csv = csvFile.value?.files?.[0]
  const zip = zipFile.value?.files?.[0]
  if (!csv || !zip || !kb_a_id.value) {
    resp.value = '请选择 CSV、ZIP 并填写 kb_a_id'
    return
  }
  const form = new FormData()
  form.append('csv_file', csv)
  form.append('zip_file', zip)
  const { data } = await api.post('/api/v1/imports/knowledge-a-hybrid', form, { params: { kb_a_id: kb_a_id.value } })
  resp.value = JSON.stringify(data, null, 2)
}

async function uploadZipOnly() {
  const zip = zipOnlyFile.value?.files?.[0]
  if (!zip || !kb_a_id.value) {
    resp.value = '请选择 ZIP 并填写 kb_a_id'
    return
  }
  const form = new FormData()
  form.append('zip_file', zip)
  const { data } = await api.post('/api/v1/imports/knowledge-a-zip', form, { params: { kb_a_id: kb_a_id.value, default_category: default_category.value } })
  resp.value = JSON.stringify(data, null, 2)
}
</script>

<style scoped>
.pre { white-space: pre-wrap; }
</style>
