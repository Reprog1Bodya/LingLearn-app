class_name LanguageTab
extends BaseTab
## Вкладка «особенности языка» + проверка произношения (ИС 11).

var _say: LineEdit
var _say_msg: Label


func refresh() -> void:
	loading()
	var r: Dictionary = await Api.get_json("/features?lang=" + Session.lang())
	if not r.ok:
		show_error(r.error)
		return
	Ui.clear(body)
	body.add_child(Ui.label("Особенности языка", 20, Ui.C_MUTED))
	body.add_child(Ui.label(Session.lang_name(), 38, Ui.C_PRIMARY))
	var items: Array = []
	if r.data is Dictionary and r.data.has("items"):
		items = r.data["items"]
	if items.is_empty():
		body.add_child(Ui.label("Для этого языка материалы пока не добавлены.", 22, Ui.C_MUTED))
	for f in items:
		var c := Ui.card(body)
		c.add_child(Ui.label(str(f.get("title", "")), 28, Ui.C_PRIMARY))
		c.add_child(Ui.label(str(f.get("body", "")), 22))
	var p := Ui.card(body, Color(0.93, 0.94, 1.0))
	p.add_child(Ui.label("Проверьте произношение", 26, Ui.C_PRIMARY))
	p.add_child(Ui.label("Введите слово или фразу — приложение озвучит её голосом устройства.", 20, Ui.C_MUTED))
	_say = Ui.input("Слово или фраза")
	p.add_child(_say)
	_say_msg = Ui.label("", 18, Ui.C_BAD)
	p.add_child(_say_msg)
	p.add_child(Ui.button("Озвучить", _speak))


func _speak() -> void:
	var t := _say.text.strip_edges()
	if t == "":
		Ui.say(_say_msg, "Введите текст")
	elif Ui.speak(t, Session.lang()):
		_say_msg.text = ""
	else:
		Ui.say(_say_msg, "Озвучка для этого языка недоступна на устройстве")
