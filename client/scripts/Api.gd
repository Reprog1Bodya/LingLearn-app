extends Node
## Слой API_Integration: HTTP-клиент к серверу LingLearn с версионированием API /api/v1/
## и внешним сервисам (перевод MyMemory). Озвучка — встроенный TTS движка.

signal session_expired()

## Адрес сервера по умолчанию читается из res://server.cfg (его создаёт server/server.py при запуске
## сервера и он вшивается в APK при экспорте). Если файла нет — локальный адрес.
const BUNDLED_CFG := "res://server.cfg"
const FALLBACK_URL := "http://127.0.0.1:8080"

var default_url := FALLBACK_URL
var base_url := FALLBACK_URL
var token := ""


func _init() -> void:
	var cf := ConfigFile.new()
	if cf.load(BUNDLED_CFG) == OK:
		default_url = str(cf.get_value("server", "url", FALLBACK_URL)).rstrip("/")
	base_url = default_url


func _format_url(path: String) -> String:
	if path.begins_with("http://") or path.begins_with("https://"):
		return path
	var clean_path := path
	if not clean_path.begins_with("/"):
		clean_path = "/" + clean_path
	if not clean_path.begins_with("/api/v1") and not clean_path.begins_with("/docs") and not clean_path.begins_with("/health"):
		clean_path = "/api/v1" + clean_path
	return base_url.rstrip("/") + clean_path


func _req(method: int, url_or_path: String, body: Variant = null, auth := true) -> Dictionary:
	var url := _format_url(url_or_path)
	var http := HTTPRequest.new()
	http.timeout = 15.0
	add_child(http)
	var headers := PackedStringArray(["Content-Type: application/json", "Accept: application/json"])
	if auth and token != "":
		headers.append("Authorization: Bearer " + token)
	var payload := ""
	if body != null:
		payload = JSON.stringify(body)
	elif method not in [HTTPClient.METHOD_GET, HTTPClient.METHOD_HEAD]:
		payload = "{}"
	var err := http.request(url, headers, method, payload)
	if err != OK:
		http.queue_free()
		return {"ok": false, "code": 0, "data": {}, "error": "Не удалось отправить запрос (код %d)" % err}
	var res: Array = await http.request_completed
	http.queue_free()
	var code: int = res[1]
	if res[0] != HTTPRequest.RESULT_SUCCESS:
		return {"ok": false, "code": code, "data": {}, "error": "Нет соединения с сервером. Проверьте адрес сервера и сеть."}
	var text: String = (res[3] as PackedByteArray).get_string_from_utf8()
	var parsed: Variant = null
	if text.strip_edges() != "":
		parsed = JSON.parse_string(text)

	var ok := code >= 200 and code < 300
	var err_msg := ""

	if not ok:
		if parsed is Dictionary:
			if parsed.has("detail"):
				var d: Variant = parsed["detail"]
				if d is String:
					err_msg = d
				elif d is Array:
					var parts: Array[String] = []
					for item in d:
						if item is Dictionary and item.has("msg"):
							parts.append(str(item["msg"]))
						else:
							parts.append(str(item))
					err_msg = "; ".join(parts)
				else:
					err_msg = str(d)
			elif parsed.has("error"):
				err_msg = str(parsed["error"])
		if err_msg == "":
			err_msg = "Ошибка сервера (%d)" % code

		# Обработка истечения токена (401)
		if code == 401 and auth and token != "":
			session_expired.emit()

	var res_data: Variant = parsed if parsed != null else {}
	return {"ok": ok, "code": code, "data": res_data, "error": err_msg}


func get_json(path: String) -> Dictionary:
	return await _req(HTTPClient.METHOD_GET, path)


func post(path: String, body: Variant = {}) -> Dictionary:
	return await _req(HTTPClient.METHOD_POST, path, body)


func put(path: String, body: Variant = {}) -> Dictionary:
	return await _req(HTTPClient.METHOD_PUT, path, body)


func delete(path: String) -> Dictionary:
	return await _req(HTTPClient.METHOD_DELETE, path)


## Внешний API перевода (MyMemory). Возвращает {"ok": bool, "text": String, "error": String}.
func translate(text: String, from_lang: String, to_lang: String) -> Dictionary:
	if not Session.use_translate:
		return {"ok": false, "text": "", "error": "Автоперевод отключён в настройках"}
	var url := "https://api.mymemory.translated.net/get?q=%s&langpair=%s%%7C%s" % [text.uri_encode(), from_lang, to_lang]
	var r: Dictionary = await _req(HTTPClient.METHOD_GET, url, null, false)
	if not r.ok:
		return {"ok": false, "text": "", "error": "Сервис перевода временно недоступен"}
	var t := ""
	if r.data is Dictionary and r.data.has("responseData"):
		var rd: Variant = r.data["responseData"]
		if rd is Dictionary and rd.has("translatedText"):
			t = str(rd["translatedText"])
	if t == "":
		return {"ok": false, "text": "", "error": "Перевод не найден"}
	return {"ok": true, "text": t, "error": ""}
