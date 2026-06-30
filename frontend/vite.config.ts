import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			// Proxy /api/* to the FastAPI backend during development
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
