class_name BaseTab
extends MarginContainer
## Базовая вкладка главного экрана: прокручиваемое тело, состояния загрузки, ошибок и успеха.

var app
var body: VBoxContainer
var _status_lbl: Label


func _ready() -> void:
	for s in ["left", "right", "top", "bottom"]:
		add_theme_constant_override("margin_" + s, 16)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(sc)
	body = Ui.make_vbox(14)
	# Тело растягивается на всю высоту вкладки: контент не «прилипает» к верху,
	# а между шапкой и нижней панелью не остаётся пустого провала
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.add_child(body)


func refresh() -> void:
	pass


func loading() -> void:
	Ui.clear(body)
	body.add_child(Ui.label("Загрузка данных…", 22, Ui.C_MUTED))


func show_error(text: String, retry := Callable()) -> void:
	Ui.clear(body)
	body.add_child(Ui.label(text, 22, Ui.C_BAD))
	body.add_child(Ui.button("Повторить", retry if retry.is_valid() else refresh))
