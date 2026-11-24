<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";

const documents = ref<any[]>([]);
const file = ref<File>();
const topic = ref("");
const effectiveDate = ref("");
const busy = ref(false);
const error = ref("");

const STATUS_LABELS: Record<string, string> = {
  pending: "待处理",
  indexing: "解析中",
  ready: "已就绪",
  failed: "失败",
};
const statusLabel = (status: string) => STATUS_LABELS[status] ?? status;

function getErrorMessage(exc: any) {
  const detail = exc.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join("；");
  }
  return exc.message || "上传失败，请确认后端服务已启动";
}

async function load() {
  documents.value = (await api.get("/documents")).data;
}
async function upload() {
  if (!file.value) return;
  const normalizedTopic = topic.value.trim();
  if (!normalizedTopic) {
    error.value = "请先填写政策主题";
    return;
  }
  busy.value = true;
  error.value = "";
  const form = new FormData();
  form.append("file", file.value);
  // 兼容当前后端（query 参数）和新版后端（multipart 表单字段）。
  form.append("topic", normalizedTopic);
  if (effectiveDate.value) form.append("effective_date", effectiveDate.value);
  try {
    await api.post("/documents/", form, {
      params: {
        topic: normalizedTopic,
        ...(effectiveDate.value && { effective_date: effectiveDate.value }),
      },
    });
    file.value = undefined;
    await load();
  } catch (exc: any) {
    error.value = getErrorMessage(exc);
  } finally {
    busy.value = false;
  }
}
async function remove(id: string) {
  await api.delete(`/documents/${id}`);
  await load();
}
async function rebuild() {
  busy.value = true;
  await api.post("/documents/rebuild");
  await load();
  busy.value = false;
}
onMounted(load);
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">POLICY LIBRARY</p>
        <h1>教务政策库</h1>
        <p>上传管理规定、实施细则后，自动完成父子分块、向量化与索引。</p>
      </div>
      <button class="secondary" :disabled="busy" @click="rebuild">重建索引</button>
    </header>
    <div class="grid two">
      <div class="card">
        <h2>导入政策文件</h2>
        <label>政策主题<input v-model="topic" required placeholder="例如：学籍管理" /></label>
        <label>施行日期<input v-model="effectiveDate" type="date" /></label>
        <label class="drop">
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            @change="file = ($event.target as HTMLInputElement).files?.[0]"
          />
          <b>{{ file?.name || "选择 PDF、DOCX 或 TXT" }}</b>
          <span>单个文件不超过 20MB</span>
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button :disabled="!file || !topic.trim() || busy" @click="upload">
          {{ busy ? "处理中…" : "上传并建立索引" }}
        </button>
      </div>
      <div class="card">
        <div class="card-title">
          <h2>已入库政策</h2><span>{{ documents.length }} 份</span>
        </div>
        <div v-if="!documents.length" class="empty">尚未导入政策文件</div>
        <div v-for="doc in documents" :key="doc.id" class="document-row">
          <div>
            <b>{{ doc.filename }}</b>
            <span>
              {{ doc.topic || "未分类" }}
              <template v-if="doc.effective_date"> · 施行日期 {{ doc.effective_date }}</template>
              · {{ doc.chunk_count }} 个检索分块
            </span>
          </div>
          <span :class="['badge', doc.status]">{{ statusLabel(doc.status) }}</span>
          <button class="text danger" @click="remove(doc.id)">删除</button>
        </div>
      </div>
    </div>
  </section>
</template>
