/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#1F4E78',
          light: '#2f6aa3',
          dark: '#14324d',
        },
      },
    },
  },
  plugins: [],
}
