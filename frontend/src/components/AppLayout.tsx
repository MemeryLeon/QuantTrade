import { NavLink, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">QuantTrade</p>
          <h1>回测工作台</h1>
        </div>
        <nav aria-label="主导航">
          <NavLink to="/" end>
            Mock 回测
          </NavLink>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
