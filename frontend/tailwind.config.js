/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
  colors: {
    border: '#334155', // slate-700 (fits your dark navy theme)

    background: {
      DEFAULT: '#0F1729',
      secondary: '#1E293B',
      card: '#1E2A3B',
    },
    primary: {
      DEFAULT: '#06B6D4',
      hover: '#0891B2',
      light: '#22D3EE',
    },
    accent: {
      DEFAULT: '#F59E0B',
      hover: '#D97706',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#E2E8F0',
      muted: '#94A3B8',
    },
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
  },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(6, 182, 212, 0.1)',
        'glass-hover': '0 8px 32px 0 rgba(6, 182, 212, 0.2)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
