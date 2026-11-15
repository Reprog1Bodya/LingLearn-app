class_name HomeScreen
extends MarginContainer
## Главный экран: вкладки Учёба / Язык / Словари / Мои слова / Профиль / (Админ).

var app
var tabs: TabContainer


func _init(a) -> void:
	app = a


func _ready() -> void:
	add_theme_constant_override("margin_top", 8)
	var r: Dictionary = await Api.get_json("/languages")
	if r.ok and r.data is Dictionary and r.data.has("items"):
		for l in r.data["items"]:
			Session.lang_names[str(l.code)] = str(l.name)
	tabs = TabContainer.new()
	tabs.tabs_position = TabContainer.POSITION_BOTTOM
	add_child(tabs)
	var list: Array = [
		["Учёба", LearnTab.new()],
		["Язык", LanguageTab.new()],
		["Словари", DictTab.new()],
		["Мои слова", MyWordsTab.new()],
		["Профиль", ProfileTab.new()],
	]
	if Session.is_admin():
		list.append(["Админ", AdminTab.new()])
	for e in list:
		var t: BaseTab = e[1]
		t.app = app
		t.name = e[0]
		tabs.add_child(t)
	tabs.tab_changed.connect(_on_tab)
	_on_tab(0)


func _on_tab(i: int) -> void:
	var t := tabs.get_child(i) as BaseTab
	if t != null:
		t.refresh()
