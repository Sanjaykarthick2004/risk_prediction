import {
  Activity, Brain, ClipboardList, Coffee, HeartPulse, Plus, ShieldAlert, User,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAthlete } from "../api/athleteApi";
import { listAssessments } from "../api/assessmentApi";
import { getAthletePredictions } from "../api/predictionApi";
import {
  Alert, Breadcrumb, Button, EmptyState, RiskBadge, SkeletonCard, Tabs,
} from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";

const TABS = [
  { key: "overview", label: "Overview", icon: User },
  { key: "training", label: "Training", icon: Activity },
  { key: "physiological", label: "Physiological", icon: HeartPulse },
  { key: "recovery", label: "Recovery", icon: Coffee },
  { key: "lifestyle", label: "Lifestyle", icon: Brain },
  { key: "injury_history", label: "Previous Injury", icon: ShieldAlert },
];

export default function AthleteDetails() {
  const { athleteId } = useParams();
  const [athlete, setAthlete] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("overview");

  useEffect(() => {
    Promise.all([getAthlete(athleteId), listAssessments(athleteId), getAthletePredictions(athleteId)])
      .then(([a, asm, preds]) => { setAthlete(a); setAssessments(asm); setPredictions(preds); })
      .catch((err) => setError(extractErrorMessage(err)));
  }, [athleteId]);

  if (error) return <Alert tone="error" title="We couldn't load this athlete.">{error}</Alert>;
  if (!athlete) return <SkeletonCard lines={5} />;

  const latestAssessment = assessments[0]; // already sorted newest-first by the backend
  const latestPrediction = predictions[0];
  const initials = athlete.name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div>
      <Breadcrumb items={[{ label: "Athletes", to: "/athletes" }, { label: athlete.name }]} />

      <div className="athlete-hero">
        <span className="athlete-avatar">{initials}</span>
        <div className="athlete-hero-info">
          <h1 className="athlete-hero-name">{athlete.name} <span className="text-caption">({athlete.athlete_id})</span></h1>
          <p className="text-secondary" style={{ margin: "2px 0 0" }}>{athlete.event_type} Runner</p>
        </div>
        <div className="athlete-hero-risk">
          {latestPrediction ? (
            <>
              <RiskBadge level={latestPrediction.risk_level} probability={latestPrediction.probability} size="lg" />
              <div className="text-caption" style={{ marginTop: 6 }}>
                Latest assessment: {latestAssessment ? new Date(latestAssessment.assessment_date).toLocaleDateString() : "—"}
              </div>
            </>
          ) : (
            <span className="text-caption">No predictions yet</span>
          )}
        </div>
      </div>

      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      <div className="card">
        {tab === "overview" && <OverviewTab athlete={athlete} />}
        {tab !== "overview" && (
          latestAssessment ? (
            <ModalityTab tab={tab} assessment={latestAssessment} />
          ) : (
            <EmptyState
              icon={ClipboardList}
              title="No assessments yet"
              description="This section fills in once an assessment has been recorded for this athlete."
              action={<Button to={`/prediction?athlete_id=${athleteId}`} icon={Plus}>New Assessment</Button>}
            />
          )
        )}
      </div>

      <div className="card">
        <h3>Assessments ({assessments.length})</h3>
        {assessments.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No assessments yet"
            description="Create the first assessment to start tracking this athlete's training, recovery, and injury risk."
            action={<Button to={`/prediction?athlete_id=${athleteId}`} icon={Plus}>New Assessment / Prediction</Button>}
          />
        ) : (
          <>
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr><th>Assessment ID</th><th>Date</th><th>Fatigue</th><th>Sleep Hours</th><th>Previous Injury</th></tr></thead>
                <tbody>
                  {assessments.map((a) => (
                    <tr key={a.assessment_id}>
                      <td><span className="id-chip">{a.assessment_id}</span></td>
                      <td>{new Date(a.assessment_date).toLocaleString()}</td>
                      <td>{a.physiological.fatigue_score}/10</td>
                      <td>{a.recovery.sleep_hours}h</td>
                      <td>{a.injury_history.previous_injury ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Button to={`/prediction?athlete_id=${athleteId}`} icon={Plus} style={{ marginTop: 14 }}>
              New Assessment / Prediction
            </Button>
          </>
        )}
      </div>

      <div className="card">
        <h3>Prediction History ({predictions.length})</h3>
        {predictions.length === 0 ? (
          <EmptyState icon={ShieldAlert} title="No predictions yet" description="Generate a prediction from an assessment to see risk results here." />
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th>Date</th><th>Risk</th><th></th></tr></thead>
              <tbody>
                {predictions.map((p) => (
                  <tr key={p.prediction_id}>
                    <td>{new Date(p.prediction_date).toLocaleString()}</td>
                    <td><RiskBadge level={p.risk_level} probability={p.probability} /></td>
                    <td><Link to={`/reports?prediction_id=${p.prediction_id}`}>Report</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function OverviewTab({ athlete }) {
  const bmi = athlete.height && athlete.weight ? (athlete.weight / (athlete.height / 100) ** 2).toFixed(1) : "—";
  return (
    <div className="detail-grid">
      <div><b>Age</b><br />{athlete.age} yrs</div>
      <div><b>Gender</b><br />{athlete.gender}</div>
      <div><b>Height</b><br />{athlete.height} cm</div>
      <div><b>Weight</b><br />{athlete.weight} kg</div>
      <div><b>BMI</b><br />{bmi}</div>
      <div><b>Experience</b><br />{athlete.experience_years} yrs</div>
      <div><b>Event Type</b><br />{athlete.event_type}</div>
      <div><b>Sport</b><br />{athlete.sport}</div>
    </div>
  );
}

function ModalityTab({ tab, assessment }) {
  const data = assessment[tab];
  if (tab === "training") {
    const workloadRatio = data.chronic_training_load ? (data.acute_training_load / data.chronic_training_load).toFixed(2) : "—";
    return (
      <div className="detail-grid">
        <div><b>Training Hours/Week</b><br />{data.training_hours_per_week} hrs</div>
        <div><b>Frequency</b><br />{data.training_frequency} days/week</div>
        <div><b>Intensity</b><br />{data.training_intensity}/10</div>
        <div><b>Weekly Distance</b><br />{data.weekly_distance_km} km</div>
        <div><b>Long Run Distance</b><br />{data.long_run_distance_km} km</div>
        <div><b>Speed Work Sessions</b><br />{data.speed_work_sessions}/week</div>
        <div><b>Training Load</b><br />{data.training_load}</div>
        <div><b>Acute Load</b><br />{data.acute_training_load}</div>
        <div><b>Chronic Load</b><br />{data.chronic_training_load}</div>
        <div><b>Workload Ratio</b><br />{workloadRatio}</div>
      </div>
    );
  }
  if (tab === "physiological") {
    return (
      <div className="detail-grid">
        <div><b>Resting Heart Rate</b><br />{data.resting_heart_rate} bpm</div>
        <div><b>HRV</b><br />{data.heart_rate_variability} ms</div>
        <div><b>Fatigue</b><br />{data.fatigue_score}/10</div>
        <div><b>Muscle Soreness</b><br />{data.muscle_soreness}/10</div>
        <div><b>Recovery Score</b><br />{data.recovery_score}/100</div>
      </div>
    );
  }
  if (tab === "recovery") {
    const sleepDeficit = Math.max(0, 8 - data.sleep_hours).toFixed(1);
    const recoveryGap = data.rest_days - data.recovery_days;
    return (
      <div className="detail-grid">
        <div><b>Sleep Hours</b><br />{data.sleep_hours} hrs/night</div>
        <div><b>Sleep Quality</b><br />{data.sleep_quality}/10</div>
        <div><b>Recovery Days</b><br />{data.recovery_days}</div>
        <div><b>Rest Days</b><br />{data.rest_days}</div>
        <div><b>Sleep Deficit</b><br />{sleepDeficit} hrs</div>
        <div><b>Recovery Gap</b><br />{recoveryGap}</div>
      </div>
    );
  }
  if (tab === "lifestyle") {
    return (
      <div className="detail-grid">
        <div><b>Stress Level</b><br />{data.stress_level}/10</div>
        <div><b>Hydration Score</b><br />{data.hydration_score}/100</div>
        <div><b>Nutrition Score</b><br />{data.nutrition_score}/100</div>
      </div>
    );
  }
  // injury_history
  return (
    <div className="detail-grid">
      <div><b>Previous Injury</b><br />{data.previous_injury ? "Yes" : "No"}</div>
      <div><b>Injury Count</b><br />{data.injury_count}</div>
      <div><b>Injury Type</b><br />{data.previous_injury_type}</div>
      <div><b>Days Since Injury</b><br />{data.days_since_previous_injury}</div>
      <div><b>Recovery Duration</b><br />{data.previous_recovery_duration} days</div>
    </div>
  );
}
