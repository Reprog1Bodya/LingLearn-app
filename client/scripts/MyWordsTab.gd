class_name MyWordsTab
extends BaseTab
## ИС 14–16: Полный CRUD для личных слов пользователя:
## Создание, Просмотр, Редактирование, Удаление.
## Серверный поиск, фильтрация, сортировка и пагинация (загрузка частями*).

const PAGE_SIZE := 6

var _items: Array = []
var _total_count := 0
var _current_page := 1
var _filter_code := "all"
var _sort_by := "id"
var _order := "asc"
var _search_query := ""

var _list: VBoxContainer
var _stat: Label
var _msg: Label
var _success_msg: Label
var _editing_word_id := -1

# Поля создания/редактирования
var f_word: LineEdit
var f_tr: LineEdit
var f_ts: LineEdit
var f_ex: LineEdit
var f_search: LineEdit

var o_filter: OptionButton
var o_sort: OptionButton
var _pagination_container: VBoxContainer


func refresh() -> void:
	await _fetch_words()


func _fetch_words() -> void:
	loading()
	var offset := (_current_page - 1) * PAGE_SIZE
	var path := "/my/words?limit=%d&offset=%d&sort_by=%s&order=%s" % [PAGE_SIZE, offset, _sort_by, _order]
	if _filter_code != "all":
		path += "&filter=" + _filter_code
	if _search_query != "":
		path += "&search=" + _search_query.uri_encode()

	var r: Dictionary = await Api.get_json(path)
	if not r.ok:
		show_error(r.error)
		return

	if r.data is Dictionary:
		_items = r.data.get("items", [])
		_total_count = int(r.data.get("total", _items.size()))
	else:
		_items = []
		_total_count = 0

	_build_ui()


func _build_ui() -> void:
	Ui.clear(body)

	# Заголовок
	body.add_child(Ui.label("Мой словарь: " + Session.lang_name(), 34, Ui.C_PRIMARY))

	# Сообщения об успехе и ошибках
	_success_msg = Ui.label("", 20, Ui.C_OK)
	body.add_child(_success_msg)
	_msg = Ui.label("", 20, Ui.C_BAD)
	body.add_child(_msg)

	# Карточка добавления / редактирования слова
	_build_input_card()

	# Панель серверного поиска, фильтрации и сортировки
	_build_filter_sort_bar()

	# Список слов
	_list = Ui.make_vbox(12)
	body.add_child(_list)
	_render_list()

	# Панель пагинации (загрузка данных частями*)
	_pagination_container = Ui.make_vbox(4)
	body.add_child(_pagination_container)
	_render_pagination()


func _build_input_card() -> void:
	var c := Ui.card(body)
	var title_text := "Редактировать слово" if _editing_word_id != -1 else "Добавить новое слово"
	c.add_child(Ui.label(title_text, 26, Ui.C_PRIMARY))

	f_word = Ui.input("Слово на изучаемом языке *")
	f_tr = Ui.input("Перевод на русский язык *")
	f_ts = Ui.input("Транскрипция (необязательно)")
	f_ex = Ui.input("Пример употребления (необязательно)")

	for f in [f_word, f_tr, f_ts, f_ex]:
		c.add_child(f)

	var row := Ui.hbox(c)
	row.add_child(Ui.button("Перевести (API)", _auto_translate, true))

	if _editing_word_id != -1:
		row.add_child(Ui.button("Сохранить изменения", _save_edit))
		row.add_child(Ui.button("Отмена", _cancel_edit, true))
	else:
		row.add_child(Ui.button("Добавить в словарь", _add_word))


func _build_filter_sort_bar() -> void:
	var bar := Ui.card(body, Color(0.97, 0.97, 0.99))
	bar.add_child(Ui.label("Поиск и параметры отображения", 22, Ui.C_PRIMARY))

	# Поисковая строка
	var s_row := Ui.hbox(bar)
	f_search = Ui.input("Серверный поиск по слову или переводу")
	f_search.text = _search_query
	f_search.text_submitted.connect(func(_t): _on_search())
	s_row.add_child(f_search)

	var s_btn := Ui.button("Найти", _on_search)
	s_btn.custom_minimum_size = Vector2(100, 56)
	s_row.add_child(s_btn)

	if _search_query != "":
		var reset_btn := Ui.button("✕", _on_search_clear, true)
		reset_btn.custom_minimum_size = Vector2(60, 56)
		s_row.add_child(reset_btn)

	# Фильтрация и сортировка
	var opt_row := Ui.hbox(bar)

	# Фильтр статуса
	o_filter = OptionButton.new()
	o_filter.custom_minimum_size = Vector2(0, 52)
	o_filter.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	o_filter.add_item("Все слова (сервер)")
	o_filter.add_item("Только изучаемые")
	o_filter.add_item("Только выученные")
	match _filter_code:
		"all": o_filter.select(0)
		"unlearned": o_filter.select(1)
		"learned": o_filter.select(2)
	o_filter.item_selected.connect(_on_filter_changed)
	opt_row.add_child(o_filter)

	# Сортировка
	o_sort = OptionButton.new()
	o_sort.custom_minimum_size = Vector2(0, 52)
	o_sort.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	o_sort.add_item("По порядку добавления")
	o_sort.add_item("Слово: А → Я")
	o_sort.add_item("Слово: Я → А")
	o_sort.add_item("Сначала новые")
	if _sort_by == "word" and _order == "asc":
		o_sort.select(1)
	elif _sort_by == "word" and _order == "desc":
		o_sort.select(2)
	elif _sort_by == "id" and _order == "desc":
		o_sort.select(3)
	else:
		o_sort.select(0)
	o_sort.item_selected.connect(_on_sort_changed)
	opt_row.add_child(o_sort)


func _render_list() -> void:
	Ui.clear(_list)
	if _items.is_empty():
		_list.add_child(Ui.label("Слова не найдены. Добавьте первое слово или измените фильтр поиска.", 22, Ui.C_MUTED))
		return

	for w in _items:
		Ui.word_card_full(
			_list,
			w,
			Session.lang(),
			_start_edit,
			_confirm_delete,
			func(_updated): pass
		)


func _render_pagination() -> void:
	Ui.clear(_pagination_container)
	var total_pages := maxi(1, int(ceil(float(_total_count) / float(PAGE_SIZE))))
	Ui.pagination_bar(
		_pagination_container,
		_current_page,
		total_pages,
		_total_count,
		_prev_page,
		_next_page
	)


func _prev_page() -> void:
	if _current_page > 1:
		_current_page -= 1
		_fetch_words()


func _next_page() -> void:
	var total_pages := maxi(1, int(ceil(float(_total_count) / float(PAGE_SIZE))))
	if _current_page < total_pages:
		_current_page += 1
		_fetch_words()


func _on_search() -> void:
	_search_query = f_search.text.strip_edges()
	_current_page = 1
	_fetch_words()


func _on_search_clear() -> void:
	_search_query = ""
	f_search.text = ""
	_current_page = 1
	_fetch_words()


func _on_filter_changed(idx: int) -> void:
	match idx:
		0: _filter_code = "all"
		1: _filter_code = "unlearned"
		2: _filter_code = "learned"
	_current_page = 1
	_fetch_words()


func _on_sort_changed(idx: int) -> void:
	match idx:
		0:
			_sort_by = "id"
			_order = "asc"
		1:
			_sort_by = "word"
			_order = "asc"
		2:
			_sort_by = "word"
			_order = "desc"
		3:
			_sort_by = "id"
			_order = "desc"
	_current_page = 1
	_fetch_words()


func _auto_translate() -> void:
	var w := f_word.text.strip_edges()
	if w == "":
		Ui.say(_msg, "Сначала введите слово для перевода")
		return
	Ui.say(_msg, "Выполняется перевод через внешний API…", true)
	var r: Dictionary = await Api.translate(w, Session.lang(), "ru")
	if r.ok:
		f_tr.text = r.text
		_msg.text = ""
		Ui.say(_success_msg, "Перевод успешно получен", true)
	else:
		Ui.say(_msg, r.error)


## Создание записи (CREATE) с валидацией ДО отправки
func _add_word() -> void:
	var word := f_word.text.strip_edges()
	var tr := f_tr.text.strip_edges()
	if word == "" or tr == "":
		Ui.say(_msg, "Поля 'Слово' и 'Перевод' обязательны для заполнения")
		return

	Ui.say(_msg, "Сохранение слова…", true)
	var r: Dictionary = await Api.post("/my/words", {
		"word": word,
		"translation": tr,
		"transcription": f_ts.text.strip_edges(),
		"example": f_ex.text.strip_edges(),
	})
	if not r.ok:
		Ui.say(_msg, r.error)
		return

	_msg.text = ""
	Ui.say(_success_msg, "Слово '%s' успешно добавлено в словарь!" % word, true)
	await _fetch_words()


## Начало редактирования записи (UPDATE)
func _start_edit(w: Dictionary) -> void:
	_editing_word_id = int(w.id)
	_build_ui()
	f_word.text = str(w.get("word", ""))
	f_tr.text = str(w.get("translation", ""))
	f_ts.text = str(w.get("transcription", ""))
	f_ex.text = str(w.get("example", ""))
	Ui.say(_msg, "Редактирование слова. Измените поля и нажмите 'Сохранить изменения'.", true)


func _cancel_edit() -> void:
	_editing_word_id = -1
	_build_ui()


## Сохранение отредактированной записи (UPDATE)
func _save_edit() -> void:
	if _editing_word_id == -1:
		return
	var word := f_word.text.strip_edges()
	var tr := f_tr.text.strip_edges()
	if word == "" or tr == "":
		Ui.say(_msg, "Поля 'Слово' и 'Перевод' не могут быть пустыми")
		return

	Ui.say(_msg, "Обновление записи на сервере…", true)
	var r: Dictionary = await Api.put("/my/words/%d" % _editing_word_id, {
		"word": word,
		"translation": tr,
		"transcription": f_ts.text.strip_edges(),
		"example": f_ex.text.strip_edges(),
	})
	if not r.ok:
		Ui.say(_msg, r.error)
		return

	_editing_word_id = -1
	_msg.text = ""
	Ui.say(_success_msg, "Слово успешно обновлено!", true)
	await _fetch_words()


## Подтверждение и удаление записи (DELETE)
func _confirm_delete(w: Dictionary) -> void:
	var word_id := int(w.id)
	var word_text := str(w.get("word", ""))

	# Показываем диалог подтверждения удаления в сообщении
	Ui.clear(_list)
	var c := Ui.card(_list)
	c.add_child(Ui.label("Вы действительно хотите удалить слово '%s'?" % word_text, 24, Ui.C_BAD))
	c.add_child(Ui.label("Это действие необратимо.", 18, Ui.C_MUTED))

	var row := Ui.hbox(c)
	var ok_btn := Ui.button("Да, удалить слово", func(): _execute_delete(word_id, word_text))
	ok_btn.add_theme_color_override("font_color", Ui.C_BAD)
	row.add_child(ok_btn)

	var cancel_btn := Ui.button("Отмена", _fetch_words, true)
	row.add_child(cancel_btn)


func _execute_delete(word_id: int, word_text: String) -> void:
	Ui.say(_msg, "Удаление слова…", true)
	var r: Dictionary = await Api.delete("/my/words/%d" % word_id)
	if not r.ok:
		Ui.say(_msg, r.error)
		return

	Ui.say(_success_msg, "Слово '%s' успешно удалено из словаря" % word_text, true)
	await _fetch_words()
