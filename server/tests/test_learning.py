def test_generate_test_questions(client):
    # Получаем словарь
    dicts_r = client.get("/api/v1/languages")
    assert dicts_r.status_code == 200

    test_r = client.get("/api/v1/test?dict_id=1&n=5")
    assert test_r.status_code == 200
    data = test_r.json()
    assert data["kind"] == "translate"
    assert len(data["questions"]) <= 5
    for q in data["questions"]:
        assert "word" in q
        assert "answer" in q
        assert "options" in q
        assert len(q["options"]) >= 2
        assert q["answer"] in q["options"]


def test_atomic_test_result_and_stats(client, user_a):
    # Проходим тест и отправляем результат
    payload = {
        "dict_id": 1,
        "kind": "translate",
        "score": 5,
        "total": 5,
        "answers": {"1": True, "2": True},
    }
    r = client.post("/api/v1/test/result", json=payload, headers=user_a["headers"])
    assert r.status_code == 200
    data = r.json()
    assert data["points"] == 50
    assert data["streak"] >= 1

    # Проверяем обновление профиля и статистики
    stats_r = client.get("/api/v1/stats", headers=user_a["headers"])
    assert stats_r.status_code == 200
    st = stats_r.json()
    assert st["points"] >= 50
    assert st["tests"] >= 1
    assert len(st["history"]) >= 1
    assert st["history"][0]["score"] == 5
