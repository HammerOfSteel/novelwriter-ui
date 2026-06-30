/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				// Base surfaces
				base: {
					950: '#0b0b14',
					900: '#10101c',
					800: '#16162a',
					700: '#1e1e35'
				},
				// Border
				border: '#252540',
				// Accent violet
				violet: {
					400: '#a78bfa',
					500: '#8b5cf6',
					600: '#7c3aed',
					700: '#6d28d9'
				},
				// Text
				ink: {
					50:  '#f0f0ff',
					100: '#e2e2f0',
					300: '#a0a0c0',
					500: '#6b6b8a',
					700: '#3d3d55'
				}
			},
			fontFamily: {
				sans: ['Inter', 'system-ui', 'sans-serif'],
				mono: ['JetBrains Mono', 'Fira Code', 'monospace']
			},
			animation: {
				'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				'fade-in': 'fadeIn 0.2s ease-out'
			},
			keyframes: {
				fadeIn: {
					'0%': { opacity: '0', transform: 'translateY(4px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' }
				}
			}
		}
	},
	plugins: []
};
