import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function RegisterPage() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "", email: "", password: "", first_name: "", last_name: "", role: "student",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(form);
      await login(form.username, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      const data = err?.response?.data;
      const message = data ? Object.values(data).flat().join(" ") : "Registration failed.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create an account</h1>
        <p className="subtitle">Register as a student, parent, or administrator</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label>
            I am a
            <select value={form.role} onChange={update("role")}>
              <option value="student">Student</option>
              <option value="parent">Parent/Guardian</option>
              <option value="school_admin">School Administrator</option>
              <option value="ministry_admin">Ministry Administrator</option>
            </select>
          </label>
          <label>
            First name
            <input value={form.first_name} onChange={update("first_name")} />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={update("last_name")} />
          </label>
          <label>
            Username
            <input value={form.username} onChange={update("username")} required />
          </label>
          <label>
            Email
            <input type="email" value={form.email} onChange={update("email")} required />
          </label>
          <label>
            Password
            <input type="password" value={form.password} onChange={update("password")} required minLength={8} />
          </label>
          <button type="submit" disabled={submitting}>
            {submitting ? "Creating account..." : "Create account"}
          </button>
        </form>
        <div className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
