import { useEffect, useState } from "react";
import { NavLink, Routes, Route } from "react-router-dom";
import client from "./api/client";

function DashboardPage() {
  const [tickets, setTickets] = useState([]);
  const [notes, setNotes] = useState({});
  const [savingNotes, setSavingNotes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [hidePcmc, setHidePcmc] = useState(false);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        const response = await client.get("/tickets/");
        const loadedTickets = response.data?.data ?? [];
        setTickets(loadedTickets);
        setNotes(
          loadedTickets.reduce((ticketNotes, ticket) => {
            ticketNotes[ticket.key] = ticket.scrum_note || "";
            return ticketNotes;
          }, {})
        );
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

  const saveNote = async (ticketKey) => {
    setSavingNotes((current) => ({ ...current, [ticketKey]: true }));
    try {
      await client.put(`/tickets/${ticketKey}/note`, {
        note: notes[ticketKey] || "",
      });
    } catch (saveError) {
      const message =
        saveError?.response?.data?.message ||
        saveError?.message ||
        "Unable to save note.";
      setError(message);
    } finally {
      setSavingNotes((current) => ({ ...current, [ticketKey]: false }));
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Daily Scrum</p>
          <h1>Support Dashboard</h1>
        </div>
        <p className="last-updated">Jira support queue</p>
      </div>

      {loading && <p>Loading tickets...</p>}

      {!loading && error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          <div className="toolbar">
            <div>
              <p className="ticket-count">{filteredTickets.length}</p>
              <p className="ticket-count-label">Tickets in view</p>
            </div>
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
                    <th>Scrum Note</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTickets.map((ticket) => (
                    <tr key={ticket.key}>
                      <td>
                        {ticket.browse_url ? (
                          <a
                            href={ticket.browse_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {ticket.key}
                          </a>
                        ) : (
                          ticket.key || "-"
                        )}
                      </td>
                      <td>{ticket.summary || "-"}</td>
                      <td>
                        <span className="status-pill">{ticket.status || "-"}</span>
                      </td>
                      <td>{ticket.client_name || "-"}</td>
                      <td>{ticket.priority || "-"}</td>
                      <td>{ticket.l0_assignee || "Unassigned"}</td>
                      <td>
                        <div className="note-editor">
                          <textarea
                            value={notes[ticket.key] || ""}
                            onChange={(event) =>
                              setNotes((current) => ({
                                ...current,
                                [ticket.key]: event.target.value,
                              }))
                            }
                            placeholder="Add scrum note"
                          />
                          <button
                            type="button"
                            onClick={() => saveNote(ticket.key)}
                            disabled={savingNotes[ticket.key]}
                          >
                            {savingNotes[ticket.key] ? "Saving..." : "Save"}
                          </button>
                        </div>
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
      <div className="page-header">
        <div>
          <p className="eyebrow">Daily Scrum</p>
          <h1>Assignee Matrix</h1>
        </div>
      </div>
      <p>Assignee-wise workload matrix will be built here.</p>
    </div>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">DS</span>
          <span>Daily Scrum</span>
        </div>
        <nav>
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/assignee-matrix">Assignee Matrix</NavLink>
        </nav>
      </header>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/assignee-matrix" element={<AssigneeMatrixPage />} />
        </Routes>
      </main>
    </div>
  );
}
