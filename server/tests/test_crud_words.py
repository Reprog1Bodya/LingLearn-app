def test_create_word(client, user_a):
    payload = {
        "word": "Kaffee",
        "translation": "кофе",
        "transcription": "[ˈkafeː]",
        "example": "Ich trinke gerne Kaffee.",
    }
    r = client.post("/api/v1/my/words", json=payload, headers=user_a["headers"])
    assert r.status_code == 201
    data = r.json()
    assert data["word"] == "Kaffee"
    assert data["translation"] == "кофе"
    assert data["transcription"] == "[ˈkafeː]"
    word_id = data["id"]

    # Проверка сохранения в БД и доступности при повторном запросе
    repeat_r = client.get(f"/api/v1/my/words/{word_id}", headers=user_a["headers"])
    assert repeat_r.status_code == 200
    assert repeat_r.json()["id"] == word_id
    assert repeat_r.json()["word"] == "Kaffee"


def test_get_word_not_found(client, user_a):
    r = client.get("/api/v1/my/words/999999", headers=user_a["headers"])
    assert r.status_code == 404


def test_update_word(client, user_a):
    # Создаём слово
    create_r = client.post("/api/v1/my/words", json={
        "word": "Tee",
        "translation": "чай",
        "transcription": "[teː]",
        "example": "Heißer Tee.",
    }, headers=user_a["headers"])
    assert create_r.status_code == 201
    word_id = create_r.json()["id"]

    # Обновляем перевод и пример
    update_r = client.put(f"/api/v1/my/words/{word_id}", json={
        "translation": "зелёный чай",
        "example": "Ich trinke heißen grünen Tee.",
    }, headers=user_a["headers"])
    assert update_r.status_code == 200
    assert update_r.json()["translation"] == "зелёный чай"
    assert update_r.json()["example"] == "Ich trinke heißen grünen Tee."

    # Проверка сохранения обновленных данных при повторном запросе
    get_r = client.get(f"/api/v1/my/words/{word_id}", headers=user_a["headers"])
    assert get_r.status_code == 200
    assert get_r.json()["translation"] == "зелёный чай"


def test_delete_word(client, user_a):
    # Создаём слово
    create_r = client.post("/api/v1/my/words", json={
        "word": "Wasser",
        "translation": "вода",
    }, headers=user_a["headers"])
    assert create_r.status_code == 201
    word_id = create_r.json()["id"]

    # Удаляем
    del_r = client.delete(f"/api/v1/my/words/{word_id}", headers=user_a["headers"])
    assert del_r.status_code == 204

    # Повторный запрос должен вернуть 404
    get_r = client.get(f"/api/v1/my/words/{word_id}", headers=user_a["headers"])
    assert get_r.status_code == 404


def test_forbidden_modify_other_user_word(client, user_a, user_b):
    # User A создаёт слово в своём словаре
    create_r = client.post("/api/v1/my/words", json={
        "word": "Geheimnis",
        "translation": "секрет",
    }, headers=user_a["headers"])
    assert create_r.status_code == 201
    word_id = create_r.json()["id"]

    # User B пытается отредактировать слово User A -> 403 Forbidden!
    edit_r = client.put(f"/api/v1/my/words/{word_id}", json={
        "translation": "взломанный секрет",
    }, headers=user_b["headers"])
    assert edit_r.status_code == 403

    # User B пытается удалить слово User A -> 403 Forbidden!
    del_r = client.delete(f"/api/v1/my/words/{word_id}", headers=user_b["headers"])
    assert del_r.status_code == 403


def test_server_search_and_pagination(client, user_a):
    # Создаем несколько тестовых слов
    for w in ["Apfel", "Banane", "Orange", "Ananas", "Kirsche"]:
        client.post("/api/v1/my/words", json={"word": w, "translation": f"tr_{w}"}, headers=user_a["headers"])

    # Серверный поиск по префиксу "An"
    search_r = client.get("/api/v1/my/words?search=Ananas", headers=user_a["headers"])
    assert search_r.status_code == 200
    items = search_r.json()["items"]
    assert any(x["word"] == "Ananas" for x in items)

    # Пагинация (limit=2, offset=0)
    p1 = client.get("/api/v1/my/words?limit=2&offset=0", headers=user_a["headers"])
    assert p1.status_code == 200
    assert len(p1.json()["items"]) <= 2
    assert p1.json()["limit"] == 2
    assert p1.json()["offset"] == 0
    assert p1.json()["total"] >= 5


def test_toggle_word_learned(client, user_a):
    create_r = client.post("/api/v1/my/words", json={"word": "Lernen", "translation": "учиться"}, headers=user_a["headers"])
    word_id = create_r.json()["id"]

    # Отмечаем выученным
    r1 = client.post(f"/api/v1/words/{word_id}/learned", json={"learned": True}, headers=user_a["headers"])
    assert r1.status_code == 200

    # Проверяем фильтрацию "только выученные"
    r_list = client.get("/api/v1/my/words?filter=learned", headers=user_a["headers"])
    assert r_list.status_code == 200
    assert any(x["id"] == word_id for x in r_list.json()["items"])
