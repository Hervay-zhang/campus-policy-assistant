import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    // host: true 监听 0.0.0.0，内网穿透的隧道才能连进来
    host: true,
    port: 5173,
    strictPort: true,
    // 允许通过穿透域名（cpolar / trycloudflare / 自定义域名）访问；
    // 不加这一行，Vite 会返回 "Blocked request. This host is not allowed."
    allowedHosts: true,
    proxy: {
      // 8000/8001 已被本机其他项目占用（资产易管理、Text2SQL2BI），本后端使用 8002
      "/api": "http://127.0.0.1:8002",
    },
  },
});

