import {
  AlertTriangle, CheckCircle2, ClipboardList, Gauge, LayoutDashboard, ShieldAlert, Target, TrendingUp, Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from "recharts";
import { getDashboardStats } from "../api/dashboardApi";
import { Alert, Button, Card, EmptyState, PageHeader, RiskBadge, SkeletonStatRow, Stat } from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";

const RISK_COLORS = { LOW: "#0c9d45", MEDIUM: "#f59e0b", HIGH: "#e11d48" };

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardStats().then(setStats).catch((err) => setError(extractErrorMessage(err)));
  }, []);

  return (
    <div className="dashboard-page">
      <PageHeader
        icon={LayoutDashboard}
        title="Dashboard"
        description="Monitor running athletes, assessments, injury-risk predictions and model insights."
      />

      {error && <Alert tone="error" title="We couldn't load the dashboard.">Please try again. If the problem continues, check the backend service.</Alert>}

      {!stats && !error && <SkeletonStatRow count={7} />}

      {stats && (
        <>
          <div className="card-grid dashboard-stat-grid">
            <Stat label="Total Athletes" value={stats.total_athletes} icon={Users} />
            <Stat label="Total Assessments" value={stats.total_assessments} icon={ClipboardList} />
            <Stat label="Total Predictions" value={stats.total_predictions} icon={Gauge} />
            <Stat label="High Risk" value={stats.high_risk} icon={AlertTriangle} tone="high" />
            <Stat label="Medium Risk" value={stats.medium_risk} icon={ShieldAlert} tone="medium" />
            <Stat label="Low Risk" value={stats.low_risk} icon={CheckCircle2} tone="low" />
            <Stat
              label="Average Predicted Risk"
              value={stats.average_predicted_risk != null ? stats.average_predicted_risk.toFixed(2) : "N/A"}
              icon={TrendingUp}
            />
          </div>

          <div className="chart-grid dashboard-chart-grid">
            <Card title="Risk Distribution">
              {stats.total_predictions === 0 ? (
                <EmptyState icon={Gauge} title="No predictions yet" description="Risk distribution will appear here once predictions are generated." />
              ) : (
                <ResponsiveContainer width="100%" height={360}>
                  <PieChart>
                    <Pie data={[
                      { name: "LOW", value: stats.low_risk },
                      { name: "MEDIUM", value: stats.medium_risk },
                      { name: "HIGH", value: stats.high_risk },
                    ]} dataKey="value" nameKey="name" outerRadius={130} label>
                      {["LOW", "MEDIUM", "HIGH"].map((name) => (
                        <Cell key={name} fill={RISK_COLORS[name]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>

            <Card title="Prediction Trend" description="Most recent 10 predictions, oldest to newest.">
              {stats.recent_predictions.length === 0 ? (
                <EmptyState icon={TrendingUp} title="No prediction activity yet" description="Once predictions are generated, the probability trend will appear here." />
              ) : (
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={[...stats.recent_predictions].reverse().map((p, i) => ({ name: `#${i + 1}`, probability: p.probability }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eceef1" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip />
                    <Bar dataKey="probability" fill="#0c9d45" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          <Card title="Recent Predictions">
            {stats.recent_predictions.length === 0 ? (
              <EmptyState
                icon={Target}
                title="No predictions yet"
                description="Generate a prediction from an athlete assessment to see risk results here."
                action={<Button to="/prediction" icon={Target}>Generate Prediction</Button>}
              />
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr><th>Athlete</th><th>Date</th><th>Probability</th><th>Risk Level</th></tr>
                  </thead>
                  <tbody>
                    {stats.recent_predictions.map((p) => (
                      <tr key={p.prediction_id}>
                        <td>{p.athlete_id}</td>
                        <td>{new Date(p.prediction_date).toLocaleString()}</td>
                        <td>{p.probability.toFixed(2)}</td>
                        <td><RiskBadge level={p.risk_level} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
