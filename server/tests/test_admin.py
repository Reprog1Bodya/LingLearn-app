def test_admin_analytics_forbidden_for_regular_user(client, user_a):
    r = client.get("/api/v1/admin/analytics", headers=user_a["headers"])
    assert r.status_code == 403
    assert "Недостаточно прав" in r.json()["detail"]


def test_admin_analytics_success(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = client.get("/api/v1/admin/analytics", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["users"] >= 1
    assert data["dictionaries"] >= 1
    assert data["words"] >= 1


def test_admin_cannot_delete_self(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Получаем профиль админа
    prof_r = client.get("/api/v1/profile", headers=headers)
    admin_id = prof_r.json()["id"]

    del_r = client.delete(f"/api/v1/admin/users/{admin_id}", headers=headers)
    assert del_r.status_code == 400
    assert "Нельзя удалить собственную учетную запись" in del_r.json()["detail"]
