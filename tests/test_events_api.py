from __future__ import annotations


def test_list_events_filters_by_severity(client, reader_headers) -> None:
    response = client.get(
        "/events",
        headers=reader_headers,
        params={"severity": "critical"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"]["total"] == 1
    assert [item["severity"] for item in body["items"]] == ["critical"]


def test_create_event_by_external_id_updates_device_activity(
    client,
    reader_headers,
    writer_headers,
) -> None:
    create_response = client.post(
        "/events",
        headers=writer_headers,
        json={
            "device_external_id": "cooling-node-3",
            "source": "agent",
            "severity": "warning",
            "message": "fan speed dropped below threshold",
            "payload": {"rpm": 420},
        },
    )

    assert create_response.status_code == 201
    created_event = create_response.json()
    assert created_event["device_external_id"] == "cooling-node-3"

    devices_response = client.get(
        "/devices",
        headers=reader_headers,
        params={"status": "offline"},
    )
    assert devices_response.status_code == 200
    offline_device = devices_response.json()["items"][0]
    assert offline_device["external_id"] == "cooling-node-3"
    assert offline_device["last_seen_at"] is not None


def test_create_event_returns_not_found_for_unknown_device(
    client,
    writer_headers,
) -> None:
    response = client.post(
        "/events",
        headers=writer_headers,
        json={
            "device_external_id": "missing-device",
            "source": "manual",
            "severity": "info",
            "message": "operator note",
            "payload": {},
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "device not found"
