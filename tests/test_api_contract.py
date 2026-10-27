from fastapi.testclient import TestClient

from reviewforge.api import app

client = TestClient(app)


def test_health_reports_provider_is_not_configured():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "review_provider": "not_configured"}


def test_changed_lines_endpoint_is_explicitly_not_a_review():
    diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -0,0 +1 @@
+print('hello')
"""
    response = client.post("/v1/diff/changed-lines", json={"diff": diff})

    assert response.status_code == 200
    assert response.json() == {
        "status": "parsed",
        "review_performed": False,
        "changed_line_count": 1,
        "changed_lines": [{"path": "a.py", "new_line": 1, "content": "print('hello')"}],
        "warning": "Diff parsing is not AI review and does not assess code safety.",
    }


def test_changed_lines_endpoint_rejects_empty_diff():
    response = client.post("/v1/diff/changed-lines", json={"diff": ""})

    assert response.status_code == 422
