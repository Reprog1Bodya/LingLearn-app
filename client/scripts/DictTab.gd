class_name DictTab
extends BaseTab
## Просмотр словарей: список словарей с рекомендациями → просмотр слов словаря
## с серверным поиском, сортировкой и пагинацией (загрузка частями*).

const PAGE_SIZE := 8

var _active_dict: Dictionary = {}
var _words: Array = []
var _words_total := 0
var _current_page := 1
var _search_query := ""
var _sort_by := "id"
var _order := "asc"

var _list: VBoxContainer
var _msg: Label
var _lang := ""
var _is_viewing_words := false

var f_search: LineEdit
var o_sort: OptionButton
var _pagination_container: VBoxContainer


func refresh() -> void:
	_is_viewing_words = false
	_active_dict = {}
	loading()
	var r: Dictionary = await Api.get_json("/dictionaries?lang=%s&goal=%s" % [Session.lang(), Session.goal()])
	if not r.ok:
		show_error(r.error)
		return

	Ui.clear(body)
	body.add_child(Ui.label("Словари: " + Session.lang_name(), 36, Ui.C_PRIMARY))
	body.add_child(Ui.label("★ — рекомендовано для вашей цели («%s»)" % Session.goal(), 20, Ui.C_MUTED))
	_msg = Ui.label("", 20, Ui.C_BAD)
	body.add_child(_msg)

	var items: Array = []
	if r.data is Dictionary and r.data.has("items"):
		items = r.data["items"]
	if items.is_empty():
		body.add_child(Ui.label("Для выбранного языка словари пока не добавлены.", 22, Ui.C_MUTED))
		return

	for d in items:
		Ui.dict_card(body, d, _toggle, _open_dict)


func _toggle(d: Dictionary, btn: Button) -> void:
	var err: String = await Ui.toggle_dict(d, btn)
	if err != "":
		Ui.say(_msg, err)
	else:
		_msg.text = ""


func _open_dict(d: Dictionary) -> void:
	_active_dict = d
	_lang = str(d.get("lang", Session.lang()))
	_is_viewing_words = true
	_current_page = 1
	_search_query = ""
	_sort_by = "id"
	_order = "asc"
	await _fetch_dict_words()


func _fetch_dict_words() -> void:
	loading()
	var offset := (_current_page - 1) * PAGE_SIZE
	var dict_id := int(_active_dict.get("id", 0))
	var path := "/dictionaries/%d/words?limit=%d&offset=%d&sort_by=%s&order=%s" % [dict_id, PAGE_SIZE, offset, _sort_by, _order]
	if _search_query != "":
		path += "&search=" + _search_query.uri_encode()

	var r: Dictionary = await Api.get_json(path)
	if not r.ok:
		show_error(r.error, _fetch_dict_words)
		return

	if r.data is Dictionary:
		_words = r.data.get("items", [])
		_words_total = int(r.data.get("total", _words.size()))
	else:
		_words = []
		_words_total = 0

	_render_dict_words_view()


func _render_dict_words_view() -> void:
	Ui.clear(body)
	body.add_child(Ui.button("← Назад к списку словарей", refresh, true))
	body.add_child(Ui.label(str(_active_dict.get("title", "Словарь")), 34, Ui.C_PRIMARY))

	var descr := str(_active_dict.get("descr", ""))
	if descr != "":
		body.add_child(Ui.label(descr, 20, Ui.C_MUTED))

	# Панель серверного поиска и сортировки слов словаря
	var bar := Ui.card(body, Color(0.97, 0.97, 0.99))
	var s_row := Ui.hbox(bar)
	f_search = Ui.input("Поиск в словаре по слову или переводу")
	f_search.text = _search_query
	f_search.text_submitted.connect(func(_t): _on_search())
	s_row.add_child(f_search)

	var s_btn := Ui.button("Найти", _on_search)
	s_btn.custom_minimum_size = Vector2(90, 56)
	s_row.add_child(s_btn)

	if _search_query != "":
		var reset_btn := Ui.button("✕", _on_search_clear, true)
		reset_btn.custom_minimum_size = Vector2(50, 56)
		s_row.add_child(reset_btn)

	var opt_row := Ui.hbox(bar)
	o_sort = OptionButton.new()
	o_sort.custom_minimum_size = Vector2(0, 50)
	o_sort.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	o_sort.add_item("Сортировка по умолчанию")
	o_sort.add_item("Слово: А → Я")
	o_sort.add_item("Слово: Я → А")
	if _sort_by == "word" and _order == "asc":
		o_sort.select(1)
	elif _sort_by == "word" and _order == "desc":
		o_sort.select(2)
	else:
		o_sort.select(0)
	o_sort.item_selected.connect(_on_sort_changed)
	opt_row.add_child(o_sort)

	_list = Ui.make_vbox(12)
	body.add_child(_list)

	if _words.is_empty():
		_list.add_child(Ui.label("В этом словаре нет подходящих слов.", 22, Ui.C_MUTED))
	else:
		for w in _words:
			Ui.word_card(_list, w, _lang)

	# Панель пагинации частями*
	_pagination_container = Ui.make_vbox(4)
	body.add_child(_pagination_container)
	var total_pages := maxi(1, int(ceil(float(_words_total) / float(PAGE_SIZE))))
	Ui.pagination_bar(
		_pagination_container,
		_current_page,
		total_pages,
		_words_total,
		_prev_page,
		_next_page
	)


func _on_search() -> void:
	_search_query = f_search.text.strip_edges()
	_current_page = 1
	_fetch_dict_words()


func _on_search_clear() -> void:
	_search_query = ""
	f_search.text = ""
	_current_page = 1
	_fetch_dict_words()


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
	_current_page = 1
	_fetch_dict_words()


func _prev_page() -> void:
	if _current_page > 1:
		_current_page -= 1
		_fetch_dict_words()


func _next_page() -> void:
	var total_pages := maxi(1, int(ceil(float(_words_total) / float(PAGE_SIZE))))
	if _current_page < total_pages:
		_current_page += 1
		_fetch_dict_words()
