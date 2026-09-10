import { KeyRound } from "lucide-react";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { resetPassword } from "../api/authApi";
import BrandMark from "../components/common/BrandMark";
import { extractErrorMessage } from "../components/common/ErrorMessage";
import { Alert, Button } from "../components/ui";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-form-panel" style={{ flex: "none", width: "100%" }}>
        <form className="auth-card" onSubmit={handleSubmit}>
          <BrandMark className="auth-brand-mark auth-brand-mark-centered" />
          <div className="auth-card-icon"><KeyRound size={20} strokeWidth={2.2} /></div>
          <h2>Set a new password</h2>
          <p className="auth-subtitle">Choose a new password for your account.</p>

          {!token && <Alert tone="error">This link is missing a reset token. Request a new one from the login page.</Alert>}

          {done ? (
            <>
              <Alert tone="success">Your password has been reset. You can log in now.</Alert>
              <Button size="lg" className="btn-block" onClick={() => navigate("/login")}>
                Go to Login
              </Button>
            </>
          ) : (
            <>
              <div className="auth-field">
                <label>New Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} autoFocus />
              </div>

              {error && <Alert tone="error">{error}</Alert>}

              <Button type="submit" size="lg" className="btn-block" disabled={!token} loading={busy}>
                Reset Password
              </Button>

              <div className="auth-links">
                <button type="button" className="btn btn-link" onClick={() => navigate("/login")}>Back to login</button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
