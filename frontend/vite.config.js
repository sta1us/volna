import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    base:'/',
    server: {
      allowedHosts: true,
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      cors: true,
      hmr: {
        protocol: 'wss',
        host: env.VITE_DOMAIN || 'localhost',
        clientPort: 443
      }
    },
    plugins: [react(), tailwindcss()]
  };
});
