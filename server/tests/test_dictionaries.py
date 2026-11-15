def test_list_dictionaries_unauthorized(client):
    r = client.get("/api/v1/dictionaries")
    assert r.status_code == 401


def test_list_dictionaries_authorized(client, user_a):
    r = client.get("/api/v1/dictionaries?lang=en", headers=user_a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert len(data["items"]) > 0
    first = data["items"][0]
    assert first["lang"] == "en"
    assert "cnt" in first
    assert "added" in first


def test_add_and_remove_user_dictionary(client, user_a):
    dicts_r = client.get("/api/v1/dictionaries?lang=en", headers=user_a["headers"])
    dict_id = dicts_r.json()["items"][0]["id"]

    # Добавляем в изучаемые
    add_r = client.post(f"/api/v1/dictionaries/{dict_id}/add", headers=user_a["headers"])
    assert add_r.status_code == 200

    # Проверяем флаг added == 1
    check_r = client.get("/api/v1/dictionaries?lang=en", headers=user_a["headers"])
    matching = next(d for d in check_r.json()["items"] if d["id"] == dict_id)
    assert matching["added"] == 1

    # Удаляем из изучаемых
    del_r = client.delete(f"/api/v1/dictionaries/{dict_id}/add", headers=user_a["headers"])
    assert del_r.status_code == 200

    # Проверяем флаг added == 0
    check_r2 = client.get("/api/v1/dictionaries?lang=en", headers=user_a["headers"])
    matching2 = next(d for d in check_r2.json()["items"] if d["id"] == dict_id)
    assert matching2["added"] == 0
