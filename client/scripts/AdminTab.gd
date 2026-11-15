class_name AdminTab
extends BaseTab
## ИС 17–21: Панель администратора: аналитика, управление словарями, словами, пользователями.

var _lang_codes: Array = []
var _goal_codes: Array = []
var _dict_ids: Array = []
var o_lang: OptionButton
var o_goal: OptionButton
var o_dict: OptionButton
var f_dtitle: LineEdit
var f_ddescr: LineEdit
var f_word: LineEdit
var f_tr: LineEdit
var f_ts: LineEdit
var f_ex: LineEdit
var f_url: LineEdit
var _msg: Label


func refresh() -> void:
	loading()
	var a: Dictionary = await Api.get_json("/admin/analytics")
	var u: Dictionary = await Api.get_json("/admin/users")
	var l: Dictionary = await Api.get_json("/languages")
	var g: Dictionary = await Api.get_json("/goals")
	var d: Dictionary = await Api.get_json("/dictionaries")
	for r in [a, u, l, g, d]:
		if not r.ok:
			show_error(r.error)
			return

	Ui.clear(body)
	body.add_child(Ui.label("Панель администратора", 36, Ui.C_PRIMARY))
	_msg = Ui.label("", 20, Ui.C_BAD)
	body.add_child(_msg)

	# Аналитика платформы
	var c := Ui.card(body)
	c.add_child(Ui.label("Аналитика платформы", 26, Ui.C_PRIMARY))
	var a_data: Dictionary = {}
	if a.data is Dictionary:
		a_data = a.data
	var stat_text := "Пользователей: %d   ·   Словарей: %d   ·   Слов: %d   ·   Тестов: %d" % [
		int(a_data.get("users", 0)),
		int(a_data.get("dictionaries", 0)),
		int(a_data.get("words", 0)),
		int(a_data.get("tests", 0)),
	]
	c.add_child(Ui.label(stat_text, 22))

	# Создание словаря
	var cd := Ui.card(body)
	cd.add_child(Ui.label("Создать системный словарь", 26, Ui.C_PRIMARY))
	o_lang = OptionButton.new()
	o_lang.custom_minimum_size = Vector2(0, 56)
	_lang_codes = []
	var lang_items: Array = []
	if l.data is Dictionary and l.data.has("items"):
		lang_items = l.data["items"]
	for it in lang_items:
		o_lang.add_item("%s (%s)" % [it.get("name"), it.get("code")])
		_lang_codes.append(str(it.get("code")))

	o_goal = OptionButton.new()
	o_goal.custom_minimum_size = Vector2(0, 56)
	_goal_codes = []
	var goal_items: Array = []
	if g.data is Dictionary and g.data.has("items"):
		goal_items = g.data["items"]
	for it in goal_items:
		o_goal.add_item(str(it.get("name")))
		_goal_codes.append(str(it.get("code")))

	f_dtitle = Ui.input("Название словаря *")
	f_ddescr = Ui.input("Описание словаря (необязательно)")
	cd.add_child(Ui.label("Язык словаря:", 18, Ui.C_MUTED))
	cd.add_child(o_lang)
	cd.add_child(Ui.label("Цель изучения:", 18, Ui.C_MUTED))
	cd.add_child(o_goal)
	cd.add_child(f_dtitle)
	cd.add_child(f_ddescr)
	cd.add_child(Ui.button("Создать словарь", _create_dict))

	# Добавление слова в словарь
	var cw := Ui.card(body)
	cw.add_child(Ui.label("Добавить слово в словарь", 26, Ui.C_PRIMARY))
	o_dict = OptionButton.new()
	o_dict.custom_minimum_size = Vector2(0, 56)
	_dict_ids = []
	var dict_items: Array = []
	if d.data is Dictionary and d.data.has("items"):
		dict_items = d.data["items"]
	for it in dict_items:
		o_dict.add_item("%s [%s]" % [it.get("title"), it.get("lang")])
		_dict_ids.append(int(it.get("id")))

	f_word = Ui.input("Слово *")
	f_tr = Ui.input("Перевод *")
	f_ts = Ui.input("Транскрипция (необязательно)")
	f_ex = Ui.input("Пример употребления (необязательно)")
	cw.add_child(Ui.label("Целевой словарь:", 18, Ui.C_MUTED))
	cw.add_child(o_dict)
	for f in [f_word, f_tr, f_ts, f_ex]:
		cw.add_child(f)
	cw.add_child(Ui.button("Добавить слово", _create_word))

	# Интеграции
	var ci := Ui.card(body)
	ci.add_child(Ui.label("Интеграции и адрес API", 26, Ui.C_PRIMARY))
	f_url = Ui.input("http://127.0.0.1:8080")
	f_url.text = Api.base_url
	ci.add_child(f_url)
	var cb := CheckButton.new()
	cb.text = "Автоперевод слов через внешний сервис (MyMemory API)"
	cb.button_pressed = Session.use_translate
	cb.toggled.connect(func(on: bool):
		Session.use_translate = on
		Session.save()
	)
	ci.add_child(cb)
	ci.add_child(Ui.button("Применить адрес API", _apply_url, true))

	# Пользователи
	var cu := Ui.card(body)
	cu.add_child(Ui.label("Зарегистрированные пользователи", 26, Ui.C_PRIMARY))
	var user_items: Array = []
	if u.data is Dictionary and u.data.has("items"):
		user_items = u.data["items"]
	for us in user_items:
		var row := Ui.hbox(cu)
		var info_text := "%s (%s)\n%s" % [us.get("username"), us.get("role"), us.get("email")]
		row.add_child(Ui.label(info_text, 18))
		if int(us.get("id", -1)) != int(Session.profile.get("id", -1)):
			var b := Ui.button("Удалить", Callable(), true)
			b.size_flags_horizontal = Control.SIZE_SHRINK_END
			b.pressed.connect(_confirm_delete_user.bind(int(us.get("id")), str(us.get("username"))))
			row.add_child(b)


func _create_dict() -> void:
	var t := f_dtitle.text.strip_edges()
	if t == "":
		Ui.say(_msg, "Введите название словаря")
		return
	if _lang_codes.is_empty() or _goal_codes.is_empty():
		Ui.say(_msg, "Не удалось определить язык или цель")
		return

	Ui.say(_msg, "Создание словаря…", true)
	var r: Dictionary = await Api.post("/admin/dictionaries", {
		"lang": _lang_codes[o_lang.selected],
		"goal": _goal_codes[o_goal.selected],
		"title": t,
		"description": f_ddescr.text.strip_edges(),
	})
	if r.ok:
		refresh()
		Ui.say(_msg, "Словарь успешно создан!", true)
	else:
		Ui.say(_msg, r.error)


func _create_word() -> void:
	if _dict_ids.is_empty():
		Ui.say(_msg, "Сначала создайте хотя бы один словарь")
		return
	var w := f_word.text.strip_edges()
	var tr := f_tr.text.strip_edges()
	if w == "" or tr == "":
		Ui.say(_msg, "Слово и перевод обязательны для заполнения")
		return

	Ui.say(_msg, "Добавление слова…", true)
	var r: Dictionary = await Api.post("/admin/words", {
		"dict_id": _dict_ids[o_dict.selected],
		"word": w,
		"translation": tr,
		"transcription": f_ts.text.strip_edges(),
		"example": f_ex.text.strip_edges(),
	})
	if r.ok:
		for f in [f_word, f_tr, f_ts, f_ex]:
			f.text = ""
		Ui.say(_msg, "Слово успешно добавлено в словарь!", true)
	else:
		Ui.say(_msg, r.error)


func _confirm_delete_user(uid: int, uname: String) -> void:
	Ui.clear(body)
	var c := Ui.card(body)
	c.add_child(Ui.label("Вы действительно хотите удалить пользователя '%s' (ID %d)?" % [uname, uid], 24, Ui.C_BAD))
	c.add_child(Ui.label("Все данные и статистика пользователя будут безвозвратно удалены.", 18, Ui.C_MUTED))
	var row := Ui.hbox(c)
	var del_btn := Ui.button("Да, удалить", func(): _execute_delete_user(uid))
	del_btn.add_theme_color_override("font_color", Ui.C_BAD)
	row.add_child(del_btn)
	row.add_child(Ui.button("Отмена", refresh, true))


func _execute_delete_user(uid: int) -> void:
	var r: Dictionary = await Api.delete("/admin/users/%d" % uid)
	if r.ok:
		refresh()
		Ui.say(_msg, "Пользователь успешно удалён", true)
	else:
		Ui.say(_msg, r.error)


func _apply_url() -> void:
	var u := f_url.text.strip_edges().rstrip("/")
	if u != "":
		Api.base_url = u
		Session.save()
		Ui.say(_msg, "Адрес сервера API успешно обновлён", true)
