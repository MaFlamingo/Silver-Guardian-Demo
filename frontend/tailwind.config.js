/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // 适老化：大字体、高对比度配色
      fontSize: {
        "elder-sm": ["1.25rem", { lineHeight: "1.8rem" }],   // 20px 最小
        "elder-base": ["1.5rem", { lineHeight: "2.2rem" }],  // 24px 正文
        "elder-lg": ["2rem", { lineHeight: "2.8rem" }],      // 32px 标题
        "elder-xl": ["2.5rem", { lineHeight: "3.2rem" }],    // 40px 大标题
      },
      colors: {
        elder: {
          primary: "#1565C0",    // 深蓝 — 主色
          secondary: "#2E7D32",  // 深绿 — 确认
          danger: "#C62828",     // 深红 — 紧急
          warning: "#E65100",    // 深橙 — 警告
          bg: "#FFF8E1",         // 暖黄背景
          card: "#FFFFFF",
          text: "#212121",       // 深色文字
          muted: "#616161",      // 辅助文字
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
