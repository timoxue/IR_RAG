<template>
  <el-container style="height:100vh">
    <el-header>
      <h2>IR RAG Console</h2>
    </el-header>
    <el-main>
      <el-tabs v-model="active">
        <el-tab-pane label="QA" name="qa">
          <QAView />
        </el-tab-pane>
        <el-tab-pane label="批量导入" name="imports">
          <ImportsView />
        </el-tab-pane>
        <el-tab-pane label="标准回答" name="standards">
          <StandardsView />
        </el-tab-pane>
        <el-tab-pane label="Prompt" name="prompts">
          <PromptsView />
        </el-tab-pane>
        <el-tab-pane label="审核工作台" name="reviews">
          <ReviewsView />
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import QAView from './views/QAView.vue'
import ImportsView from './views/ImportsView.vue'
import StandardsView from './views/StandardsView.vue'
import PromptsView from './views/PromptsView.vue'
import ReviewsView from './views/ReviewsView.vue'

const active = ref('qa')
</script>

<style>
body { margin: 0; }
</style>
