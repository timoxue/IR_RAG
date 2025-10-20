<template>
  <el-form :model="form" label-width="120px" @submit.prevent>
    <el-form-item label="Topic Key">
      <el-input v-model="form.topic_key" />
    </el-form-item>
    <el-form-item label="强约束">
      <el-switch v-model="form.strong_constraint" />
    </el-form-item>
    <el-form-item label="内容">
      <el-input type="textarea" :rows="6" v-model="form.content" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="promote">保存为标准回答</el-button>
    </el-form-item>
  </el-form>
  <pre class="pre">{{ resp }}</pre>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import axios from 'axios'

const form = reactive({ topic_key: '', content: '', strong_constraint: false })
const resp = ref('')

async function promote() {
  const { data } = await axios.post('/api/v1/standards/promote', form)
  resp.value = JSON.stringify(data, null, 2)
}
</script>

<style scoped>
.pre { white-space: pre-wrap; }
</style>
