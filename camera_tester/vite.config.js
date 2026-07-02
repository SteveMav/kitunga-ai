import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const djangoTarget = env.VITE_DJANGO_TARGET || "http://127.0.0.1:8000";

  return {
    server: {
      host: "127.0.0.1",
      port: 5174,
      proxy: {
        "/api": {
          target: djangoTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
