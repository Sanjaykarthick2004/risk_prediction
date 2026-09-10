import { FileText, History, Search, Sparkles, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listAthletes } from "../api/athleteApi";
import { listPredictions } from "../api/predictionApi";
import {
  Alert, Button, EmptyState, PageHeader, Pagination, paginate, RiskBadge, SkeletonTable,
} from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";

const PAGE_SIZE = 10;
const RISK_FILTERS = ["ALL", "LOW", "MEDIUM", "HIGH"];

export default function PredictionHistory() {
  const [predictions, setPredictions] = useState(null);
  const [athleteMap, setAthleteMap] = useState({});
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [page, setPage] = useState(1);

  useEffect(() => {
    Promise.all([listPredictions(), listAthletes()])
      .then(([preds, athletes]) => {
        setPredictions(preds);
        setAthleteMap(Object.fromEntries(athletes.map((a) => [a.athlete_id, a])));
      })
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  const filtered = useMemo(() => {
    if (!predictions) return [];
    const q = search.trim().toLowerCase();
    return predictions.filter((p) => {
      const athlete = athleteMap[p.athlete_id];
      const matchesSearch = !q || p.athlete_id.toLowerCase().includes(q) || athlete?.name?.toLowerCase().includes(q);
      const matchesRisk = riskFilter === "ALL" || p.risk_level === riskFilter;
      return matchesSearch && matchesRisk;
    });
  }, [predictions, athleteMap, search, riskFilter]);

  const pageItems = useMemo(() => paginate(filtered, page, PAGE_SIZE), [filtered, page]);

  if (error) return <Alert tone="error" title="We couldn't load prediction history.">{error}</Alert>;

  return (
    <div>
      <PageHeader icon={History} title="Prediction History" description="Every injury-risk prediction generated, with links into SHAP explanations and reports." />

      <div className="card">
        {!predictions && <SkeletonTable rows={6} cols={6} />}

        {predictions && predictions.length === 0 && (
          <EmptyState
            icon={Target}
            title="No predictions yet"
            description="Generate a prediction from an athlete assessment to see risk results here."
            action={<Button to="/prediction" icon={Target}>Generate Prediction</Button>}
          />
        )}

        {predictions && predictions.length > 0 && (
          <>
            <div className="history-filters">
              <div className="search-wrap" style={{ marginBottom: 0, flex: 1 }}>
                <Search size={16} className="search-icon" />
                <input
                  className="search-input" placeholder="Search by athlete name or ID..." aria-label="Search predictions"
                  value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                />
              </div>
              <select aria-label="Filter by risk level" value={riskFilter} onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}>
                {RISK_FILTERS.map((r) => <option key={r} value={r}>{r === "ALL" ? "All Risk Levels" : `${r} Risk`}</option>)}
              </select>
            </div>

            {filtered.length === 0 ? (
              <EmptyState icon={Search} title="No matching predictions" description="Try a different search term or risk filter." />
            ) : (
              <>
                <div className="table-scroll">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th><th>Athlete</th><th>Event</th><th>Risk</th><th>Probability</th>
                        <th>Model</th><th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {pageItems.map((p) => {
                        const athlete = athleteMap[p.athlete_id];
                        return (
                          <tr key={p.prediction_id}>
                            <td>{new Date(p.prediction_date).toLocaleString()}</td>
                            <td><Link to={`/athletes/${p.athlete_id}`}>{athlete?.name || p.athlete_id}</Link></td>
                            <td>{athlete?.event_type || "—"}</td>
                            <td><RiskBadge level={p.risk_level} /></td>
                            <td>{(p.probability * 100).toFixed(1)}%</td>
                            <td>{p.model_version}</td>
                            <td>
                              <div className="row-actions">
                                <Link className="btn btn-ghost btn-sm" to={`/explainability?prediction_id=${p.prediction_id}`}>
                                  <Sparkles size={13} /> SHAP
                                </Link>
                                <Link className="btn btn-ghost btn-sm" to={`/reports?prediction_id=${p.prediction_id}`}>
                                  <FileText size={13} /> Report
                                </Link>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <Pagination page={page} pageSize={PAGE_SIZE} total={filtered.length} onChange={setPage} />
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
