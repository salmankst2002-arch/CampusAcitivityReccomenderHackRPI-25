// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  // Add the daisyUI plugin
  plugins: [require("daisyui")],
  // Configure the theme for a retro look
  daisyui: {
    themes: ["retro"], // Use the built-in 'retro' theme
  },
};
