class_name AppRoot
extends Control
## Корневой узел: переключает экраны (Авторизация → Настройка → Главный).

var current: Control
var expired_notice := ""


func _ready() -> void:
	theme = Ui.make_theme()
	var bg := ColorRect.new()
	bg.color = Ui.C_BG
	add_child(bg)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	Api.session_expired.connect(_on_session_expired)

	Session.load_saved()
	if Session.token != "":
		Api.token = Session.token
		var r: Dictionary = await Api.get_json("/profile")
		if r.ok:
			Session.profile = r.data
			route()
			return
		Session.clear()
	go(AuthScreen.new(self))


func _on_session_expired() -> void:
	expired_notice = "Срок действия сессии истёк. Пожалуйста, выполните вход снова."
	Session.clear()
	var auth := AuthScreen.new(self)
	go(auth)
	if is_instance_valid(auth) and auth.msg:
		Ui.say(auth.msg, expired_notice)


func go(s: Control) -> void:
	if current != null and is_instance_valid(current):
		current.queue_free()
	current = s
	add_child(s)
	s.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func route() -> void:
	if Session.lang() == "" or Session.goal() == "":
		go(SetupScreen.new(self))
	else:
		go(HomeScreen.new(self))


func logout() -> void:
	if Session.token != "":
		await Api.post("/logout")  # отзыв токена на сервере
	Session.clear()
	go(AuthScreen.new(self))
