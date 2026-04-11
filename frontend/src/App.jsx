import { useEffect, useState } from "react";
import { Routes, Route, Link } from "react-router-dom";
import client from "./api/client";

function DashboardPage() {
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        const response = await client.get("/tickets/");
        setTickets(response.data?.data ?? []);
        setTotal(response.data?.total ?? 0);
        setError("");
      } catch (fetchError) {
        const message =
          fetchError?.response?.data?.message ||
          fetchError?.message ||
          "Unable to load tickets.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, []);

  return (
    <div className="page">
      <h1>Support Dashboard</h1>
      <p>Showing latest tickets from backend.</p>

      {loading && <p>Loading tickets...</p>}

      {!loading && error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          <p className="ticket-count">Total tickets: {total}</p>
          {tickets.length === 0 ? (
            <p>No tickets found.</p>
          ) : (
            <div className="table-wrapper">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Summary</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Assignee</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((ticket) => (
                    <tr key={ticket.key}>
                      <td>{ticket.key || "-"}</td>
                      <td>{ticket.summary || "-"}</td>
                      <td>{ticket.status || "-"}</td>
                      <td>{ticket.priority || "-"}</td>
                      <td>{ticket.assignee || "Unassigned"}</td>
                      <td>
                        {ticket.updated
                          ? new Date(ticket.updated).toLocaleString()
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
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
