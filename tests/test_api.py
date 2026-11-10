import io
from fastapi.testclient import TestClient
from app.main import app
from api.index import app as vercel_app


client = TestClient(app)


def test_index_endpoint():
    """Verify root / serves HTML dashboard with 200 OK without errors."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Polars CSV Analytics Dashboard" in response.text
    assert "Polars Analytics Dashboard" in response.text


def test_static_files():
    """Verify static assets are properly served."""
    css_resp = client.get("/static/css/styles.css")
    assert css_resp.status_code == 200
    assert "text/css" in css_resp.headers.get("content-type", "")

    js_resp = client.get("/static/js/dashboard.js")
    assert js_resp.status_code == 200


def test_health_check():
    """Verify /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("engine") == "Polars"
    assert data.get("framework") == "FastAPI"


def test_list_sample_files():
    """Verify sample files endpoint returns the sample CSV datasets."""
    response = client.get("/api/sample-files")
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)
    filenames = [f["filename"] for f in files]
    assert "ecommerce_orders.csv" in filenames
    assert "employee_metrics.csv" in filenames


def test_load_sample_file():
    """Verify loading a valid sample file processes data via Polars."""
    response = client.get("/api/load-sample/ecommerce_orders.csv")
    assert response.status_code == 200
    data = response.json()
    assert data.get("file_name") == "ecommerce_orders.csv"
    assert "kpis" in data
    assert "summary_statistics" in data
    assert "chart_data" in data
    assert data["kpis"]["total_rows"] > 0


def test_load_sample_file_not_found():
    """Verify 404 for nonexistent sample file."""
    response = client.get("/api/load-sample/non_existent_dataset.csv")
    assert response.status_code == 404


def test_upload_csv():
    """Verify uploading a CSV file processes data correctly."""
    csv_content = b"col1,col2,col3\n1,10.5,alpha\n2,20.0,beta\n3,,gamma\n"
    response = client.post(
        "/api/upload",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kpis"]["total_rows"] == 3
    assert data["kpis"]["total_columns"] == 3


def test_upload_invalid_extension():
    """Verify uploading a non-csv file returns 400."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", io.BytesIO(b"some text"), "text/plain")},
    )
    assert response.status_code == 400


def test_vercel_entrypoint_app():
    """Verify api/index.py exports the FastAPI app."""
    assert vercel_app is app
