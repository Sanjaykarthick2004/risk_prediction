"""API-level test of the dataset upload -> validate -> process -> select-for-training
workflow, using a small running-athlete CSV built with the current schema.

The "selected training dataset" pointer is GLOBAL to the app (not per-owner),
so this test always resets it back to the default synthetic dataset when
done, to avoid leaving other tests / the running app pointed at a throwaway
test upload.
"""
import io

from app.ml.data_loader import generate_synthetic_dataset


def _small_csv_bytes(n=120, seed=99):
    df = generate_synthetic_dataset(n_athletes=n, seed=seed)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.read()


def test_dataset_upload_validate_process_select_workflow(client, auth_headers):
    csv_bytes = _small_csv_bytes()
    try:
        upload_res = client.post(
            "/api/datasets/upload",
            files={"file": ("pytest_running_dataset.csv", csv_bytes, "text/csv")},
            headers=auth_headers,
        )
        assert upload_res.status_code == 200
        uploaded = upload_res.json()
        dataset_id = uploaded["dataset_id"]
        assert uploaded["rows"] == 120
        assert "event_type" in uploaded["column_names"]
        assert "position" not in uploaded["column_names"]

        validate_res = client.post(f"/api/datasets/{dataset_id}/validate", headers=auth_headers)
        assert validate_res.status_code == 200
        validation = validate_res.json()
        assert validation["is_valid"] is True
        assert validation["stats"]["n_missing_values"] == 0

        process_res = client.post(f"/api/datasets/{dataset_id}/process", headers=auth_headers)
        assert process_res.status_code == 200
        processed = process_res.json()
        assert processed["has_target_column"] is True
        assert "workload_ratio" in processed["columns_after_processing"]

        select_res = client.post(f"/api/datasets/{dataset_id}/select-for-training", headers=auth_headers)
        assert select_res.status_code == 200

        selection_res = client.get("/api/datasets/training-selection", headers=auth_headers)
        assert selection_res.status_code == 200
        assert selection_res.json()["dataset_id"] == dataset_id
        assert selection_res.json()["source"] == "uploaded"
    finally:
        reset_res = client.post("/api/datasets/reset-training-selection", headers=auth_headers)
        assert reset_res.status_code == 200
        assert reset_res.json()["source"] == "synthetic"
