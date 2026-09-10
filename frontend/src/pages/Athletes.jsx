import { Plus, Search, Trash2, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createAthlete, deleteAthlete, listAthletes } from "../api/athleteApi";
import {
  Alert, Button, ConfirmModal, EmptyState, FormField, PageHeader, Pagination, paginate,
  SkeletonTable, useToast,
} from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";

const EVENT_TYPES = ["Sprint", "Middle Distance", "Long Distance", "Cross Country", "General Running"];
const PAGE_SIZE = 10;

const EMPTY_FORM = {
  name: "", age: "", gender: "Male", sport: "Running", event_type: "General Running",
  height: "", weight: "", experience_years: "",
};

export default function Athletes() {
  const toast = useToast();
  const [athletes, setAthletes] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  function load(searchValue = search) {
    listAthletes(searchValue).then(setAthletes).catch((err) => setError(extractErrorMessage(err)));
  }

  useEffect(() => { load(""); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const created = await createAthlete({
        ...form,
        age: Number(form.age), height: Number(form.height),
        weight: Number(form.weight), experience_years: Number(form.experience_years),
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
      toast(`Athlete ${created.athlete_id} created successfully.`, "success");
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    setDeleting(true);
    try {
      await deleteAthlete(pendingDelete);
      toast("Athlete deleted.", "success");
      setPendingDelete(null);
      load();
    } catch (err) {
      toast(extractErrorMessage(err), "error");
    } finally {
      setDeleting(false);
    }
  }

  const pageItems = useMemo(() => (athletes ? paginate(athletes, page, PAGE_SIZE) : []), [athletes, page]);

  return (
    <div>
      <PageHeader
        icon={Users}
        title="Athletes"
        description="Research population: Running Athletes."
        actions={<Button icon={Plus} onClick={() => setShowForm((s) => !s)}>{showForm ? "Cancel" : "Add Athlete"}</Button>}
      />

      {error && <Alert tone="error" title="We couldn't complete that action.">{error}</Alert>}

      {showForm && (
        <form className="card form-card" onSubmit={handleCreate}>
          <p className="text-secondary" style={{ margin: 0 }}>The Athlete ID is generated automatically (e.g. ATH-0007) once you save.</p>
          <div className="form-grid">
            <FormField label="Name" required>
              <input value={form.name} required onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </FormField>
            <FormField label="Age" required unit="years">
              <input type="number" min={15} max={60} value={form.age} required onChange={(e) => setForm({ ...form, age: e.target.value })} />
            </FormField>
            <FormField label="Gender">
              <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                {["Male", "Female", "Other"].map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </FormField>
            <FormField label="Sport">
              <input type="text" value={form.sport} disabled />
            </FormField>
            <FormField label="Event Type">
              <select value={form.event_type} onChange={(e) => setForm({ ...form, event_type: e.target.value })}>
                {EVENT_TYPES.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </FormField>
            <FormField label="Height" required unit="cm">
              <input type="number" min={100} max={230} value={form.height} required onChange={(e) => setForm({ ...form, height: e.target.value })} />
            </FormField>
            <FormField label="Weight" required unit="kg">
              <input type="number" min={30} max={200} value={form.weight} required onChange={(e) => setForm({ ...form, weight: e.target.value })} />
            </FormField>
            <FormField label="Experience" required unit="years">
              <input type="number" min={0} max={45} value={form.experience_years} required onChange={(e) => setForm({ ...form, experience_years: e.target.value })} />
            </FormField>
          </div>
          <Button type="submit" loading={saving}>Save Athlete</Button>
        </form>
      )}

      <div className="card">
        <div className="search-wrap">
          <Search size={16} className="search-icon" />
          <input
            className="search-input" placeholder="Search by name or ID..." aria-label="Search athletes" value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); load(e.target.value); }}
          />
        </div>

        {!athletes && <SkeletonTable rows={6} cols={7} />}

        {athletes && athletes.length === 0 && (
          <EmptyState
            icon={Users}
            title="No athletes yet"
            description="Add your first running athlete to start recording assessments and generating injury-risk predictions."
            action={<Button icon={Plus} onClick={() => setShowForm(true)}>Add Athlete</Button>}
          />
        )}

        {athletes && athletes.length > 0 && (
          <>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr><th>Athlete ID</th><th>Name</th><th>Age</th><th>Gender</th><th>Sport</th><th>Event Type</th><th></th></tr>
                </thead>
                <tbody>
                  {pageItems.map((a) => (
                    <tr key={a.athlete_id}>
                      <td><Link to={`/athletes/${a.athlete_id}`}>{a.athlete_id}</Link></td>
                      <td>{a.name}</td>
                      <td>{a.age}</td>
                      <td>{a.gender}</td>
                      <td>{a.sport}</td>
                      <td>{a.event_type}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm" onClick={() => setPendingDelete(a.athlete_id)}>
                          <Trash2 size={13} /> Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={athletes.length} onChange={setPage} />
          </>
        )}
      </div>

      <ConfirmModal
        open={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        busy={deleting}
        title="Delete Athlete?"
        description={`This will permanently delete ${pendingDelete} and cannot be undone.`}
        confirmLabel="Delete Athlete"
      />
    </div>
  );
}
