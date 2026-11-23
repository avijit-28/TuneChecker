import time
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

def test_full_pipeline_red_call():
    client = TestClient(app)
    red_audio_path = Path("D:/avi/TuneChecker/samples/red_call_01.m4a")
    assert red_audio_path.exists(), f"File {red_audio_path} does not exist"

    with open(red_audio_path, "rb") as f:
        response = client.post(
            "/api/v1/calls",
            files={"file": ("red_call_01.m4a", f, "audio/mp4")}
        )

    assert response.status_code == 202, f"Upload failed: {response.text}"
    call_data = response.json()
    call_id = call_data["id"]
    print(f"\nUploaded call {call_id}, status: {call_data['status']}")

    # Poll status until terminal (complete, partial, or failed)
    max_wait = 180
    start = time.time()
    final_status = None

    while time.time() - start < max_wait:
        r_status = client.get(f"/api/v1/calls/{call_id}/status")
        assert r_status.status_code == 200
        st = r_status.json()
        print(f"Status: {st['status']} (Completed stages: {st['completed_stages']}/7)")
        if st["status"] in ["complete", "partial", "failed"]:
            final_status = st["status"]
            break
        time.sleep(2)

    assert final_status in ["complete", "partial"], f"Pipeline failed or timed out: {final_status}"
    print(f"Pipeline finished with final status: {final_status}")

    # Verify transcript endpoint
    r_tr = client.get(f"/api/v1/calls/{call_id}/transcript")
    assert r_tr.status_code == 200
    tr = r_tr.json()
    assert len(tr["utterances"]) > 0
    assert len(tr["speakers"]) >= 1
    print(f"Transcript verified: {len(tr['utterances'])} utterances, {len(tr['speakers'])} speakers.")

    # Verify analysis endpoint
    r_an = client.get(f"/api/v1/calls/{call_id}/analysis")
    assert r_an.status_code == 200
    an = r_an.json()
    print(f"Analysis verdict: {an['verdict']}, confidence: {an['confidence']['level']}")
    assert an["verdict"] == "RED", f"Expected RED verdict, got {an['verdict']}"
    assert len(an["evidence"]) > 0, "Expected at least 1 verified evidence item"
    print(f"Verified evidence quotes count: {len(an['evidence'])}")
    for ev in an["evidence"]:
        print(f"  [{ev['ref']}] \"{ev['quote']}\" ({ev['criterion_id']})")

    # Verify action items
    assert isinstance(an["action_items"], list)
    print(f"Verified action items count: {len(an['action_items'])}")
    for act in an["action_items"]:
        print(f"  [{act['ref']}] {act['task']} (Owner: {act['owner']['text']}, Deadline: {act['deadline']})")

    # Verify export endpoint
    r_exp_md = client.get(f"/api/v1/calls/{call_id}/export?format=markdown")
    assert r_exp_md.status_code == 200
    assert "Sales Call Audit Report" in r_exp_md.text
    print("Markdown export verified.")

    # Verify dashboard summary updated
    r_dash = client.get("/api/v1/dashboard/summary")
    assert r_dash.status_code == 200
    dash = r_dash.json()
    assert dash["kpis"]["total_calls"] >= 1
    assert dash["kpis"]["red"] >= 1
    print("Dashboard KPIs verified!")


def test_full_pipeline_green_call():
    client = TestClient(app)
    green_audio_path = Path("D:/avi/TuneChecker/samples/green_call_01.m4a")
    assert green_audio_path.exists(), f"File {green_audio_path} does not exist"

    with open(green_audio_path, "rb") as f:
        response = client.post(
            "/api/v1/calls",
            files={"file": ("green_call_01.m4a", f, "audio/mp4")}
        )

    assert response.status_code == 202, f"Upload failed: {response.text}"
    call_data = response.json()
    call_id = call_data["id"]
    print(f"\nUploaded green call {call_id}, status: {call_data['status']}")

    max_wait = 180
    start = time.time()
    final_status = None

    while time.time() - start < max_wait:
        r_status = client.get(f"/api/v1/calls/{call_id}/status")
        assert r_status.status_code == 200
        st = r_status.json()
        print(f"Status: {st['status']} (Completed stages: {st['completed_stages']}/7)")
        if st["status"] in ["complete", "partial", "failed"]:
            final_status = st["status"]
            break
        time.sleep(2)

    assert final_status in ["complete", "partial"], f"Pipeline failed or timed out: {final_status}"
    print(f"Green pipeline finished with final status: {final_status}")

    # Verify transcript
    r_tr = client.get(f"/api/v1/calls/{call_id}/transcript")
    assert r_tr.status_code == 200
    tr = r_tr.json()
    assert len(tr["utterances"]) > 0

    # Verify analysis
    r_an = client.get(f"/api/v1/calls/{call_id}/analysis")
    assert r_an.status_code == 200
    an = r_an.json()
    print(f"Analysis verdict: {an['verdict']}, confidence: {an['confidence']['level']}")
    assert an["verdict"] == "GREEN", f"Expected GREEN verdict, got {an['verdict']}"
    assert len(an["evidence"]) == 0, f"Expected 0 negative evidence items, got {len(an['evidence'])}"
    print("GREEN verdict and clean evidence list verified!")

    # Verify export endpoint
    r_exp_md = client.get(f"/api/v1/calls/{call_id}/export?format=markdown")
    assert r_exp_md.status_code == 200
    assert "Sales Call Audit Report" in r_exp_md.text
    assert "GREEN" in r_exp_md.text
    print("Markdown export verified for green call.")

    # Verify Role Swap: swap roles so Speaker A is sales_rep and Speaker B is customer
    r_swap = client.put(
        f"/api/v1/calls/{call_id}/speaker-roles",
        json={"roles": {"A": "sales_rep", "B": "customer"}}
    )
    assert r_swap.status_code == 202
    assert r_swap.json()["status"] == "analyzing"
    print("Speaker roles swapped. Polling for re-analysis completion...")

    start = time.time()
    final_swap_status = None
    while time.time() - start < 120:
        r_status = client.get(f"/api/v1/calls/{call_id}/status")
        assert r_status.status_code == 200
        st = r_status.json()
        if st["status"] in ["complete", "partial", "failed"]:
            final_swap_status = st["status"]
            break
        time.sleep(2)

    assert final_swap_status in ["complete", "partial"]
    r_an2 = client.get(f"/api/v1/calls/{call_id}/analysis")
    assert r_an2.status_code == 200
    an2 = r_an2.json()
    assert an2["run_number"] >= 2
    assert an2["sales_rep"]["label"] == "A"
    assert an2["sales_rep"]["source"] == "user"
    assert an2["sales_rep"]["status"] == "confirmed"
    print(f"Role swap verified: Run {an2['run_number']}, Rep is Speaker {an2['sales_rep']['label']}, source={an2['sales_rep']['source']}")
