// tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
  // This content array is still important. It tells Tailwind which files
  // to scan for classes, ensuring nothing gets purged in production builds.
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  // We only need to define the plugins array.
  // Tailwind v4 will handle the rest.
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
