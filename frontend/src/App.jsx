import { Fragment, useEffect, useState } from "react";
import { NavLink, Routes, Route } from "react-router-dom";
import client from "./api/client";

function DashboardPage() {
  const ticketCategories = [
    { id: "active", label: "Active" },
    { id: "resolved", label: "Resolved" },
    { id: "roadmap", label: "Roadmap" },
  ];
  const [tickets, setTickets] = useState([]);
  const [notes, setNotes] = useState({});
  const [savingNotes, setSavingNotes] = useState({});
  const [commentsByTicket, setCommentsByTicket] = useState({});
  const [commentsLoading, setCommentsLoading] = useState({});
  const [expandedTicket, setExpandedTicket] = useState("");
  const [activeCategory, setActiveCategory] = useState("active");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [hidePcmc, setHidePcmc] = useState(false);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        const response = await client.get("/tickets/", {
          params: { category: activeCategory },
        });
        const loadedTickets = response.data?.data ?? [];
        setTickets(loadedTickets);
        setNotes(
          loadedTickets.reduce((ticketNotes, ticket) => {
            ticketNotes[ticket.key] = ticket.scrum_note || "";
            return ticketNotes;
          }, {})
        );
        setExpandedTicket("");
        setCommentsByTicket({});
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
  }, [activeCategory]);

  const visibleByPcmc = hidePcmc
    ? tickets.filter((ticket) => !ticket.is_pcmc_ticket && !ticket.pcmc_inclusion_date)
    : tickets;
  const normalizedSearchQuery = searchQuery.trim().toLowerCase();
  const filteredTickets = normalizedSearchQuery
    ? visibleByPcmc.filter((ticket) =>
        [
          ticket.key,
          ticket.summary,
          ticket.status,
          ticket.client_name,
          ticket.priority,
          ticket.l0_assignee,
          notes[ticket.key],
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearchQuery)
      )
    : visibleByPcmc;

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

  const loadComments = async (ticketKey) => {
    if (commentsByTicket[ticketKey]) {
      return;
    }
    setCommentsLoading((current) => ({ ...current, [ticketKey]: true }));
    try {
      const response = await client.get(`/tickets/${ticketKey}/comments`);
      setCommentsByTicket((current) => ({
        ...current,
        [ticketKey]: response.data?.data ?? [],
      }));
    } catch (commentError) {
      const message =
        commentError?.response?.data?.message ||
        commentError?.message ||
        "Unable to load comments.";
      setError(message);
    } finally {
      setCommentsLoading((current) => ({ ...current, [ticketKey]: false }));
    }
  };

  const toggleComments = async (ticketKey) => {
    const nextExpandedTicket = expandedTicket === ticketKey ? "" : ticketKey;
    setExpandedTicket(nextExpandedTicket);
    if (nextExpandedTicket) {
      await loadComments(ticketKey);
    }
  };

  const commentsByDate = (comments) =>
    comments.reduce((groups, comment) => {
      const dateKey = comment.created
        ? new Intl.DateTimeFormat("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          }).format(new Date(comment.created))
        : "No date";
      groups[dateKey] = [...(groups[dateKey] || []), comment];
      return groups;
    }, {});

  const formatCommentTime = (created) =>
    created
      ? new Intl.DateTimeFormat("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
        }).format(new Date(created))
      : "";

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
          <div className="tabs" aria-label="Ticket categories">
            {ticketCategories.map((category) => (
              <button
                key={category.id}
                type="button"
                className={activeCategory === category.id ? "active" : ""}
                onClick={() => setActiveCategory(category.id)}
              >
                {category.label}
              </button>
            ))}
          </div>
          <div className="toolbar">
            <div>
              <p className="ticket-count">{filteredTickets.length}</p>
              <p className="ticket-count-label">Tickets in view</p>
            </div>
            <div className="toolbar-actions">
              <label className="search-field">
                <span>Search tickets</span>
                <input
                  type="search"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Key, client, assignee, status"
                />
              </label>
              <label className="filter-toggle">
                <input
                  type="checkbox"
                  checked={hidePcmc}
                  onChange={(event) => setHidePcmc(event.target.checked)}
                />
                Filter out PCMC tickets
              </label>
            </div>
          </div>
          {filteredTickets.length === 0 ? (
            <p>No tickets found.</p>
          ) : (
            <div className="table-wrapper">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Comments</th>
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
                    <Fragment key={ticket.key}>
                      <tr>
                        <td>
                          <button
                            type="button"
                            className="comments-toggle"
                            onClick={() => toggleComments(ticket.key)}
                            aria-expanded={expandedTicket === ticket.key}
                          >
                            {expandedTicket === ticket.key ? "Hide" : "Show"}
                          </button>
                        </td>
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
                      {expandedTicket === ticket.key && (
                        <tr className="comments-row">
                          <td colSpan="8">
                            {commentsLoading[ticket.key] && (
                              <p className="comments-empty">Loading comments...</p>
                            )}
                            {!commentsLoading[ticket.key] &&
                              (commentsByTicket[ticket.key]?.length ? (
                                <div className="comments-panel">
                                  {Object.entries(
                                    commentsByDate(commentsByTicket[ticket.key])
                                  ).map(([date, comments]) => (
                                    <section className="comment-date-group" key={date}>
                                      <h3>{date}</h3>
                                      {comments.map((comment) => (
                                        <article
                                          className="comment-item"
                                          key={comment.id}
                                        >
                                          <p className="comment-meta">
                                            {formatCommentTime(comment.created)}
                                            {comment.author
                                              ? ` | ${comment.author}`
                                              : ""}
                                          </p>
                                          <p>{comment.body || "-"}</p>
                                        </article>
                                      ))}
                                    </section>
                                  ))}
                                </div>
                              ) : (
                                <p className="comments-empty">No comments found.</p>
                              ))}
                          </td>
                        </tr>
                      )}
                    </Fragment>
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
