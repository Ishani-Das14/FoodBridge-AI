import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // Needed for Docker container mapping
    strictPort: true,
  },
  preview: {
    port: 80,
    host: true,
  }
});
