<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="seal">校</span>
        <div>
          <strong>校园百事通</strong>
          <small>CAMPUS POLICY RAG</small>
        </div>
      </div>
      <nav>
        <RouterLink to="/">教务问答</RouterLink>
        <RouterLink to="/documents">教务政策库</RouterLink>
        <RouterLink to="/evaluation">效果评估</RouterLink>
        <RouterLink to="/settings">模型设置</RouterLink>
      </nav>
      <div class="notice">
        <b>证据约束</b>
        <span>回答只依据已入库的教务政策条款，并给出可回溯的文件、章节与页码。</span>
      </div>
      <p class="side-foot">广东工业大学 · 教务处试点 · v1.0</p>
    </aside>
    <main>
      <RouterView />
    </main>
  </div>
</template>
