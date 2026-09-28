import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        popup: resolve(root, 'popup.html'),
        app: resolve(root, 'app.html'),
        background: resolve(root, 'src/background.ts'),
      },
      output: { entryFileNames: '[name].js' },
    },
  },
});
