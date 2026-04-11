import { useEffect, useState } from "react";
import { Routes, Route, Link } from "react-router-dom";
import client from "./api/client";

function DashboardPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [hidePcmc, setHidePcmc] = useState(false);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        const response = await client.get("/tickets/");
        setTickets(response.data?.data ?? []);
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

  const filteredTickets = hidePcmc
    ? tickets.filter((ticket) => !ticket.is_pcmc_ticket && !ticket.pcmc_inclusion_date)
    : tickets;

  return (
    <div className="page">
      <h1>Support Dashboard</h1>
  

      {loading && <p>Loading tickets...</p>}

      {!loading && error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          <div className="toolbar">
            <p className="ticket-count">Total tickets: {filteredTickets.length}</p>
            <label className="filter-toggle">
              <input
                type="checkbox"
                checked={hidePcmc}
                onChange={(event) => setHidePcmc(event.target.checked)}
              />
              Filter out PCMC tickets
            </label>
          </div>
          {filteredTickets.length === 0 ? (
            <p>No tickets found.</p>
          ) : (
            <div className="table-wrapper">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Summary</th>
                    <th>Status</th>
                    <th>Client Name</th>
                    <th>Priority</th>
                    <th>L0 Assignee</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTickets.map((ticket) => (
                    <tr key={ticket.key}>
                      <td>{ticket.key || "-"}</td>
                      <td>{ticket.summary || "-"}</td>
                      <td>{ticket.status || "-"}</td>
                      <td>{ticket.client_name || "-"}</td>
                      <td>{ticket.priority || "-"}</td>
                      <td>{ticket.l0_assignee || "Unassigned"}</td>
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
