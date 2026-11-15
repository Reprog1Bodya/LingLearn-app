class_name SetupScreen
extends MarginContainer
## ИС 5: выбор языка → цель изучения → подбор словарей.

var app
var step := 1
var chosen_lang := ""
var chosen_goal := ""
var body: VBoxContainer
var msg: Label
var _gen := 0
var _dicts: Array = []


func _init(a) -> void:
	app = a


func _ready() -> void:
	for s in ["left", "right", "top", "bottom"]:
		add_theme_constant_override("margin_" + s, 28)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(sc)
	body = Ui.make_vbox(16)
	sc.add_child(body)
	chosen_lang = Session.lang()
	chosen_goal = Session.goal()
	_build()


func _build() -> void:
	_gen += 1
	var g := _gen
	Ui.clear(body)
	msg = Ui.label("", 20, Ui.C_BAD)
	match step:
		1:
			await _step_lang(g)
		2:
			await _step_goal(g)
		3:
			await _step_dicts(g)


func _fail(text: String) -> void:
	body.add_child(Ui.label(text, 22, Ui.C_BAD))
	body.add_child(Ui.button("Повторить", _build))


func _step_lang(g: int) -> void:
	body.add_child(Ui.label("Шаг 1 из 3", 20, Ui.C_MUTED))
	body.add_child(Ui.label("Какой язык вы хотите изучать?", 34))
	var r: Dictionary = await Api.get_json("/languages")
	if g != _gen:
		return
	if not r.ok:
		_fail(r.error)
		return
	var lang_items: Array = []
	if r.data is Dictionary and r.data.has("items"):
		lang_items = r.data["items"]
	for l in lang_items:
		Session.lang_names[str(l.code)] = str(l.name)
		var title := "%s — %s" % [l.native, l.name]
		if int(l.niche) == 1:
			title += "  · редкий язык"
		body.add_child(Ui.button(title, _pick_lang.bind(str(l.code)), str(l.code) != chosen_lang))
	if Session.lang() != "":
		body.add_child(Ui.button("Отмена", Callable(app, "route"), true))


func _goto(n: int) -> void:
	step = n
	_build()


func _pick_lang(code: String) -> void:
	chosen_lang = code
	step = 2
	_build()


func _step_goal(g: int) -> void:
	body.add_child(Ui.label("Шаг 2 из 3", 20, Ui.C_MUTED))
	body.add_child(Ui.label("Для чего вам нужен язык?", 34))
	body.add_child(msg)
	var r: Dictionary = await Api.get_json("/goals")
	if g != _gen:
		return
	if not r.ok:
		_fail(r.error)
		return
	var goal_items: Array = []
	if r.data is Dictionary and r.data.has("items"):
		goal_items = r.data["items"]
	for it in goal_items:
		var c := Ui.card(body)
		c.add_child(Ui.label(str(it.name), 28, Ui.C_PRIMARY))
		c.add_child(Ui.label(str(it.descr), 20, Ui.C_MUTED))
		c.add_child(Ui.button("Выбрать" if str(it.code) != chosen_goal else "Выбрано ✓", _pick_goal.bind(str(it.code)), str(it.code) != chosen_goal))
	body.add_child(Ui.button("← Назад", _goto.bind(1), true))


func _pick_goal(code: String) -> void:
	chosen_goal = code
	var r: Dictionary = await Api.put("/profile", {"language": chosen_lang, "goal": chosen_goal})
	if not r.ok:
		Ui.say(msg, r.error)
		return
	Session.profile = r.data
	step = 3
	_build()


func _step_dicts(g: int) -> void:
	body.add_child(Ui.label("Шаг 3 из 3", 20, Ui.C_MUTED))
	body.add_child(Ui.label("Подбор словарей", 34))
	body.add_child(Ui.label("Словари со звёздочкой ★ подходят под выбранную цель. Добавьте те, что хотите учить.", 20, Ui.C_MUTED))
	var r: Dictionary = await Api.get_json("/dictionaries?lang=%s&goal=%s" % [chosen_lang, chosen_goal])
	if g != _gen:
		return
	if not r.ok:
		_fail(r.error)
		return
	_dicts = []
	if r.data is Dictionary and r.data.has("items"):
		_dicts = r.data["items"]
	if _dicts.is_empty():
		body.add_child(Ui.label("Для этого языка пока нет словарей.", 22, Ui.C_MUTED))
	body.add_child(Ui.button("Добавить все рекомендуемые", _add_recommended, true))
	for d in _dicts:
		Ui.dict_card(body, d, _toggle)
	body.add_child(msg)
	body.add_child(Ui.button("Начать обучение", _finish))
	body.add_child(Ui.button("← Назад", _goto.bind(2), true))


func _toggle(d: Dictionary, btn: Button) -> void:
	var err: String = await Ui.toggle_dict(d, btn)
	if err != "":
		Ui.say(msg, err)


func _add_recommended() -> void:
	for d in _dicts:
		if d.get("recommended", false) and int(d.get("added", 0)) == 0:
			await Api.post("/dictionaries/%d/add" % int(d.id), {})
	_build()


func _finish() -> void:
	var any := false
	for d in _dicts:
		if int(d.get("added", 0)) == 1:
			any = true
	if not any:
		Ui.say(msg, "Добавьте хотя бы один словарь")
		return
	app.route()
