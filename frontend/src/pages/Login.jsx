import { CheckCircle2, KeyRound, Sparkles, UserPlus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { forgotPassword, register as registerApi } from "../api/authApi";
import BrandMark from "../components/common/BrandMark";
import { extractErrorMessage } from "../components/common/ErrorMessage";
import { Alert, Button } from "../components/ui";
import { useAuth } from "../context/AuthContext";

const MODE_META = {
  login: { title: "Welcome back", subtitle: "Sign in to continue to your dashboard.", cta: "Login" },
  register: { title: "Create your account", subtitle: "Register as a researcher to get started.", cta: "Register" },
  forgot: { title: "Reset your password", subtitle: "Enter your username and we'll generate a reset link.", cta: "Send Reset Link" },
};

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "register" | "forgot"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [info, setInfo] = useState(null); // { message, devLink }
  const [justRegistered, setJustRegistered] = useState(false);

  function switchMode(next) {
    setMode(next);
    setError("");
    setInfo(null);
    setJustRegistered(false);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo(null);
    setBusy(true);
    try {
      if (mode === "forgot") {
        const res = await forgotPassword(username);
        setInfo({ message: res.message, devLink: res.dev_link });
        return;
      }
      if (mode === "register") {
        await registerApi(username, password);
        setJustRegistered(true);
        setPassword("");
        return;
      }
      await login(username, password);
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const meta = MODE_META[mode];

  return (
    <div className="auth-page">
      <div className="auth-brand-panel">
        <span className="blob" style={{ width: 260, height: 260, top: -80, right: -60 }} />
        <span className="blob" style={{ width: 180, height: 180, bottom: 40, left: -60 }} />
        <div className="auth-brand-content">
          <BrandMark className="auth-brand-mark" />
          <h1>Know the risk before it becomes an injury.</h1>
          <p>
            Explainable Multimodal AI-Based Athlete Injury Risk Prediction — powered by
            XGBoost, explained with SHAP.
          </p>
        </div>
      </div>

      <div className="auth-form-panel">
        {justRegistered ? (
          <div className="auth-card">
            <div className="auth-card-icon auth-card-icon-success"><CheckCircle2 size={20} strokeWidth={2.2} /></div>
            <h2>Registration successful</h2>
            <p className="auth-subtitle">
              Your account <b>{username}</b> has been created. Log in with your new username and password to continue.
            </p>
            <Button size="lg" className="btn-block" onClick={() => switchMode("login")}>
              Go to Login
            </Button>
          </div>
        ) : (
          <form className="auth-card" onSubmit={handleSubmit}>
            <div className="auth-card-icon">
              {mode === "login" && <Sparkles size={20} strokeWidth={2.2} />}
              {mode === "register" && <UserPlus size={20} strokeWidth={2.2} />}
              {mode === "forgot" && <KeyRound size={20} strokeWidth={2.2} />}
            </div>
            <h2>{meta.title}</h2>
            <p className="auth-subtitle">{meta.subtitle}</p>

            <div className="auth-field">
              <label>Username</label>
              <input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
            </div>

            {mode !== "forgot" && (
              <div className="auth-field">
                <label>Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
              </div>
            )}

            {error && <Alert tone="error">{error}</Alert>}
            {info && (
              <Alert tone="info">
                {info.message}
                {info.devLink && (
                  <>
                    <br /><br />
                    <b>No mail/SMS provider is configured for this project</b> — here is the
                    simulated reset link (also logged to <code>backend/logs/app.log</code>):
                    <br />
                    <a href={info.devLink}>{info.devLink}</a>
                  </>
                )}
              </Alert>
            )}

            <Button type="submit" size="lg" className="btn-block" loading={busy}>{meta.cta}</Button>

            <div className="auth-links">
              {mode === "login" && (
                <>
                  <button type="button" className="btn btn-link" onClick={() => switchMode("register")}>
                    New researcher? Create an account
                  </button>
                  <button type="button" className="btn btn-link" onClick={() => switchMode("forgot")}>
                    Forgot password?
                  </button>
                </>
              )}
              {mode !== "login" && (
                <button type="button" className="btn btn-link" onClick={() => switchMode("login")}>
                  Back to login
                </button>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
