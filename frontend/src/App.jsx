import { Routes, Route, Link } from "react-router-dom";

function DashboardPage() {
  return (
    <div className="page">
      <h1>Support Dashboard</h1>
      <p>Dashboard UI will be built here.</p>
    </div>
  );
}

function AssigneeMatrixPage() {
  return (
    <div className="page">
      <h1>Assignee Matrix</h1>
      <p>Assignee-wise workload matrix will be built here.</p>
    </div>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>Daily Scrum</h2>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/assignee-matrix">Assignee Matrix</Link>
        </nav>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/assignee-matrix" element={<AssigneeMatrixPage />} />
        </Routes>
      </main>
    </div>
  );
}
