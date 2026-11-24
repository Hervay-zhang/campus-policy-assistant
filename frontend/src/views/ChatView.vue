<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { api, streamChat, type Citation } from "../api";

type Message = {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  refused?: boolean;
};

type ConversationSummary = {
  id: string;
  title: string;
  updated_at: string;
};

const WELCOME_MESSAGE: Message = {
  role: "assistant",
  content:
    "你好，我是校园百事通。学籍注册、转专业、补考重修、奖学金、毕业与学位这些事都可以问我，我只依据已入库的教务政策条款作答，并标注出处。",
};

// 新生最常问的几件事，点一下就能直接问
const SUGGESTIONS = [
  "大二学生可以申请转专业吗？需要哪些材料？",
  "必修课补考和重修有什么区别？",
  "国家奖学金和国家励志奖学金可以同时获得吗？",
  "毕业论文的文字复制比要求是多少？",
];

const question = ref("");
const loading = ref(false);
const loadingHistory = ref(true);
const stage = ref("");
const conversationId = ref<string>();
const conversations = ref<ConversationSummary[]>([]);
const messages = ref<Message[]>([{ ...WELCOME_MESSAGE }]);
const messagesElement = ref<HTMLElement>();

async function scrollToBottom() {
  await nextTick();
  messagesElement.value?.scrollTo({
    top: messagesElement.value.scrollHeight,
    behavior: "smooth",
  });
}

async function loadConversations() {
  conversations.value = (await api.get("/chat/conversations")).data;
}

async function openConversation(id: string) {
  if (loading.value) return;
  loadingHistory.value = true;
  try {
    const { data } = await api.get(`/chat/conversations/${id}`);
    conversationId.value = data.id;
    localStorage.setItem("campus-rag-conversation-id", data.id);
    messages.value = data.messages;
    await scrollToBottom();
  } finally {
    loadingHistory.value = false;
  }
}

function newConversation() {
  if (loading.value) return;
  conversationId.value = undefined;
  localStorage.removeItem("campus-rag-conversation-id");
  messages.value = [{ ...WELCOME_MESSAGE }];
}

async function removeConversation(id: string) {
  if (loading.value) return;
  await api.delete(`/chat/conversations/${id}`);
  if (conversationId.value === id) newConversation();
  await loadConversations();
}

async function send() {
  const text = question.value.trim();
  if (!text || loading.value) return;
  messages.value.push({ role: "user", content: text });
  const reply: Message = { role: "assistant", content: "" };
  messages.value.push(reply);
  question.value = "";
  loading.value = true;
  await scrollToBottom();
  try {
    await streamChat(
      {
        question: text,
        conversation_id: conversationId.value,
        filters: {},
      },
      (name, data) => {
        if (name === "status") stage.value = data.message;
        if (name === "token") reply.content += data.content;
        if (name === "done") {
          reply.id = data.message_id;
          reply.citations = data.citations;
          reply.refused = data.refused;
          conversationId.value = data.conversation_id;
          localStorage.setItem("campus-rag-conversation-id", data.conversation_id);
          stage.value = "";
          void loadConversations();
        }
        if (name === "error") throw new Error(data.message);
      },
    );
  } catch (error: any) {
    reply.content = `请求失败：${error.message}`;
  } finally {
    loading.value = false;
    await scrollToBottom();
  }
}

function askSuggestion(text: string) {
  if (loading.value) return;
  question.value = text;
  void send();
}

function formatUtcTime(timeStr: string) {
  if (!timeStr) return ""
  // 后端是UTC时间字符串，手动补上Z，强制JS解析为UTC时间
  const d = new Date(timeStr + "Z")
  return d.toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  })
}

onMounted(async () => {
  try {
    await loadConversations();
    const savedId = localStorage.getItem("campus-rag-conversation-id");
    const target = conversations.value.find((item) => item.id === savedId)
      ?? conversations.value[0];
    if (target) await openConversation(target.id);
  } finally {
    loadingHistory.value = false;
  }
});
</script>

<template>
  <section class="page chat-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">ACADEMIC POLICY ASSISTANT</p>
        <h1>教务政策问答</h1>
        <p>混合检索 + 重排序 + 引用校验，每条回答都能回到具体条款。</p>
      </div>
      <span class="status"><i></i> 教务政策库已接入</span>
    </header>

    <div class="chat-layout">
      <aside class="conversation-panel">
        <button class="new-chat" :disabled="loading" @click="newConversation">
          新建会话
        </button>
        <div v-if="!conversations.length" class="conversation-empty">暂无历史会话</div>
        <div
          v-for="item in conversations"
          :key="item.id"
          :class="['conversation-item', { active: item.id === conversationId }]"
        >
          <button class="conversation-open" @click="openConversation(item.id)">
            <b>{{ item.title }}</b>
            <span>{{ formatUtcTime(item.updated_at) }}</span>
          </button>
          <button class="conversation-delete" title="删除会话" @click="removeConversation(item.id)">
            ×
          </button>
        </div>
      </aside>
      <div class="chat-panel">
      <div ref="messagesElement" class="messages">
        <div v-if="loadingHistory" class="history-loading">正在恢复历史会话…</div>
        <article
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.role, { refused: message.refused }]"
        >
          <b>{{ message.role === "user" ? "学生" : "教务助手" }}</b>
          <p>{{ message.content || "正在组织有依据的回答…" }}</p>
          <details v-if="message.citations?.length" class="citations">
            <summary>查看 {{ message.citations.length }} 条条款依据</summary>
            <div v-for="item in message.citations" :key="item.chunk_id" class="citation">
              <b>[{{ item.label }}] {{ item.filename }}</b>
              <span>{{ item.section }} {{ item.page ? `第 ${item.page} 页` : "" }}</span>
              <p>{{ item.quote }}</p>
            </div>
          </details>
        </article>
        <div v-if="messages.length === 1" class="suggestions">
          <span>常见问题</span>
          <button
            v-for="item in SUGGESTIONS"
            :key="item"
            class="chip"
            :disabled="loading"
            @click="askSuggestion(item)"
          >{{ item }}</button>
        </div>
      </div>
      <form class="composer" @submit.prevent="send">
        <span v-if="stage" class="stage">{{ stage }}</span>
        <textarea
          v-model="question"
          placeholder="例如：大二学生可以申请转专业吗？需要提交哪些材料？"
          @keydown.ctrl.enter="send"
        />
        <button :disabled="loading">{{ loading ? "检索中" : "发送问题" }}</button>
      </form>
      </div>
    </div>
  </section>
</template>
