import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import viteImagemin from 'vite-plugin-imagemin'

// https://vitejs.dev/config/
export default defineConfig({
    server: {
        headers: {
            'Cache-Control': 'no-store, no-cache, must-revalidate',
        },
        port: 5173,
        host: true,
        hmr: {
            protocol: 'ws',
            host: 'localhost',
            overlay: false,
        },
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    },
    plugins: [
        react(),
        tailwindcss(),
        viteImagemin({
            gifsicle: { optimizationLevel: 7, interlaced: false },
            optipng: { optimizationLevel: 7 },
            mozjpeg: { quality: 20 },
            pngquant: { quality: [0.8, 0.9], speed: 4 },
            svgo: {
                plugins: [{ name: 'removeViewBox' }, { name: 'removeEmptyAttrs', active: false }]
            }
        })
    ],
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ['react', 'react-dom'],
                    charts: ['recharts'],
                    forms: ['react-hook-form', 'zod']
                }
            }
        }
    },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./src/test/setup.js'],
    },
})
