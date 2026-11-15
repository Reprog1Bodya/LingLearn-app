extends Node
## Слой Data_Management (клиент): состояние сессии и локальное хранилище настроек.

const CFG_PATH := "user://linglearn.cfg"

var token := ""
var profile: Dictionary = {}
var lang_names: Dictionary = {}
var use_translate := true


func load_saved() -> void:
	var cf := ConfigFile.new()
	if cf.load(CFG_PATH) == OK:
		token = str(cf.get_value("auth", "token", ""))
		# Ручной адрес сохраняется, только если пользователь сам его менял; иначе берём вшитый адрес сборки
		if bool(cf.get_value("server", "custom", false)):
			Api.base_url = str(cf.get_value("server", "url", Api.default_url))
		use_translate = bool(cf.get_value("integrations", "translate", true))


func save() -> void:
	var cf := ConfigFile.new()
	cf.load(CFG_PATH)
	cf.set_value("auth", "token", token)
	cf.set_value("server", "url", Api.base_url)
	cf.set_value("server", "custom", Api.base_url != Api.default_url)
	cf.set_value("integrations", "translate", use_translate)
	cf.save(CFG_PATH)


func clear() -> void:
	token = ""
	profile = {}
	Api.token = ""
	save()


func lang() -> String:
	var v: Variant = profile.get("language")
	return v if v is String else ""


func goal() -> String:
	var v: Variant = profile.get("goal")
	return v if v is String else ""


func is_admin() -> bool:
	return str(profile.get("role", "")) == "admin"


func lang_name() -> String:
	return str(lang_names.get(lang(), lang().to_upper()))
