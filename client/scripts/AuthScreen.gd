class_name AuthScreen
extends MarginContainer
## ИС 1–2: регистрация, вход, восстановление пароля с валидацией до отправки.

var app
var mode := "login"
var body: VBoxContainer
var msg: Label
var f_email: LineEdit
var f_name: LineEdit
var f_pass: LineEdit
var f_pass2: LineEdit
var f_code: LineEdit
var f_url: LineEdit
var _recover_step := 1
var _recover_email := ""
var _demo_code := ""


func _init(a) -> void:
	app = a


func _ready() -> void:
	for s in ["left", "right", "top", "bottom"]:
		add_theme_constant_override("margin_" + s, 32)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(sc)
	body = Ui.make_vbox(16)
	sc.add_child(body)
	_build()
	if app != null and app.expired_notice != "":
		Ui.say(msg, app.expired_notice)
		app.expired_notice = ""


func _set_mode(m: String) -> void:
	mode = m
	_recover_step = 1
	_build()


func _build() -> void:
	Ui.clear(body)
	body.add_child(Ui.spacer(30))
	body.add_child(Ui.label("LingLearn", 64, Ui.C_PRIMARY, HORIZONTAL_ALIGNMENT_CENTER))
	body.add_child(Ui.label("Изучайте иностранные языки легко и эффективно", 22, Ui.C_MUTED, HORIZONTAL_ALIGNMENT_CENTER))
	body.add_child(Ui.spacer(20))
	var titles := {"login": "Вход в аккаунт", "register": "Регистрация", "recover": "Восстановление пароля"}
	body.add_child(Ui.label(titles[mode], 34))
	msg = Ui.label("", 20, Ui.C_BAD)
	match mode:
		"login":
			_build_login()
		"register":
			_build_register()
		"recover":
			_build_recover()
	body.add_child(Ui.spacer(10))
	# Адрес сервера уже вшит в сборку; поле нужно только для нестандартной настройки
	var srv := VBoxContainer.new()
	srv.add_theme_constant_override("separation", 10)
	srv.visible = false
	f_url = Ui.input(Api.default_url)
	f_url.text = Api.base_url
	srv.add_child(Ui.label("Адрес сервера API", 18, Ui.C_MUTED))
	srv.add_child(f_url)
	srv.add_child(Ui.button("Сбросить на адрес по умолчанию", func(): f_url.text = Api.default_url, true))
	var toggle := Ui.button("Настройки сервера", Callable(), true)
	toggle.pressed.connect(func(): srv.visible = not srv.visible)
	body.add_child(toggle)
	body.add_child(srv)


func _build_login() -> void:
	f_email = Ui.input("Email (например student@example.com)")
	f_pass = Ui.input("Пароль", true)
	f_pass.text_submitted.connect(func(_t): _login())
	body.add_child(f_email)
	body.add_child(f_pass)
	body.add_child(msg)
	body.add_child(Ui.button("Войти", _login))
	body.add_child(Ui.button("Создать новый аккаунт", _set_mode.bind("register"), true))
	body.add_child(Ui.button("Забыли пароль?", _set_mode.bind("recover"), true))


func _build_register() -> void:
	f_email = Ui.input("Email")
	f_name = Ui.input("Имя пользователя (минимум 2 символа)")
	f_pass = Ui.input("Пароль (минимум 6 символов)", true)
	f_pass2 = Ui.input("Повторите пароль", true)
	for f in [f_email, f_name, f_pass, f_pass2]:
		body.add_child(f)
	body.add_child(msg)
	body.add_child(Ui.button("Зарегистрироваться", _register))
	body.add_child(Ui.button("У меня уже есть аккаунт", _set_mode.bind("login"), true))


func _build_recover() -> void:
	if _recover_step == 1:
		f_email = Ui.input("Email, указанный при регистрации")
		body.add_child(f_email)
		body.add_child(msg)
		body.add_child(Ui.button("Получить код", _recover_request))
	else:
		body.add_child(Ui.label("Код отправлен на %s." % _recover_email, 20, Ui.C_MUTED))
		if _demo_code != "":
			body.add_child(Ui.label("Демо-режим: ваш код подтверждения %s" % _demo_code, 20, Ui.C_OK))
		f_code = Ui.input("Код из письма")
		f_code.text = _demo_code
		f_pass = Ui.input("Новый пароль (минимум 6 символов)", true)
		body.add_child(f_code)
		body.add_child(f_pass)
		body.add_child(msg)
		body.add_child(Ui.button("Сменить пароль", _recover_confirm))
	body.add_child(Ui.button("Назад ко входу", _set_mode.bind("login"), true))


func _apply_url() -> void:
	var u := f_url.text.strip_edges().rstrip("/")
	if u != "":
		Api.base_url = u
		Session.save()


func _finish(d: Dictionary) -> void:
	Api.token = str(d.token)
	Session.token = Api.token
	Session.profile = d.profile
	Session.save()
	app.route()


func _login() -> void:
	_apply_url()
	var email := f_email.text.strip_edges()
	var pw := f_pass.text
	if email == "" or pw == "":
		Ui.say(msg, "Пожалуйста, введите email и пароль")
		return
	if not ("@" in email and "." in email):
		Ui.say(msg, "Введите корректный адрес электронной почты")
		return
	Ui.say(msg, "Вход…", true)
	var r: Dictionary = await Api.post("/login", {"email": email, "password": pw})
	if not r.ok:
		Ui.say(msg, r.error)
		return
	_finish(r.data)


func _register() -> void:
	_apply_url()
	var email := f_email.text.strip_edges()
	var username := f_name.text.strip_edges()
	var pw := f_pass.text
	var pw2 := f_pass2.text

	# Валидация ДО отправки запроса
	if email == "":
		Ui.say(msg, "Введите email")
		return
	if not ("@" in email and "." in email):
		Ui.say(msg, "Введите корректный email (с символом @ и доменом)")
		return
	if username.length() < 2:
		Ui.say(msg, "Имя пользователя должно содержать минимум 2 символа")
		return
	if pw.length() < 6:
		Ui.say(msg, "Пароль должен содержать минимум 6 символов")
		return
	if pw != pw2:
		Ui.say(msg, "Введённые пароли не совпадают")
		return

	Ui.say(msg, "Регистрация…", true)
	var r: Dictionary = await Api.post(
		"/register",
		{
			"email": email,
			"username": username,
			"password": pw,
			"password_confirm": pw2,
		}
	)
	if not r.ok:
		Ui.say(msg, r.error)
		return
	_finish(r.data)


func _recover_request() -> void:
	_apply_url()
	var email := f_email.text.strip_edges()
	if email == "":
		Ui.say(msg, "Введите email")
		return
	if not ("@" in email and "." in email):
		Ui.say(msg, "Введите корректный адрес email")
		return
	Ui.say(msg, "Отправка запроса…", true)
	var r: Dictionary = await Api.post("/recover", {"email": email})
	if not r.ok:
		Ui.say(msg, r.error)
		return
	_recover_email = email
	var dc: Variant = r.data.get("demo_code") if r.data is Dictionary else null
	_demo_code = dc if dc is String else ""
	_recover_step = 2
	_build()


func _recover_confirm() -> void:
	if f_pass.text.length() < 6:
		Ui.say(msg, "Новый пароль должен содержать минимум 6 символов")
		return
	Ui.say(msg, "Смена пароля…", true)
	var r: Dictionary = await Api.post(
		"/recover/confirm",
		{
			"email": _recover_email,
			"code": f_code.text.strip_edges(),
			"password": f_pass.text,
		}
	)
	if not r.ok:
		Ui.say(msg, r.error)
		return
	mode = "login"
	_recover_step = 1
	_build()
	Ui.say(msg, "Пароль успешно изменён! Теперь выполните вход.", true)
