from __future__ import annotations


def test_healthcheck_does_not_require_auth(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_devices_rejects_invalid_token(client) -> None:
    response = client.get("/devices", headers={"X-Api-Key": "bad-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid api key"


def test_reader_cannot_create_device(client, reader_headers) -> None:
    response = client.post(
        "/devices",
        headers=reader_headers,
        json={
            "external_id": "edge-gw-22",
            "name": "Edge Gateway 22",
            "site": "fra-1",
            "owner_team": "ops-core",
            "metadata": {"rack": "r9"},
        },
    )

    assert response.status_code == 403
    assert "scope 'write'" in response.json()["detail"]
