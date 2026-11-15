class_name ProfileTab
extends BaseTab
## ИС 3–4: профиль, настройки (дневная цель, уведомления), статистика и выход из аккаунта.

const KIND_NAMES := {
	"translate": "Выбор перевода",
	"cards": "Карточки слов",
	"listening": "Аудирование",
	"spelling": "Правописание",
}

var f_name: LineEdit
var f_goal: SpinBox
var f_notif: CheckButton
var _msg: Label


func refresh() -> void:
	loading()
	var pr: Dictionary = await Api.get_json("/profile")
	var st: Dictionary = await Api.get_json("/stats")
	if not pr.ok or not st.ok:
		show_error(pr.error if not pr.ok else st.error)
		return

	if pr.data is Dictionary:
		Session.profile = pr.data
	else:
		Session.profile = {}

	var p: Dictionary = Session.profile
	var s: Dictionary = {}
	if st.data is Dictionary:
		s = st.data

	Ui.clear(body)
	body.add_child(Ui.label("Профиль пользователя", 36, Ui.C_PRIMARY))
	body.add_child(Ui.label("Email: " + str(p.get("email", "")), 20, Ui.C_MUTED))

	var c := Ui.card(body)
	c.add_child(Ui.label("Настройки обучения", 26, Ui.C_PRIMARY))

	f_name = Ui.input("Имя пользователя (минимум 2 символа)")
	f_name.text = str(p.get("username", ""))
	c.add_child(f_name)

	c.add_child(Ui.label("Дневная цель (слов в день, от 1 до 100):", 20, Ui.C_MUTED))
	f_goal = SpinBox.new()
	f_goal.min_value = 1
	f_goal.max_value = 100
	f_goal.value = int(p.get("daily_goal", 10))
	f_goal.custom_minimum_size = Vector2(0, 60)
	c.add_child(f_goal)

	f_notif = CheckButton.new()
	f_notif.text = "Напоминания о занятиях"
	f_notif.button_pressed = int(p.get("notifications", 1)) == 1
	c.add_child(f_notif)

	_msg = Ui.label("", 20, Ui.C_BAD)
	c.add_child(_msg)
	c.add_child(Ui.button("Сохранить настройки", _save))

	# Статистика
	var sc := Ui.card(body)
	sc.add_child(Ui.label("Ваш прогресс", 26, Ui.C_PRIMARY))
	var acc := 0
	if int(s.get("questions", 0)) > 0:
		acc = int(round(100.0 * float(s.get("correct", 0)) / float(s.get("questions", 1))))

	sc.add_child(Ui.label("Изучаемый язык: %s" % Session.lang_name(), 22))
	sc.add_child(Ui.label("Серия непрерывных занятий: %d дн." % int(s.get("streak", 0)), 22))
	sc.add_child(Ui.label("Набранные очки опыта: %d" % int(s.get("points", 0)), 22))
	sc.add_child(Ui.label("Слов выучено: %d из %d" % [int(s.get("learned", 0)), int(s.get("words", 0))], 22))
	sc.add_child(Ui.label("Всего тренировок: %d · Точность ответов: %d%%" % [int(s.get("tests", 0)), acc], 22))

	var hist: Array = []
	if s.has("history") and s["history"] is Array:
		hist = s["history"]

	if not hist.is_empty():
		sc.add_child(Ui.spacer(10))
		sc.add_child(Ui.label("История последних тренировок", 22, Ui.C_PRIMARY))
		for h in hist:
			var dt: String = Time.get_datetime_string_from_unix_time(int(h.get("created", 0)), true)
			var kind_raw: String = str(h.get("kind", ""))
			var kind_str: String = str(KIND_NAMES.get(kind_raw, kind_raw))
			sc.add_child(Ui.label("%s — %s: результат %d/%d" % [dt, kind_str, int(h.get("score", 0)), int(h.get("total", 0))], 18, Ui.C_MUTED))

	body.add_child(Ui.spacer(10))
	body.add_child(Ui.button("Сменить язык и цель обучения", func(): app.go(SetupScreen.new(app)), true))
	body.add_child(Ui.button("Выйти из аккаунта", func(): app.logout(), true))


func _save() -> void:
	var n := f_name.text.strip_edges()
	if n.length() < 2:
		Ui.say(_msg, "Имя пользователя должно содержать не менее 2 символов")
		return
	if int(f_goal.value) < 1 or int(f_goal.value) > 100:
		Ui.say(_msg, "Дневная цель должна быть от 1 до 100 слов")
		return

	Ui.say(_msg, "Сохранение…", true)
	var r: Dictionary = await Api.put(
		"/profile",
		{
			"username": n,
			"daily_goal": int(f_goal.value),
			"notifications": 1 if f_notif.button_pressed else 0,
		}
	)
	if r.ok:
		Session.profile = r.data
		Ui.say(_msg, "Настройки успешно сохранены!", true)
	else:
		Ui.say(_msg, r.error)
