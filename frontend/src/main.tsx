import React from "react";
import ReactDOM from "react-dom/client";
import "./styles.css";

function App() {
  return (
    <main className="app-shell">
      <section className="status-panel" aria-labelledby="status-title">
        <p className="eyebrow">QuantTrade</p>
        <h1 id="status-title">开发基线已就绪</h1>
        <p>前端构建冒烟用于确认 React、TypeScript 和 Vite 工具链可用。</p>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
