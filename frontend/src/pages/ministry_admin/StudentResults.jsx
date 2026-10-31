import { useCallback, useEffect, useState } from "react";
import api from "../../api/client";

const PAGE_SIZE = 10;

/** Module 1: "accepts exam score data from authorized administrative
 * uploads". Lists registered students and lets the Ministry Administrator
 * upload or correct a student's exam score. */
export default function StudentResults({ onChanged }) {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(undefined);
  const [scores, setScores] = useState({});
  const [busyId, setBusyId] = useState(null);
  const [message, setMessage] = useState(null);

  const load = useCallback(() => {
    const params = new URLSearchParams({ page, page_size: PAGE_SIZE });
    if (search) params.set("search", search);
    api.get(`students/?${params}`).then((res) => setData(res.data));
  }, [page, search]);

  useEffect(() => {
    load();
  }, [load]);

  async function upload(student) {
    const value = scores[student.id];
    if (value === undefined || value === "") return;
    setBusyId(student.id);
    setMessage(null);
    try {
      await api.post(`students/${student.id}/upload_results/`, { exam_score: Number(value) });
      setMessage({ type: "success", text: `Score for ${student.full_name} saved.` });
      setScores((m) => ({ ...m, [student.id]: "" }));
      load();
      onChanged?.();
    } catch (err) {
      const detail = err?.response?.data?.exam_score?.[0] || "Could not save score.";
      setMessage({ type: "error", text: detail });
    } finally {
      setBusyId(null);
    }
  }

  const rows = data?.results ?? [];
  const total = data?.count ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setSearch(query.trim());
        }}
      >
        <input
          placeholder="Search by name, username or county"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {data === undefined ? (
        <p className="muted">Loading students...</p>
      ) : rows.length === 0 ? (
        <p className="muted">No students match your search.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Name</th>
                <th>County</th>
                <th>Exam score</th>
                <th>Placed school</th>
                <th>Upload / correct score</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td className="mono">{s.username}</td>
                  <td>{s.full_name}</td>
                  <td>{s.county}</td>
                  <td>
                    {s.has_results ? (
                      <strong>{Number(s.exam_score).toFixed(1)}</strong>
                    ) : (
                      <span className="badge badge-pending">awaiting results</span>
                    )}
                  </td>
                  <td>{s.placed_school || <span className="muted">Not placed</span>}</td>
                  <td>
                    <div className="inline-upload">
                      <input
                        type="number"
                        min="0"
                        max="500"
                        step="0.1"
                        placeholder="0–500"
                        value={scores[s.id] ?? ""}
                        onChange={(e) => setScores((m) => ({ ...m, [s.id]: e.target.value }))}
                      />
                      <button
                        className="btn-secondary"
                        disabled={busyId === s.id || !scores[s.id]}
                        onClick={() => upload(s)}
                      >
                        Save
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="pager">
        <span className="muted">
          {total} student{total === 1 ? "" : "s"} · page {page} of {pages}
        </span>
        <div>
          <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <button className="btn-secondary" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
