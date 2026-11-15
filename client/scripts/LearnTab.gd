class_name LearnTab
extends BaseTab
## ИС 8–13: тренировки (выбор перевода, карточки, аудирование, правописание).

const KINDS := [
	["translate", "Выбор перевода"],
	["cards", "Карточки слов"],
	["listening", "Аудирование"],
	["spelling", "Правописание"],
]
const ARTICLES := ["der", "die", "das", "el", "la", "los", "las", "the", "a", "an"]

var dicts: Array = []
var sel_idx := 0
var opt: OptionButton
var cur_dict := 0
var kind := "translate"
var questions: Array = []
var idx := 0
var score := 0
var answers := {}
var opt_buttons: Array = []
var spell: LineEdit
var speak_msg: Label
var card_ans: Label
var reveal_btn: Button
var _answered := false


func refresh() -> void:
	loading()
	var pr: Dictionary = await Api.get_json("/profile")
	if pr.ok:
		Session.profile = pr.data
	var r: Dictionary = await Api.get_json("/dictionaries?lang=%s&goal=%s" % [Session.lang(), Session.goal()])
	if not r.ok:
		show_error(r.error)
		return
	dicts = []
	if r.data is Dictionary and r.data.has("items"):
		for d in r.data["items"]:
			if int(d.get("added", 0)) == 1:
				dicts.append(d)
	_menu()


func _menu() -> void:
	Ui.clear(body)
	var p: Dictionary = Session.profile
	var hero := Ui.card(body, Ui.C_PRIMARY)
	hero.add_child(Ui.label("Привет, %s!" % str(p.get("username", "")), 34, Color.WHITE))
	hero.add_child(Ui.label("Серия: %d дн. · Очки: %d · Язык: %s" % [int(p.get("streak", 0)), int(p.get("points", 0)), Session.lang_name()], 22, Color(1, 1, 1, 0.85)))
	if dicts.is_empty():
		body.add_child(Ui.label("У вас пока нет добавленных словарей.", 24))
		body.add_child(Ui.button("Подобрать словари", func(): app.go(SetupScreen.new(app))))
		return
	body.add_child(Ui.label("Словарь для тренировки", 22, Ui.C_MUTED))
	opt = OptionButton.new()
	opt.custom_minimum_size = Vector2(0, 64)
	for d in dicts:
		opt.add_item("%s (%d)" % [d.title, int(d.cnt)])
	sel_idx = clampi(sel_idx, 0, dicts.size() - 1)
	opt.select(sel_idx)
	opt.item_selected.connect(_on_sel)
	body.add_child(opt)
	body.add_child(Ui.label("Выберите тип тренировки", 22, Ui.C_MUTED))
	# Плитки 2×2 делят всё свободное место по высоте — верх и нижняя панель больше не «разъезжаются»
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	body.add_child(grid)
	for k in KINDS:
		var b := Ui.button(k[1], _start.bind(k[0]))
		b.custom_minimum_size = Vector2(0, 160)
		b.size_flags_vertical = Control.SIZE_EXPAND_FILL
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.add_theme_font_size_override("font_size", 28)
		grid.add_child(b)


func _on_sel(i: int) -> void:
	sel_idx = i


func _start(k: String) -> void:
	kind = k
	cur_dict = int(dicts[sel_idx].id)
	loading()
	var r: Dictionary = await Api.get_json("/test?dict_id=%d&n=8" % cur_dict)
	if not r.ok:
		show_error(r.error, _menu)
		return
	questions = []
	if r.data is Dictionary and r.data.has("questions"):
		questions = r.data["questions"]
	idx = 0
	score = 0
	answers = {}
	_show_q()


func _show_q() -> void:
	Ui.clear(body)
	opt_buttons = []
	_answered = false
	if idx >= questions.size():
		_finish()
		return
	var q: Dictionary = questions[idx]
	body.add_child(Ui.label("Вопрос %d из %d" % [idx + 1, questions.size()], 20, Ui.C_MUTED))
	var pb := ProgressBar.new()
	pb.max_value = questions.size()
	pb.value = idx
	pb.show_percentage = false
	pb.custom_minimum_size = Vector2(0, 14)
	body.add_child(pb)
	var c := Ui.card(body)
	var ctr := HORIZONTAL_ALIGNMENT_CENTER
	match kind:
		"translate":
			c.add_child(Ui.label("Выберите перевод", 20, Ui.C_MUTED, ctr))
			c.add_child(Ui.label(str(q.word), 44, Ui.C_PRIMARY, ctr))
			c.add_child(Ui.label(str(q.transcription), 22, Ui.C_MUTED, ctr))
			_options(q)
		"listening":
			c.add_child(Ui.label("Прослушайте слово и выберите перевод", 22, Ui.C_MUTED, ctr))
			c.add_child(Ui.button("Прослушать", _play.bind(str(q.word))))
			speak_msg = Ui.label("", 18, Ui.C_BAD, ctr)
			c.add_child(speak_msg)
			_options(q)
			_play(str(q.word))
		"spelling":
			c.add_child(Ui.label("Напишите слово на изучаемом языке", 20, Ui.C_MUTED, ctr))
			c.add_child(Ui.label(str(q.answer), 40, Ui.C_PRIMARY, ctr))
			spell = Ui.input("Ваш ответ")
			spell.text_submitted.connect(_on_spell_submit.bind(q))
			body.add_child(spell)
			body.add_child(Ui.button("Проверить", _check_spell.bind(q)))
		"cards":
			c.add_child(Ui.label(str(q.word), 44, Ui.C_PRIMARY, ctr))
			c.add_child(Ui.label(str(q.transcription), 22, Ui.C_MUTED, ctr))
			card_ans = Ui.label("", 32, Ui.C_OK, ctr)
			c.add_child(card_ans)
			reveal_btn = Ui.button("Показать перевод", _reveal.bind(q))
			body.add_child(reveal_btn)
	body.add_child(Ui.button("Прервать тренировку", _menu, true))


func _options(q: Dictionary) -> void:
	for o in q.options:
		var b := Ui.button(str(o), Callable(), true)
		b.pressed.connect(_pick.bind(q, str(o)))
		opt_buttons.append(b)
		body.add_child(b)


func _play(text: String) -> void:
	if not Ui.speak(text, Session.lang()):
		Ui.say(speak_msg, "Озвучка недоступна на этом устройстве")


func _pick(q: Dictionary, choice: String) -> void:
	if _answered:
		return
	var ok := choice == str(q.answer)
	for b: Button in opt_buttons:
		b.disabled = true
		if b.text == str(q.answer):
			b.add_theme_stylebox_override("disabled", Ui.box(Ui.C_OK, 14, 14))
		elif b.text == choice:
			b.add_theme_stylebox_override("disabled", Ui.box(Ui.C_BAD, 14, 14))
	_mark(q, ok, str(q.answer))


func _strip_article(s: String) -> String:
	var parts := s.split(" ", false)
	if parts.size() > 1 and parts[0] in ARTICLES:
		return " ".join(parts.slice(1))
	return s


func _on_spell_submit(_t: String, q: Dictionary) -> void:
	_check_spell(q)


func _check_spell(q: Dictionary) -> void:
	if _answered:
		return
	var typed := spell.text.strip_edges().to_lower()
	var word := str(q.word).to_lower()
	var ok := typed != "" and (typed == word or typed == _strip_article(word))
	spell.editable = false
	_mark(q, ok, str(q.word))


func _reveal(q: Dictionary) -> void:
	card_ans.text = str(q.answer)
	reveal_btn.queue_free()
	var row := Ui.hbox(body)
	row.add_child(Ui.button("Не знаю", _card_mark.bind(q, false), true))
	row.add_child(Ui.button("Знаю", _card_mark.bind(q, true)))


func _card_mark(q: Dictionary, ok: bool) -> void:
	_answered = true
	answers[str(int(q.word_id))] = ok
	if ok:
		score += 1
	idx += 1
	_show_q()


func _mark(q: Dictionary, ok: bool, shown: String) -> void:
	if _answered:
		return
	_answered = true
	answers[str(int(q.word_id))] = ok
	if ok:
		score += 1
	var text := "Верно!" if ok else "Неверно. Правильный ответ: " + shown
	body.add_child(Ui.label(text, 24, Ui.C_OK if ok else Ui.C_BAD, HORIZONTAL_ALIGNMENT_CENTER))
	body.add_child(Ui.button("Далее" if idx + 1 < questions.size() else "Завершить", _next))


func _next() -> void:
	idx += 1
	_show_q()


func _finish() -> void:
	Ui.clear(body)
	body.add_child(Ui.label("Сохраняем результат…", 22, Ui.C_MUTED))
	var r: Dictionary = await Api.post("/test/result", {
		"dict_id": cur_dict, "kind": kind, "score": score,
		"total": questions.size(), "answers": answers,
	})
	Ui.clear(body)
	var c := Ui.card(body)
	var ctr := HORIZONTAL_ALIGNMENT_CENTER
	c.add_child(Ui.label("Тренировка завершена", 34, Ui.C_PRIMARY, ctr))
	c.add_child(Ui.label("Результат: %d из %d" % [score, questions.size()], 30, Ui.C_TEXT, ctr))
	if r.ok:
		c.add_child(Ui.label("+%d очков · серия: %d дн." % [int(r.data.get("points", 0)), int(r.data.get("streak", 0))], 22, Ui.C_MUTED, ctr))
	else:
		c.add_child(Ui.label("Не удалось сохранить результат: " + r.error, 20, Ui.C_BAD, ctr))
	body.add_child(Ui.button("Ещё раз", _start.bind(kind)))
	body.add_child(Ui.button("В меню", refresh, true))
