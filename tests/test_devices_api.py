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


def test_import_devices_creates_multiple_entries(client, writer_headers) -> None:
    response = client.post(
        "/devices/import",
        headers=writer_headers,
        json={
            "items": [
                {
                    "external_id": "edge-gw-31",
                    "name": "Edge Gateway 31",
                    "site": "fra-1",
                    "owner_team": "ops-core",
                    "status": "active",
                    "metadata": {"rack": "r3"},
                },
                {
                    "external_id": "edge-gw-32",
                    "name": "Edge Gateway 32",
                    "site": "ams-2",
                    "owner_team": "ops-core",
                    "status": "maintenance",
                    "metadata": {"rack": "r4"},
                },
            ]
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["imported_count"] == 2
    assert body["failed_count"] == 0


def test_import_devices_collects_duplicate_failures(client, writer_headers) -> None:
    response = client.post(
        "/devices/import",
        headers=writer_headers,
        json={
            "continue_on_error": True,
            "items": [
                {
                    "external_id": "edge-gw-1",
                    "name": "Duplicate Edge Gateway",
                    "site": "fra-1",
                    "owner_team": "ops-core",
                    "status": "active",
                    "metadata": {},
                },
                {
                    "external_id": "edge-gw-99",
                    "name": "Edge Gateway 99",
                    "site": "mad-1",
                    "owner_team": "ops-core",
                    "status": "active",
                    "metadata": {},
                },
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["imported_count"] == 1
    assert body["failed_count"] == 1
