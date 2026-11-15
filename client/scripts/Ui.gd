class_name Ui
extends RefCounted
## Слой UI_Layer: тема и фабрики виджетов для мобильного интерфейса Godot 4.

const C_PRIMARY := Color(0.31, 0.275, 0.898)
const C_PRIMARY_DARK := Color(0.216, 0.188, 0.639)
const C_PRIMARY_LIGHT := Color(0.506, 0.549, 0.973)
const C_BG := Color(0.957, 0.965, 0.984)
const C_TEXT := Color(0.122, 0.161, 0.216)
const C_MUTED := Color(0.42, 0.447, 0.502)
const C_OK := Color(0.086, 0.639, 0.29)
const C_BAD := Color(0.863, 0.149, 0.149)
const C_WARN := Color(0.89, 0.55, 0.1)
const C_BORDER := Color(0.82, 0.835, 0.859)


static func box(color: Color, radius := 16, pad := 16, border := 0, border_color := Color.TRANSPARENT) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.set_corner_radius_all(radius)
	s.set_content_margin_all(pad)
	if border > 0:
		s.set_border_width_all(border)
		s.border_color = border_color
	return s


static func make_theme() -> Theme:
	var t := Theme.new()
	t.default_font_size = 24
	t.set_color("font_color", "Label", C_TEXT)
	t.set_stylebox("normal", "Button", box(C_PRIMARY, 14, 14))
	t.set_stylebox("hover", "Button", box(C_PRIMARY_LIGHT, 14, 14))
	t.set_stylebox("pressed", "Button", box(C_PRIMARY_DARK, 14, 14))
	t.set_stylebox("disabled", "Button", box(Color(0.6, 0.62, 0.68), 14, 14))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_disabled_color", "font_hover_pressed_color"]:
		t.set_color(c, "Button", Color.WHITE)
	for tp in ["CheckButton", "CheckBox"]:
		for st in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
			t.set_stylebox(st, tp, StyleBoxEmpty.new())
		for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
			t.set_color(c, tp, C_TEXT)
	t.set_stylebox("normal", "LineEdit", box(Color.WHITE, 12, 14, 2, C_BORDER))
	t.set_stylebox("focus", "LineEdit", box(Color.WHITE, 12, 14, 2, C_PRIMARY))
	t.set_stylebox("read_only", "LineEdit", box(Color(0.94, 0.94, 0.96), 12, 14, 2, C_BORDER))
	t.set_color("font_color", "LineEdit", C_TEXT)
	t.set_color("font_placeholder_color", "LineEdit", C_MUTED)
	t.set_color("caret_color", "LineEdit", C_PRIMARY)
	t.set_stylebox("panel", "TabContainer", StyleBoxEmpty.new())
	t.set_stylebox("tabbar_background", "TabContainer", box(Color.WHITE, 0, 0, 1, C_BORDER))
	t.set_stylebox("tab_selected", "TabContainer", box(Color(0.91, 0.92, 1.0), 12, 10))
	t.set_stylebox("tab_unselected", "TabContainer", box(Color.WHITE, 12, 10))
	t.set_stylebox("tab_hovered", "TabContainer", box(Color(0.95, 0.96, 1.0), 12, 10))
	t.set_color("font_selected_color", "TabContainer", C_PRIMARY)
	t.set_color("font_unselected_color", "TabContainer", C_MUTED)
	t.set_color("font_hovered_color", "TabContainer", C_PRIMARY)
	t.set_font_size("font_size", "TabContainer", 20)
	return t


static func label(text: String, size := 24, color := C_TEXT, align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.horizontal_alignment = align
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


static func input(placeholder: String, secret := false) -> LineEdit:
	var e := LineEdit.new()
	e.placeholder_text = placeholder
	e.secret = secret
	e.custom_minimum_size = Vector2(0, 64)
	return e


static func button(text: String, cb := Callable(), secondary := false) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 56)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if cb.is_valid():
		b.pressed.connect(cb)
	if secondary:
		b.add_theme_stylebox_override("normal", box(Color.WHITE, 14, 14, 2, C_PRIMARY))
		b.add_theme_stylebox_override("hover", box(Color(0.93, 0.94, 1.0), 14, 14, 2, C_PRIMARY))
		b.add_theme_stylebox_override("pressed", box(Color(0.87, 0.89, 1.0), 14, 14, 2, C_PRIMARY))
		for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
			b.add_theme_color_override(c, C_PRIMARY)
	return b


static func make_vbox(sep := 14) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", sep)
	return v


static func hbox(parent: Node, sep := 10) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_theme_constant_override("separation", sep)
	parent.add_child(h)
	return h


static func card(parent: Node, color := Color.WHITE) -> VBoxContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", box(color, 18, 18, 1, C_BORDER))
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(p)
	var v := make_vbox(10)
	p.add_child(v)
	return v


static func spacer(h: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	return c


static func clear(n: Node) -> void:
	for c in n.get_children():
		n.remove_child(c)
		c.queue_free()


static func say(l: Label, text: String, ok := false) -> void:
	if not is_instance_valid(l):
		return
	l.text = text
	l.add_theme_color_override("font_color", C_OK if ok else C_BAD)


## Озвучка слова встроенным TTS движка (ИС 11).
static func speak(text: String, lang: String) -> bool:
	if not DisplayServer.has_feature(DisplayServer.FEATURE_TEXT_TO_SPEECH):
		return false
	var voices: PackedStringArray = DisplayServer.tts_get_voices_for_language(lang)
	if voices.is_empty():
		return false
	DisplayServer.tts_stop()
	DisplayServer.tts_speak(text, voices[0])
	return true


## Пагинация: панель навигации по страницам (Кейс 1: загрузка частями*)
static func pagination_bar(parent: Node, page: int, total_pages: int, total_items: int, on_prev: Callable, on_next: Callable) -> HBoxContainer:
	var row := hbox(parent, 10)
	var prev_btn := button("← Назад", on_prev, true)
	prev_btn.disabled = page <= 1
	prev_btn.custom_minimum_size = Vector2(120, 48)
	row.add_child(prev_btn)

	var info_text := "Стр. %d из %d (%d зап.)" % [page, maxi(1, total_pages), total_items]
	var info_lbl := label(info_text, 18, C_MUTED, HORIZONTAL_ALIGNMENT_CENTER)
	row.add_child(info_lbl)

	var next_btn := button("Вперёд →", on_next, true)
	next_btn.disabled = page >= total_pages
	next_btn.custom_minimum_size = Vector2(120, 48)
	row.add_child(next_btn)
	return row


## Переключение добавления словаря в коллекцию
static func toggle_dict(d: Dictionary, btn: Button) -> String:
	var added := int(d.get("added", 0)) == 1
	var path := "/dictionaries/%d/add" % int(d.id)
	var r: Dictionary
	if added:
		r = await Api.delete(path)
	else:
		r = await Api.post(path, {})
	if not r.ok:
		return r.error
	d["added"] = 0 if added else 1
	if is_instance_valid(btn):
		btn.text = dict_btn_text(d)
	return ""


static func dict_btn_text(d: Dictionary) -> String:
	return "Убрать из моих" if int(d.get("added", 0)) == 1 else "Добавить в мои"


static func dict_card(parent: Node, d: Dictionary, on_toggle: Callable, on_open := Callable()) -> void:
	var c := card(parent)
	var title := str(d.get("title", ""))
	if d.get("recommended", false):
		title += "  ★"
	c.add_child(label(title, 28, C_PRIMARY))
	var descr := str(d.get("descr", ""))
	if descr != "":
		c.add_child(label(descr, 20, C_MUTED))
	var meta := "Слов: %d" % int(d.get("cnt", 0))
	if d.get("recommended", false):
		meta += " · подходит под вашу цель"
	c.add_child(label(meta, 20, C_MUTED))
	var row := hbox(c)
	if on_open.is_valid():
		row.add_child(button("Открыть слова", on_open.bind(d), true))
	var tb := button(dict_btn_text(d))
	tb.pressed.connect(on_toggle.bind(d, tb))
	row.add_child(tb)


## Интерактивная карточка слова: просмотр, озвучка, статус, редактирование, удаление (CRUD)
static func word_card_full(
	parent: Node,
	w: Dictionary,
	lang: String,
	on_edit: Callable = Callable(),
	on_delete: Callable = Callable(),
	on_status_change: Callable = Callable()
) -> VBoxContainer:
	var c := card(parent)
	var head := hbox(c)
	head.add_child(label(str(w.get("word", "")), 32, C_PRIMARY))

	var is_learned := int(w.get("learned", 0)) == 1
	var badge_text := "✓ Выучено" if is_learned else "В изучении"
	var badge_col := C_OK if is_learned else C_WARN
	var badge := label(badge_text, 18, badge_col, HORIZONTAL_ALIGNMENT_RIGHT)
	head.add_child(badge)

	var ts := str(w.get("transcription", ""))
	if ts != "":
		c.add_child(label(ts, 20, C_MUTED))
	c.add_child(label(str(w.get("translation", "")), 26))

	var ex := str(w.get("example", ""))
	if ex != "":
		c.add_child(label("Пример: " + ex, 18, C_MUTED))

	# Ряд действий 1: Озвучить и Переключить статус
	var row1 := hbox(c)
	var sb := button("Озвучить", Callable(), true)
	sb.pressed.connect(_on_speak.bind(str(w.get("word", "")), lang, sb))
	row1.add_child(sb)

	var lb := button("Отметить выученным" if not is_learned else "Вернуть в изучение")
	lb.pressed.connect(func():
		var nv := 0 if int(w.get("learned", 0)) == 1 else 1
		lb.disabled = true
		var r: Dictionary = await Api.post("/words/%d/learned" % int(w.id), {"learned": nv == 1})
		if is_instance_valid(lb):
			lb.disabled = false
		if r.ok:
			w["learned"] = nv
			badge.text = "✓ Выучено" if nv == 1 else "В изучении"
			badge.add_theme_color_override("font_color", C_OK if nv == 1 else C_WARN)
			lb.text = "Отметить выученным" if nv == 0 else "Вернуть в изучение"
			if on_status_change.is_valid():
				on_status_change.call(w)
	)
	row1.add_child(lb)

	# Ряд действий 2: Редактировать и Удалить (CRUD)
	if on_edit.is_valid() or on_delete.is_valid():
		var row2 := hbox(c)
		if on_edit.is_valid():
			var eb := button("Редактировать", on_edit.bind(w), true)
			row2.add_child(eb)
		if on_delete.is_valid():
			var db := button("Удалить", on_delete.bind(w), true)
			db.add_theme_color_override("font_color", C_BAD)
			row2.add_child(db)

	return c


static func word_card(parent: Node, w: Dictionary, lang: String) -> void:
	word_card_full(parent, w, lang)


static func _on_speak(text: String, lang: String, b: Button) -> void:
	if not speak(text, lang):
		b.text = "Озвучка недоступна"
