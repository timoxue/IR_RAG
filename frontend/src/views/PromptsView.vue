<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card header="模板列表">
        <el-button size="small" @click="load">刷新</el-button>
        <el-menu style="margin-top:8px" @select="onSelect">
          <el-menu-item v-for="p in items" :key="p.id" :index="String(p.id)">
            {{ p.name }} v{{ p.version }}
          </el-menu-item>
        </el-menu>
      </el-card>
    </el-col>
    <el-col :span="16">
      <el-card header="编辑">
        <el-form label-width="100px" @submit.prevent>
          <el-form-item label="名称">
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="form.is_active" />
          </el-form-item>
          <el-form-item label="内容">
            <el-input v-model="form.content" type="textarea" :rows="10" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="create">新建</el-button>
            <el-button @click="newVersion">新版本</el-button>
          </el-form-item>
        </el-form>
        <pre class="pre">{{ resp }}</pre>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '../api'

const items = ref<any[]>([])
const form = ref({ name: '', is_active: true, content: '' })
const resp = ref('')

async function load() {
  const { data } = await api.get('/api/v1/prompts')
  items.value = data
}

async function onSelect(key: string) {
  const p = items.value.find((i: any) => String(i.id) === key)
  if (p) {
    form.value = { name: p.name, is_active: p.is_active, content: p.content }
  }
}

async function create() {
  const { data } = await api.post('/api/v1/prompts', form.value, { headers: { 'X-User-Email': 'ir@example.com' } })
  resp.value = JSON.stringify(data)
  await load()
}

async function newVersion() {
  const { data } = await api.post(`/api/v1/prompts/${encodeURIComponent(form.value.name)}/new_version`, form.value, { headers: { 'X-User-Email': 'ir@example.com' } })
  resp.value = JSON.stringify(data)
  await load()
}

load()
</script>

<style scoped>
.pre { white-space: pre-wrap; }
</style>
