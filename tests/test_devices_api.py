from __future__ import annotations


def test_list_devices_filters_by_status_and_site(client, reader_headers) -> None:
    response = client.get(
        "/devices",
        headers=reader_headers,
        params={"status": "active", "site": "fra-1", "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"]["total"] == 1
    assert body["page"]["has_more"] is False
    assert [item["external_id"] for item in body["items"]] == ["edge-gw-1"]


def test_summary_uses_cache_after_first_call(client, reader_headers) -> None:
    first_response = client.get("/devices/summary", headers=reader_headers)
    second_response = client.get("/devices/summary", headers=reader_headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["cached"] is False
    assert second_response.json()["cached"] is True


def test_create_device_invalidates_summary_cache(
    client,
    reader_headers,
    writer_headers,
) -> None:
    first_summary = client.get("/devices/summary", headers=reader_headers)
    assert first_summary.status_code == 200

    create_response = client.post(
        "/devices",
        headers=writer_headers,
        json={
            "external_id": "edge-gw-9",
            "name": "Edge Gateway 9",
            "site": "ams-1",
            "owner_team": "ops-core",
            "status": "active",
            "metadata": {"rack": "r7"},
        },
    )

    assert create_response.status_code == 201

    refreshed_summary = client.get("/devices/summary", headers=reader_headers)
    assert refreshed_summary.status_code == 200
    assert refreshed_summary.json()["cached"] is False
    assert refreshed_summary.json()["total_devices"] == 4
