/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0f1115",
                surface: "#181b21",
                primary: "#3b82f6",
                secondary: "#64748b",
                accent: "#10b981",
                danger: "#ef4444",
                warning: "#f59e0b",
                text: "#e2e8f0",
                "text-muted": "#94a3b8",
                border: "#2d3748",
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
