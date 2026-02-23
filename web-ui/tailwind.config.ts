import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                neuro: {
                    void: '#05070f',
                    bg: '#0a0e1a',
                    surface: '#141b2d',
                    border: '#1e293b',
                    primary: '#3b82f6',
                    success: '#10b981',
                    warning: '#f59e0b',
                    danger: '#ef4444',
                    text: {
                        primary: '#f1f5f9',
                        secondary: '#94a3b8',
                        muted: '#64748b',
                    },
                },
                severity: {
                    critical: '#dc2626',
                    high: '#f97316',
                    medium: '#eab308',
                    low: '#22c55e',
                    info: '#3b82f6',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float-slow': 'float 6s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-6px)' },
                },
            },
        },
    },
    plugins: [],
}

export default config
