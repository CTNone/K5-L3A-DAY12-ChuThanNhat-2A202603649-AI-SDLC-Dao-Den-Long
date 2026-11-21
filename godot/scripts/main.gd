extends Node3D

const TUNING_PATH := "res://shared/tuning.json"
const MAP_PATHS := {
	1: "res://shared/maps/night1.json",
	2: "res://shared/maps/night2.json",
	3: "res://shared/maps/night3.json",
}
const SETTINGS_PATH := "user://settings.cfg"
const AUDIO_SCRIPT := preload("res://scripts/audio_manager.gd")
const DEFAULT_BINDS := {
	"move_forward": KEY_W, "move_back": KEY_S, "move_left": KEY_A, "move_right": KEY_D,
	"jump": KEY_SPACE, "dash": KEY_SHIFT, "interact": KEY_E, "pulse": KEY_F, "pause": KEY_ESCAPE,
}
const BIND_LABELS := {
	"move_forward": "Tiến", "move_back": "Lùi", "move_left": "Trái", "move_right": "Phải",
	"jump": "Nhảy / liệng", "dash": "Lướt", "interact": "Tương tác", "pulse": "Xung sáng", "pause": "Tạm dừng",
}

var T: Dictionary = {}
var map: Dictionary = {}
var night := 1
var state := "menu"
var settings := {"master": 0.8, "music": 0.55, "sfx": 0.8, "sensitivity": 1.0, "color_mode": "default",
	"facing": "camera", "reduce_motion": false, "text_scale": 1.0, "admin": false}
var cheat_invincible := false
var cheat_fuel := false
var cheat_speed := false
var cheat_reveal := false
var bindings: Dictionary = {}
var rebind_action := ""
var rebind_buttons: Dictionary = {}
var rebind_status: Label

var world_root: Node3D
var player: Node3D
var player_body: MeshInstance3D
var player_light: OmniLight3D
var camera: Camera3D
var audio: Node

var cam_yaw := 0.0
var cam_pitch := -0.24
var cam_distance := 8.5

var pos := Vector3.ZERO
var vy := 0.0
var on_ground := true
var safe_pos := Vector3.ZERO
var move_dir := Vector3.ZERO
var dash_dir := Vector3.FORWARD
var dash_t := 0.0
var dash_cd := 0.0
var pulse_cd := 0.0
var invuln := 0.0
var wind_shield := 0.0
var jump_held := false
var dash_held := false
var interact_held := false
var pulse_held := false
var pause_held := false

var flames := 3
var carried := 0
var score := 0
var time_left := 300.0
var sim_time := 0.0
var won := false
var end_reason := ""
var successful_lights := 0

var lanterns: Array = []
var motes: Array = []
var shades: Array = []
var wisps: Array = []
var charms: Array = []
var bell: Dictionary = {}
var wind_zones: Array = []
var jump_pads: Array = []
var rng := RandomNumberGenerator.new()

var menu_layer: CanvasLayer
var menu_root: Control
var intro_layer: CanvasLayer
var intro_root: Control
var intro_title: Label
var intro_desc: Label
var intro_start: Button
var intro_night := 1
var settings_layer: CanvasLayer
var settings_root: Control
var settings_from_pause := false
var master_slider: HSlider
var music_slider: HSlider
var sfx_slider: HSlider
var sensitivity_slider: HSlider
var setting_labels: Dictionary = {}
var controls_layer: CanvasLayer
var controls_root: Control
var pause_layer: CanvasLayer
var pause_root: Control
var end_layer: CanvasLayer
var end_root: Control
var end_title: Label
var end_detail: Label
var end_score: Label
var end_next: Button
var end_leaderboard: Button
var hud_layer: CanvasLayer
var hud_root: Control
var hud_flames: Label
var hud_timer: Label
var hud_night: Label
var hud_score: Label
var hud_lanterns: Label
var hud_capacity: Label
var hud_fuel: ProgressBar
var hud_fuel_label: Label
var hud_slots_label: Label
var hud_wind: Label
var hud_fps: Label
var hud_prompt: Label
var hud_warning: Label
var hud_compass_arrow: Label
var hud_compass_label: Label
var hud_slots: Array[ColorRect] = []
var hud_dash: ProgressBar
var hud_pulse: ProgressBar
var hud_dash_label: Label
var hud_pulse_label: Label
var color_mode_button: OptionButton
var facing_button: OptionButton
var text_scale_button: OptionButton
var reduce_motion_check: CheckBox
var admin_check: CheckBox
var leaderboard_box: VBoxContainer
var leaderboard_name: LineEdit
var leaderboard_save: Button
var leaderboard_list: Label
var leaderboard_layer: CanvasLayer
var leaderboard_root: Control
var leaderboard_from_end := false


func _ready() -> void:
	var tuning_doc := _read_json(TUNING_PATH)
	T = tuning_doc.get("tuning", {})
	_load_settings()
	_setup_input()
	_setup_environment()
	world_root = Node3D.new()
	world_root.name = "World"
	add_child(world_root)
	_load_map(1)
	_build_world()
	_create_player()
	_create_camera()
	_create_ui()
	_setup_audio()
	_reset_state()
	_show_menu()
	if "--capture" in OS.get_cmdline_user_args():
		_run_capture()


func _run_capture() -> void:
	var args := OS.get_cmdline_user_args()
	var capture_dir := "docs/proof/phase-3"
	for i in args.size():
		if args[i] == "--capture-dir" and i + 1 < args.size():
			capture_dir = args[i + 1]
	DirAccess.make_dir_recursive_absolute(capture_dir)
	await get_tree().process_frame
	await get_tree().create_timer(0.8).timeout
	_save_viewport(capture_dir + "/menu-1280x720.png")
	start_night(1)
	await get_tree().create_timer(1.4).timeout
	_save_viewport(capture_dir + "/night1-1280x720.png")
	start_night(3)
	pos = Vector3(0.0, 0.0, 14.0)
	player.position = pos
	cam_yaw = 0.0
	cam_pitch = -0.28
	cam_distance = 12.0
	_update_camera(0.0)
	await get_tree().create_timer(0.15).timeout
	_save_viewport(capture_dir + "/night3-1280x720.png")
	get_tree().quit()


func _save_viewport(path: String) -> void:
	var image := get_viewport().get_texture().get_image()
	if image != null:
		image.save_png(path)


func _setup_audio() -> void:
	audio = AUDIO_SCRIPT.new()
	add_child(audio)
	_apply_audio_settings()


func _setup_environment() -> void:
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.015, 0.025, 0.075)
	sky_material.sky_horizon_color = Color(0.12, 0.09, 0.24)
	sky_material.ground_bottom_color = Color(0.01, 0.015, 0.035)
	sky_material.ground_horizon_color = Color(0.08, 0.07, 0.16)
	sky_material.sun_angle_max = 18.0
	sky_material.sun_curve = 0.08
	var sky := Sky.new()
	sky.sky_material = sky_material
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 1.15
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_light_color = Color(0.11, 0.14, 0.28)
	env.fog_light_energy = 0.5
	env.fog_density = 0.004
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-52.0, -28.0, 0.0)
	moon.light_color = Color(0.64, 0.74, 1.0)
	moon.light_energy = 1.35
	moon.shadow_enabled = true
	add_child(moon)
	var fill := OmniLight3D.new()
	fill.position = Vector3(0.0, 12.0, 0.0)
	fill.light_color = Color(0.35, 0.42, 0.85)
	fill.light_energy = 1.15
	fill.omni_range = 95.0
	fill.shadow_enabled = false
	add_child(fill)


func _create_player() -> void:
	player = Node3D.new()
	player.name = "Player"
	add_child(player)
	var mesh := CapsuleMesh.new()
	mesh.radius = 0.38
	mesh.height = 1.6
	mesh.radial_segments = 20
	mesh.rings = 8
	player_body = MeshInstance3D.new()
	player_body.mesh = mesh
	player_body.position = Vector3(0.0, 0.85, 0.0)
	var body_mat := StandardMaterial3D.new()
	body_mat.albedo_color = Color(0.92, 0.52, 0.18)
	body_mat.roughness = 0.42
	body_mat.emission_enabled = true
	body_mat.emission = Color(0.35, 0.12, 0.02)
	body_mat.emission_energy_multiplier = 0.8
	player_body.material_override = body_mat
	player.add_child(player_body)
	var head := MeshInstance3D.new()
	var head_mesh := SphereMesh.new()
	head_mesh.radius = 0.27
	head_mesh.height = 0.54
	head.mesh = head_mesh
	head.position = Vector3(0.0, 1.58, 0.0)
	var skin := StandardMaterial3D.new()
	skin.albedo_color = Color(0.9, 0.66, 0.46)
	skin.roughness = 0.7
	head.material_override = skin
	player.add_child(head)
	var cloak := MeshInstance3D.new()
	var cloak_mesh := CylinderMesh.new()
	cloak_mesh.top_radius = 0.22
	cloak_mesh.bottom_radius = 0.52
	cloak_mesh.height = 0.95
	cloak.mesh = cloak_mesh
	cloak.position = Vector3(0.0, 0.58, 0.0)
	var cloak_mat := StandardMaterial3D.new()
	cloak_mat.albedo_color = Color(0.1, 0.24, 0.3)
	cloak_mat.roughness = 0.8
	cloak.material_override = cloak_mat
	player.add_child(cloak)
	var staff := MeshInstance3D.new()
	var staff_mesh := CylinderMesh.new()
	staff_mesh.top_radius = 0.035
	staff_mesh.bottom_radius = 0.045
	staff_mesh.height = 1.45
	staff.mesh = staff_mesh
	staff.position = Vector3(0.42, 0.92, 0.15)
	staff.rotation_degrees = Vector3(0.0, 0.0, -7.0)
	var staff_mat := StandardMaterial3D.new()
	staff_mat.albedo_color = Color(0.24, 0.16, 0.1)
	staff.material_override = staff_mat
	player.add_child(staff)
	var lantern_mesh := SphereMesh.new()
	lantern_mesh.radius = 0.24
	lantern_mesh.height = 0.48
	var lantern_ball := MeshInstance3D.new()
	lantern_ball.mesh = lantern_mesh
	lantern_ball.position = Vector3(0.42, 1.12, 0.15)
	var lantern_mat := StandardMaterial3D.new()
	lantern_mat.albedo_color = Color(1.0, 0.82, 0.35)
	lantern_mat.emission_enabled = true
	lantern_mat.emission = Color(1.0, 0.55, 0.12)
	lantern_mat.emission_energy_multiplier = 2.2
	lantern_ball.material_override = lantern_mat
	player.add_child(lantern_ball)
	player_light = OmniLight3D.new()
	player_light.position = Vector3(0.0, 1.25, 0.0)
	player_light.light_color = Color(1.0, 0.62, 0.25)
	player_light.light_energy = 1.2
	player_light.omni_range = 7.0
	player_light.shadow_enabled = false
	player.add_child(player_light)


func _create_camera() -> void:
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 68.0
	camera.near = 0.1
	camera.far = 260.0
	add_child(camera)


func _create_ui() -> void:
	hud_layer = _canvas(5)
	hud_root = _full_control(hud_layer)
	hud_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_hud()

	menu_layer = _canvas(10)
	menu_root = _full_control(menu_layer)
	_build_menu()

	intro_layer = _canvas(11)
	intro_root = _full_control(intro_layer)
	_build_intro()

	settings_layer = _canvas(12)
	settings_root = _full_control(settings_layer)
	_build_settings()

	controls_layer = _canvas(13)
	controls_root = _full_control(controls_layer)
	_build_controls()

	pause_layer = _canvas(14)
	pause_root = _full_control(pause_layer)
	_build_pause()

	end_layer = _canvas(15)
	end_root = _full_control(end_layer)
	_build_end()

	leaderboard_layer = _canvas(16)
	leaderboard_root = _full_control(leaderboard_layer)
	_build_leaderboard()

	hud_root.visible = false
	intro_root.visible = false
	settings_root.visible = false
	controls_root.visible = false
	pause_root.visible = false
	end_root.visible = false
	leaderboard_root.visible = false


func _canvas(layer_index: int) -> CanvasLayer:
	var layer := CanvasLayer.new()
	layer.layer = layer_index
	add_child(layer)
	return layer


func _full_control(parent: Node) -> Control:
	var control := Control.new()
	parent.add_child(control)
	control.set_anchors_preset(Control.PRESET_FULL_RECT)
	control.offset_left = 0.0
	control.offset_top = 0.0
	control.offset_right = 0.0
	control.offset_bottom = 0.0
	return control


func _anchor_rect(control: Control, left: float, top: float, right: float, bottom: float) -> void:
	control.anchor_left = left
	control.anchor_top = top
	control.anchor_right = right
	control.anchor_bottom = bottom


func _panel_style(bg: Color, border: Color, radius := 10) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.corner_radius_top_left = radius
	style.corner_radius_top_right = radius
	style.corner_radius_bottom_left = radius
	style.corner_radius_bottom_right = radius
	style.content_margin_left = 14.0
	style.content_margin_right = 14.0
	style.content_margin_top = 12.0
	style.content_margin_bottom = 12.0
	return style


func _button_style(bg: Color, border: Color) -> StyleBoxFlat:
	return _panel_style(bg, border, 8)


func _label(text: String, size := 18, color := Color(0.9, 0.94, 1.0)) -> Label:
	var label := Label.new()
	label.text = text
	var scaled := int(maxi(18, roundi(float(size) * float(settings.get("text_scale", 1.0)))))
	label.add_theme_font_size_override("font_size", scaled)
	label.add_theme_color_override("font_color", color)
	return label


func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(300.0, 42.0)
	button.add_theme_font_size_override("font_size", 18)
	button.add_theme_color_override("font_color", Color(0.92, 0.96, 1.0))
	button.add_theme_stylebox_override("normal", _button_style(Color(0.09, 0.13, 0.24, 0.95), Color(0.25, 0.42, 0.7)))
	button.add_theme_stylebox_override("hover", _button_style(Color(0.14, 0.2, 0.36, 1.0), Color(0.5, 0.75, 1.0)))
	button.add_theme_stylebox_override("pressed", _button_style(Color(0.05, 0.08, 0.16, 1.0), Color(0.8, 0.9, 1.0)))
	button.pressed.connect(callback)
	return button


func _panel(min_size := Vector2.ZERO) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.04, 0.085, 0.94), Color(0.2, 0.36, 0.62)))
	panel.custom_minimum_size = min_size
	return panel


func _margin(parent: Node, value := 18) -> MarginContainer:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", value)
	margin.add_theme_constant_override("margin_right", value)
	margin.add_theme_constant_override("margin_top", value)
	margin.add_theme_constant_override("margin_bottom", value)
	parent.add_child(margin)
	return margin


func _vbox(parent: Node, separation := 10) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", separation)
	parent.add_child(box)
	return box


func _hbox(parent: Node, separation := 8) -> HBoxContainer:
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", separation)
	parent.add_child(box)
	return box


func _build_menu() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.78)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	menu_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(560.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 28)
	var box := _vbox(margin, 12)
	var title := _label("ĐẢO ĐÈN LỒNG", 44, Color(1.0, 0.82, 0.42))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var subtitle := _label("Thắp sáng những ngọn đèn trước khi bình minh", 17, Color(0.72, 0.8, 1.0))
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(subtitle)
	box.add_child(_label("Đêm 1  •  Đảo Bình Yên", 15, Color(0.62, 0.72, 0.9)))
	box.add_child(_button("Bắt đầu đêm 1", _show_intro.bind(1)))
	box.add_child(_button("Đêm 2  •  Hai Đảo", _show_intro.bind(2)))
	box.add_child(_button("Đêm 3  •  Tháp Chuông", _show_intro.bind(3)))
	box.add_child(_button("Cài đặt", _show_settings.bind(false)))
	box.add_child(_button("Điều khiển", _show_controls))
	box.add_child(_button("Bảng điểm", _show_leaderboard.bind(false)))
	box.add_child(_button("Thoát", _quit_game))
	var hint := _label("Chuột: nhìn  •  WASD: di chuyển  •  Space: nhảy/liệng  •  E: tương tác  •  F: xung sáng  •  Shift: lướt", 13, Color(0.58, 0.68, 0.82))
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hint)


func _build_intro() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.72)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	intro_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	intro_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(560.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 28)
	var box := _vbox(margin, 12)
	intro_title = _label("ĐÊM 1", 38, Color(1.0, 0.82, 0.42))
	intro_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(intro_title)
	intro_desc = _label("", 18, Color(0.82, 0.88, 1.0))
	intro_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	intro_desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(intro_desc)
	var objective := _label("Mục tiêu: thắp sáng tất cả ngọn đèn trước khi bình minh. Đom đóm nằm rải rác quanh đảo; mỗi đèn cần 5 đom đóm.", 15, Color(0.68, 0.78, 0.92))
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	objective.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(objective)
	intro_start = _button("Bắt đầu", _on_intro_start)
	box.add_child(intro_start)
	box.add_child(_button("Quay lại", _show_menu))


func _build_settings() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.86)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	settings_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	settings_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(560.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 26)
	var box := _vbox(margin, 14)
	var title := _label("CÀI ĐẶT", 34, Color(1.0, 0.82, 0.42))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	master_slider = _add_slider(box, "Âm lượng tổng", 0.0, 100.0, 1.0, settings["master"] * 100.0, "master")
	music_slider = _add_slider(box, "Nhạc nền", 0.0, 100.0, 1.0, settings["music"] * 100.0, "music")
	sfx_slider = _add_slider(box, "Hiệu ứng", 0.0, 100.0, 1.0, settings["sfx"] * 100.0, "sfx")
	sensitivity_slider = _add_slider(box, "Độ nhạy chuột", 50.0, 300.0, 5.0, settings["sensitivity"] * 100.0, "sensitivity")
	var color_row := _vbox(box, 3)
	color_row.add_child(_label("Bảng màu", 16, Color(0.82, 0.88, 1.0)))
	color_mode_button = OptionButton.new()
	color_mode_button.add_item("Mặc định", 0)
	color_mode_button.add_item("Dễ phân biệt màu", 1)
	color_mode_button.selected = 1 if str(settings["color_mode"]) == "colorblind" else 0
	color_mode_button.custom_minimum_size = Vector2(420.0, 30.0)
	color_mode_button.item_selected.connect(_on_color_mode_selected)
	color_row.add_child(color_mode_button)
	var facing_row := _vbox(box, 3)
	facing_row.add_child(_label("Hướng nhân vật", 18, Color(0.82, 0.88, 1.0)))
	facing_button = OptionButton.new()
	facing_button.add_item("Theo camera", 0)
	facing_button.add_item("Theo hướng di chuyển", 1)
	facing_button.selected = 1 if str(settings["facing"]) == "movement" else 0
	facing_button.custom_minimum_size = Vector2(420.0, 34.0)
	facing_button.add_theme_font_size_override("font_size", 18)
	facing_button.item_selected.connect(_on_facing_selected)
	facing_row.add_child(facing_button)
	var scale_row := _vbox(box, 3)
	scale_row.add_child(_label("Cỡ chữ (áp dụng sau khi mở lại)", 18, Color(0.82, 0.88, 1.0)))
	text_scale_button = OptionButton.new()
	text_scale_button.add_item("100%", 0)
	text_scale_button.add_item("125%", 1)
	text_scale_button.selected = 1 if float(settings["text_scale"]) > 1.0 else 0
	text_scale_button.custom_minimum_size = Vector2(420.0, 34.0)
	text_scale_button.add_theme_font_size_override("font_size", 18)
	text_scale_button.item_selected.connect(_on_text_scale_selected)
	scale_row.add_child(text_scale_button)
	reduce_motion_check = CheckBox.new()
	reduce_motion_check.text = "Giảm chuyển động"
	reduce_motion_check.button_pressed = bool(settings["reduce_motion"])
	reduce_motion_check.add_theme_font_size_override("font_size", 18)
	reduce_motion_check.toggled.connect(_on_reduce_motion_toggled)
	box.add_child(reduce_motion_check)
	admin_check = CheckBox.new()
	admin_check.text = "Admin: bật cheat khi chơi (không lưu bảng điểm)"
	admin_check.button_pressed = bool(settings["admin"])
	admin_check.add_theme_font_size_override("font_size", 18)
	admin_check.toggled.connect(_on_admin_toggled)
	box.add_child(admin_check)
	box.add_child(_button("Lưu và quay lại", _close_settings))


func _add_slider(parent: Node, label_text: String, min_value: float, max_value: float, step: float, value: float, key: String) -> HSlider:
	var row := _vbox(parent, 3)
	var header := _hbox(row, 8)
	header.add_child(_label(label_text, 16, Color(0.82, 0.88, 1.0)))
	var value_label := _label("", 15, Color(1.0, 0.82, 0.42))
	value_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	header.add_child(value_label)
	setting_labels[key] = value_label
	var slider := HSlider.new()
	slider.min_value = min_value
	slider.max_value = max_value
	slider.step = step
	slider.value = value
	slider.custom_minimum_size = Vector2(420.0, 22.0)
	row.add_child(slider)
	slider.value_changed.connect(_on_setting_changed.bind(key))
	_update_setting_label(key, value)
	return slider


func _update_setting_label(key: String, value: float) -> void:
	if not setting_labels.has(key):
		return
	var label: Label = setting_labels[key]
	if key == "sensitivity":
		label.text = "%.2fx" % (value / 100.0)
	else:
		label.text = "%d%%" % int(value)


func _build_controls() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.86)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	controls_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	controls_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(620.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 26)
	var box := _vbox(margin, 10)
	var title := _label("ĐIỀU KHIỂN", 34, Color(1.0, 0.82, 0.42))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var text := _label("WASD — di chuyển theo hướng camera\nChuột — xoay camera\nSpace — nhảy; giữ Space khi rơi để liệng\nShift — lướt nhanh (có hồi chiêu)\nE — nhặt đom đóm / nạp dầu / thắp đèn\nF — xung sáng: đẩy lùi và làm choáng Bóng Tối\nEsc — tạm dừng\n\nĐèn mới cần 10 đom đóm; thắp lại cần 5. Mỗi đom nạp 10 dầu.\nGiữ đèn trên 30 dầu để duy trì vùng an toàn.\nBình minh: cần ít nhất 60% số đèn còn sáng.", 17, Color(0.82, 0.88, 1.0))
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	box.add_child(text)
	box.add_child(_button("Quay lại", _show_menu))


func _build_pause() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.72)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pause_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	pause_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(460.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 26)
	var box := _vbox(margin, 12)
	var title := _label("TẠM DỪNG", 34, Color(1.0, 0.82, 0.42))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	box.add_child(_button("Tiếp tục", _resume_game))
	box.add_child(_button("Cài đặt", _show_settings.bind(true)))
	box.add_child(_button("Chơi lại đêm nay", _on_retry))
	box.add_child(_button("Về menu", _show_menu))


func _build_end() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.76)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	end_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	end_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(560.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 28)
	var box := _vbox(margin, 12)
	end_title = _label("", 38, Color(1.0, 0.82, 0.42))
	end_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(end_title)
	end_detail = _label("", 18, Color(0.82, 0.88, 1.0))
	end_detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	end_detail.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(end_detail)
	end_score = _label("", 24, Color(0.65, 0.95, 0.75))
	end_score.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(end_score)
	end_next = _button("Đêm kế tiếp", _on_next)
	box.add_child(end_next)
	end_leaderboard = _button("Lưu vào bảng điểm", _show_leaderboard.bind(true))
	box.add_child(end_leaderboard)
	box.add_child(_button("Chơi lại", _on_retry))
	box.add_child(_button("Về menu", _show_menu))


func _build_leaderboard() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.008, 0.012, 0.035, 0.9)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	leaderboard_root.add_child(bg)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var center := CenterContainer.new()
	leaderboard_root.add_child(center)
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	var panel := _panel(Vector2(640.0, 0.0))
	center.add_child(panel)
	var margin := _margin(panel, 28)
	var box := _vbox(margin, 12)
	var title := _label("BẢNG ĐIỂM", 34, Color(1.0, 0.82, 0.42))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	leaderboard_list = _label("", 18, Color(0.82, 0.9, 1.0))
	leaderboard_list.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	leaderboard_list.custom_minimum_size = Vector2(580.0, 260.0)
	box.add_child(leaderboard_list)
	leaderboard_box = _vbox(box, 8)
	leaderboard_name = LineEdit.new()
	leaderboard_name.placeholder_text = "Tên 3-12 ký tự"
	leaderboard_name.max_length = 12
	leaderboard_name.custom_minimum_size = Vector2(560.0, 40.0)
	leaderboard_name.add_theme_font_size_override("font_size", 18)
	leaderboard_box.add_child(leaderboard_name)
	leaderboard_save = _button("Lưu điểm", _save_leaderboard_entry)
	leaderboard_box.add_child(leaderboard_save)
	box.add_child(_button("Đóng", _close_leaderboard))
	box.add_child(_button("Về menu", _show_menu))


func _show_leaderboard(from_end: bool) -> void:
	leaderboard_from_end = from_end
	leaderboard_root.visible = true
	end_root.visible = false
	menu_root.visible = false
	pause_root.visible = false
	leaderboard_box.visible = from_end and not bool(settings["admin"])
	leaderboard_name.text = ""
	_refresh_leaderboard()
	state = "leaderboard"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _close_leaderboard() -> void:
	leaderboard_root.visible = false
	if leaderboard_from_end:
		end_root.visible = true
		state = "won" if won else "lost"
	else:
		_show_menu()


func _refresh_leaderboard() -> void:
	var entries := _load_leaderboard()
	var lines: Array[String] = []
	for i in mini(entries.size(), 10):
		var e: Dictionary = entries[i]
		lines.append("%d. %s  %d điểm  %d đêm  %s" % [i + 1, str(e.get("name", "?")), int(e.get("score", 0)), int(e.get("nights_won", 0)), str(e.get("achieved_at", ""))])
	if lines.is_empty():
		lines.append("Chưa có ai trên bảng điểm.")
	leaderboard_list.text = "\n".join(lines)


func _load_leaderboard() -> Array:
	var entries: Array = []
	if not FileAccess.file_exists("user://leaderboard.json"):
		return entries
	var file := FileAccess.open("user://leaderboard.json", FileAccess.READ)
	if file == null:
		return entries
	var data = JSON.parse_string(file.get_as_text())
	if data is Array:
		entries = data
	elif data is Dictionary and data.get("entries") is Array:
		entries = data["entries"]
	var valid: Array = []
	for raw in entries:
		if not raw is Dictionary:
			continue
		var name := str(raw.get("name", "")).strip_edges()
		if name.length() < 3 or name.length() > 12:
			continue
		valid.append({"name": name, "score": int(raw.get("score", 0)), "nights_won": int(raw.get("nights_won", 0)),
			"achieved_at": str(raw.get("achieved_at", "")), "seed": int(raw.get("seed", 1))})
	valid.sort_custom(func(a, b): return int(a["score"]) > int(b["score"]) or (int(a["score"]) == int(b["score"]) and str(a["achieved_at"]) < str(b["achieved_at"])))
	return valid.slice(0, 10)


func _save_leaderboard_entry() -> void:
	var name := leaderboard_name.text.strip_edges()
	if name.length() < 3 or name.length() > 12:
		leaderboard_name.placeholder_text = "Tên phải từ 3 đến 12 ký tự"
		return
	if bool(settings["admin"]):
		leaderboard_name.text = ""
		return
	var achieved := Time.get_datetime_string_from_system(true) + "Z"
	var entry := {"name": name, "score": score, "nights_won": night if won else max(0, night - 1), "achieved_at": achieved, "seed": 1}
	var entries := _load_leaderboard()
	entries.append(entry)
	entries.sort_custom(func(a, b): return int(a["score"]) > int(b["score"]) or (int(a["score"]) == int(b["score"]) and str(a["achieved_at"]) < str(b["achieved_at"])))
	entries = entries.slice(0, 10)
	var file := FileAccess.open("user://leaderboard.json", FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"version": 1, "entries": entries}, "  "))
	leaderboard_name.text = ""
	leaderboard_box.visible = false
	_refresh_leaderboard()


func _build_hud() -> void:
	var left_panel := _panel()
	left_panel.anchor_left = 0.0
	left_panel.anchor_top = 0.0
	left_panel.anchor_right = 0.0
	left_panel.anchor_bottom = 0.0
	left_panel.offset_left = 18.0
	left_panel.offset_top = 18.0
	left_panel.offset_right = 360.0
	left_panel.offset_bottom = 196.0
	hud_root.add_child(left_panel)
	var left_margin := _margin(left_panel, 12)
	var left_box := _vbox(left_margin, 5)
	hud_flames = _label("LỬA  3/3", 24, Color(1.0, 0.58, 0.28))
	left_box.add_child(hud_flames)
	hud_timer = _label("05:00", 30, Color(0.82, 0.92, 1.0))
	left_box.add_child(hud_timer)
	hud_night = _label("ĐÊM 1", 15, Color(0.62, 0.75, 0.95))
	left_box.add_child(hud_night)
	hud_fuel_label = _label("DẦU  --", 14, Color(1.0, 0.86, 0.5))
	left_box.add_child(hud_fuel_label)
	hud_fuel = _bar(left_box)
	hud_fuel.custom_minimum_size = Vector2(300.0, 12.0)
	hud_fuel.max_value = 100.0
	hud_fuel.value = 0.0

	var right_panel := _panel()
	right_panel.anchor_left = 1.0
	right_panel.anchor_top = 0.0
	right_panel.anchor_right = 1.0
	right_panel.anchor_bottom = 0.0
	right_panel.offset_left = -350.0
	right_panel.offset_top = 18.0
	right_panel.offset_right = -18.0
	right_panel.offset_bottom = 206.0
	hud_root.add_child(right_panel)
	var right_margin := _margin(right_panel, 12)
	var right_box := _vbox(right_margin, 5)
	hud_score = _label("ĐIỂM  0", 21, Color(0.68, 0.95, 0.75))
	right_box.add_child(hud_score)
	hud_lanterns = _label("ĐÈN  0/5", 18, Color(1.0, 0.82, 0.42))
	right_box.add_child(hud_lanterns)
	hud_capacity = _label("TÚI  0/10", 15, Color(0.8, 0.88, 1.0))
	right_box.add_child(hud_capacity)
	hud_wind = _label("", 15, Color(0.55, 0.9, 1.0))
	right_box.add_child(hud_wind)
	hud_fps = _label("", 13, Color(0.5, 0.62, 0.78))
	right_box.add_child(hud_fps)

	var slots_panel := _panel()
	slots_panel.anchor_left = 0.0
	slots_panel.anchor_top = 1.0
	slots_panel.anchor_right = 0.0
	slots_panel.anchor_bottom = 1.0
	slots_panel.offset_left = 18.0
	slots_panel.offset_top = -140.0
	slots_panel.offset_right = 660.0
	slots_panel.offset_bottom = -18.0
	hud_root.add_child(slots_panel)
	var slots_margin := _margin(slots_panel, 12)
	var slots_box := _vbox(slots_margin, 6)
	hud_slots_label = _label("ĐOM ĐÓM  0/10", 14, Color(0.8, 0.86, 1.0))
	slots_box.add_child(hud_slots_label)
	var slot_row := _hbox(slots_box, 5)
	for i in 20:
		var slot := ColorRect.new()
		slot.custom_minimum_size = Vector2(24.0, 24.0)
		slot.color = Color(0.12, 0.16, 0.24, 0.9)
		slot_row.add_child(slot)
		hud_slots.append(slot)
	var cooldown_row := _hbox(slots_box, 8)
	hud_dash = _bar(cooldown_row)
	hud_dash_label = _label("Lướt", 12, Color(0.62, 0.78, 1.0))
	cooldown_row.add_child(hud_dash_label)
	hud_pulse = _bar(cooldown_row)
	hud_pulse_label = _label("Xung", 12, Color(1.0, 0.62, 0.72))
	cooldown_row.add_child(hud_pulse_label)

	hud_prompt = _label("", 18, Color(1.0, 0.9, 0.55))
	hud_prompt.anchor_left = 0.5
	hud_prompt.anchor_top = 1.0
	hud_prompt.anchor_right = 0.5
	hud_prompt.anchor_bottom = 1.0
	hud_prompt.offset_left = -330.0
	hud_prompt.offset_top = -112.0
	hud_prompt.offset_right = 330.0
	hud_prompt.offset_bottom = -76.0
	hud_prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_root.add_child(hud_prompt)

	hud_warning = _label("", 18, Color(1.0, 0.48, 0.42))
	hud_warning.anchor_left = 0.5
	hud_warning.anchor_top = 0.0
	hud_warning.anchor_right = 0.5
	hud_warning.anchor_bottom = 0.0
	hud_warning.offset_left = -300.0
	hud_warning.offset_top = 88.0
	hud_warning.offset_right = 300.0
	hud_warning.offset_bottom = 126.0
	hud_warning.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_root.add_child(hud_warning)

	var compass_panel := _panel()
	compass_panel.anchor_left = 1.0
	compass_panel.anchor_top = 1.0
	compass_panel.anchor_right = 1.0
	compass_panel.anchor_bottom = 1.0
	compass_panel.offset_left = -210.0
	compass_panel.offset_top = -144.0
	compass_panel.offset_right = -18.0
	compass_panel.offset_bottom = -18.0
	hud_root.add_child(compass_panel)
	var compass_margin := _margin(compass_panel, 8)
	var compass_box := _vbox(compass_margin, 2)
	hud_compass_arrow = _label("▲", 38, Color(1.0, 0.82, 0.42))
	hud_compass_arrow.custom_minimum_size = Vector2(48.0, 48.0)
	hud_compass_arrow.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_compass_arrow.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hud_compass_arrow.pivot_offset = Vector2(24.0, 24.0)
	compass_box.add_child(hud_compass_arrow)
	hud_compass_label = _label("", 12, Color(0.68, 0.8, 0.95))
	hud_compass_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	compass_box.add_child(hud_compass_label)


func _bar(parent: Node) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.custom_minimum_size = Vector2(88.0, 10.0)
	bar.max_value = 1.0
	bar.value = 1.0
	bar.show_percentage = false
	bar.add_theme_stylebox_override("background", _button_style(Color(0.08, 0.1, 0.16, 0.95), Color(0.18, 0.25, 0.4)))
	bar.add_theme_stylebox_override("fill", _button_style(Color(0.3, 0.62, 0.95), Color(0.5, 0.8, 1.0)))
	parent.add_child(bar)
	return bar


func _load_map(n: int) -> void:
	night = n
	map = _read_json(MAP_PATHS[n])


func _reset_state() -> void:
	var spawn: Array = map.get("player_spawn", [0, 0, 0])
	pos = Vector3(float(spawn[0]), float(spawn[1]), float(spawn[2]))
	safe_pos = pos
	vy = 0.0
	on_ground = true
	move_dir = Vector3.ZERO
	dash_t = 0.0
	dash_cd = 0.0
	pulse_cd = 0.0
	invuln = 0.0
	wind_shield = 0.0
	jump_held = false
	dash_held = false
	interact_held = false
	pulse_held = false
	pause_held = false
	flames = int(T.get("flames", 3))
	carried = 0
	score = 0
	time_left = float(map.get("duration_s", 300))
	sim_time = 0.0
	won = false
	end_reason = ""
	successful_lights = 0
	cam_yaw = 0.0
	cam_pitch = -0.24
	player.position = pos
	player.rotation = Vector3.ZERO
	_update_camera(0.0)
	_update_hud()


func start_night(n: int) -> void:
	_load_map(n)
	_build_world()
	_reset_state()
	menu_root.visible = false
	intro_root.visible = false
	settings_root.visible = false
	controls_root.visible = false
	pause_root.visible = false
	end_root.visible = false
	leaderboard_root.visible = false
	hud_root.visible = true
	state = "playing"
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	audio.unlock()
	audio.play("ui")


func _show_menu() -> void:
	state = "menu"
	menu_root.visible = true
	intro_root.visible = false
	settings_root.visible = false
	controls_root.visible = false
	pause_root.visible = false
	end_root.visible = false
	leaderboard_root.visible = false
	hud_root.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	audio.play("ui")


func _show_intro(n: int) -> void:
	intro_night = n
	_load_map(n)
	_build_world()
	_reset_state()
	var title_text := "ĐÊM %d" % n
	if map.has("name"):
		title_text += "  —  " + str(map["name"])
	intro_title.text = title_text
	match n:
		1:
			intro_desc.text = "Một hòn đảo tròn yên tĩnh, 5 ngọn đèn và những đốm sáng lang thang. Hãy học cách nhặt đom đóm, nạp dầu và giữ đèn sáng."
		2:
			intro_desc.text = "Hai hòn đảo nối bằng cây cầu hẹp. Bóng Ma Lạc xuất hiện; hãy tìm bùa gió và giữ đèn trên 30 dầu."
		3:
			intro_desc.text = "Ba tầng đảo, dốc đá, bệ nhảy và gió mạnh. Giữ ít nhất 60% số đèn sáng tới bình minh."
	intro_start.text = "Bắt đầu đêm %d" % n
	menu_root.visible = false
	intro_root.visible = true
	settings_root.visible = false
	controls_root.visible = false
	pause_root.visible = false
	end_root.visible = false
	leaderboard_root.visible = false
	hud_root.visible = false
	state = "intro"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	audio.play("ui")


func _on_intro_start() -> void:
	start_night(intro_night)


func _show_settings(from_pause: bool) -> void:
	settings_from_pause = from_pause
	menu_root.visible = false
	intro_root.visible = false
	controls_root.visible = false
	pause_root.visible = false
	leaderboard_root.visible = false
	settings_root.visible = true
	state = "settings"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	audio.play("ui")


func _close_settings() -> void:
	settings_root.visible = false
	if settings_from_pause:
		pause_root.visible = true
		state = "paused"
	else:
		menu_root.visible = true
		state = "menu"


func _show_controls() -> void:
	menu_root.visible = false
	intro_root.visible = false
	settings_root.visible = false
	pause_root.visible = false
	leaderboard_root.visible = false
	controls_root.visible = true
	state = "controls"
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	audio.play("ui")


func _pause_game() -> void:
	if state != "playing":
		return
	state = "paused"
	pause_root.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	audio.play("ui")


func _resume_game() -> void:
	if state != "paused":
		return
	pause_root.visible = false
	settings_root.visible = false
	state = "playing"
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	audio.play("ui")


func _on_retry() -> void:
	start_night(night)


func _on_next() -> void:
	if won and night < 3:
		start_night(night + 1)
	else:
		_show_menu()


func _quit_game() -> void:
	get_tree().quit()


func _on_setting_changed(value: float, key: String) -> void:
	if key == "sensitivity":
		settings["sensitivity"] = value / 100.0
	else:
		settings[key] = value / 100.0
	_update_setting_label(key, value)
	_apply_audio_settings()
	_save_settings()


func _on_color_mode_selected(index: int) -> void:
	settings["color_mode"] = "colorblind" if index == 1 else "default"
	_save_settings()
	_apply_color_mode()


func _on_facing_selected(index: int) -> void:
	settings["facing"] = "movement" if index == 1 else "camera"
	_save_settings()


func _on_text_scale_selected(index: int) -> void:
	settings["text_scale"] = 1.25 if index == 1 else 1.0
	_save_settings()


func _on_reduce_motion_toggled(value: bool) -> void:
	settings["reduce_motion"] = value
	_save_settings()


func _on_admin_toggled(value: bool) -> void:
	settings["admin"] = value
	if not value:
		cheat_invincible = false
		cheat_fuel = false
		cheat_speed = false
		cheat_reveal = false
	_save_settings()


func _apply_color_mode() -> void:
	for lantern in lanterns:
		_refresh_lantern(lantern)
	_update_hud()


func _apply_audio_settings() -> void:
	if audio == null:
		return
	audio.set_master_volume(float(settings["master"]))
	audio.set_music_volume(float(settings["music"]))
	audio.set_sfx_volume(float(settings["sfx"]))


func _load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) != OK:
		return
	settings["master"] = clampf(float(cfg.get_value("audio", "master", settings["master"])), 0.0, 1.0)
	settings["music"] = clampf(float(cfg.get_value("audio", "music", settings["music"])), 0.0, 1.0)
	settings["sfx"] = clampf(float(cfg.get_value("audio", "sfx", settings["sfx"])), 0.0, 1.0)
	settings["sensitivity"] = clampf(float(cfg.get_value("input", "sensitivity", settings["sensitivity"])), 0.5, 3.0)
	settings["color_mode"] = str(cfg.get_value("display", "color_mode", settings["color_mode"]))
	if settings["color_mode"] != "colorblind":
		settings["color_mode"] = "default"
	settings["facing"] = str(cfg.get_value("display", "facing", settings["facing"]))
	if settings["facing"] != "movement":
		settings["facing"] = "camera"
	settings["reduce_motion"] = bool(cfg.get_value("display", "reduce_motion", settings["reduce_motion"]))
	settings["text_scale"] = clampf(float(cfg.get_value("display", "text_scale", settings["text_scale"])), 1.0, 1.25)
	settings["admin"] = bool(cfg.get_value("admin", "enabled", settings["admin"]))
	bindings = DEFAULT_BINDS.duplicate()
	var raw_binds = cfg.get_value("input", "binds", {})
	if raw_binds is Dictionary:
		for action in DEFAULT_BINDS.keys():
			if raw_binds.has(action):
				bindings[action] = int(raw_binds[action])


func _save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "master", settings["master"])
	cfg.set_value("audio", "music", settings["music"])
	cfg.set_value("audio", "sfx", settings["sfx"])
	cfg.set_value("input", "sensitivity", settings["sensitivity"])
	cfg.set_value("display", "color_mode", settings["color_mode"])
	cfg.set_value("display", "facing", settings["facing"])
	cfg.set_value("display", "reduce_motion", settings["reduce_motion"])
	cfg.set_value("display", "text_scale", settings["text_scale"])
	cfg.set_value("admin", "enabled", settings["admin"])
	cfg.set_value("input", "binds", bindings)
	cfg.save(SETTINGS_PATH)


func _setup_input() -> void:
	if bindings.is_empty():
		bindings = DEFAULT_BINDS.duplicate()
	for action in DEFAULT_BINDS.keys():
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		InputMap.action_erase_events(action)
		var event := InputEventKey.new()
		event.physical_keycode = int(bindings.get(action, DEFAULT_BINDS[action]))
		InputMap.action_add_event(action, event)


func _key_name(keycode: int) -> String:
	return OS.get_keycode_string(keycode)


func _begin_rebind(action: String, button: Button) -> void:
	rebind_action = action
	button.text = "Nhấn phím..."
	rebind_status.text = "Đang đổi phím cho: " + str(BIND_LABELS.get(action, action))


func _bind_key(keycode: int) -> void:
	if rebind_action == "":
		return
	for action in bindings.keys():
		if action != rebind_action and int(bindings[action]) == keycode:
			rebind_status.text = "Phím đã dùng cho: " + str(BIND_LABELS.get(action, action))
			return
	bindings[rebind_action] = keycode
	_setup_input()
	_save_settings()
	if rebind_buttons.has(rebind_action):
		rebind_buttons[rebind_action].text = _key_name(keycode)
	rebind_status.text = "Đã đổi phím."
	rebind_action = ""


func _reset_bindings() -> void:
	bindings = DEFAULT_BINDS.duplicate()
	_setup_input()
	_save_settings()
	for action in rebind_buttons.keys():
		rebind_buttons[action].text = _key_name(int(bindings[action]))
	rebind_status.text = "Đã khôi phục phím mặc định."


func _read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Cannot open " + path)
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		push_error("Invalid JSON " + path)
		return {}
	return parsed


func _v3(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _surface_height(x: float, z: float):
	var best = null
	for platform in map.get("platforms", []):
		var kind := str(platform.get("type", ""))
		var height = null
		if kind == "circle":
			var center: Array = platform["center"]
			var d := Vector2(x - float(center[0]), z - float(center[1])).length()
			if d <= float(platform["radius_m"]):
				height = float(platform.get("height_m", 0.0))
		elif kind == "rect":
			var mn: Array = platform["min"]
			var mx: Array = platform["max"]
			if float(mn[0]) <= x and x <= float(mx[0]) and float(mn[1]) <= z and z <= float(mx[1]):
				height = float(platform.get("height_m", 0.0))
		elif kind == "ramp":
			var mn: Array = platform["min"]
			var mx: Array = platform["max"]
			if float(mn[0]) <= x and x <= float(mx[0]) and float(mn[1]) <= z and z <= float(mx[1]):
				var low := float(platform.get("height_min_m", 0.0))
				var high := float(platform.get("height_max_m", low))
				var t := 0.0
				if str(platform.get("axis", "z")) == "x":
					var span_x := float(mx[0]) - float(mn[0])
					t = (x - float(mn[0])) / span_x if span_x != 0.0 else 0.0
				else:
					var span_z := float(mx[1]) - float(mn[1])
					t = (z - float(mn[1])) / span_z if span_z != 0.0 else 0.0
				height = low + (high - low) * clampf(t, 0.0, 1.0)
		elif kind == "jump_pad":
			var center: Array = platform["center"]
			var d := Vector2(x - float(center[0]), z - float(center[1])).length()
			if d <= float(platform["radius_m"]):
				height = float(platform.get("height_m", 0.0))
		if height != null and (best == null or height > best):
			best = height
	return best


func _can_stand(x: float, z: float) -> bool:
	var height = _surface_height(x, z)
	return height == null or height <= pos.y + float(T["step_height_m"])


func _jump_pad_at(x: float, z: float, y: float) -> Dictionary:
	for platform in map.get("platforms", []):
		if str(platform.get("type", "")) != "jump_pad":
			continue
		var center: Array = platform["center"]
		var height := float(platform.get("height_m", 0.0))
		if Vector2(x - float(center[0]), z - float(center[1])).length() <= float(platform["radius_m"]) and abs(y - height) <= float(T["step_height_m"]):
			return platform
	return {}


func _wind_at(p: Vector3) -> Vector3:
	for zone in wind_zones:
		var mn: Array = zone["min"]
		var mx: Array = zone["max"]
		if float(mn[0]) <= p.x and p.x <= float(mx[0]) and float(mn[1]) <= p.z and p.z <= float(mx[1]):
			return _v3(zone.get("push", [0, 0, 0]))
	return Vector3.ZERO


func _nearest_unlit_lantern(p: Vector3) -> Dictionary:
	var best: Dictionary = {}
	var best_d := 1e20
	for lantern in lanterns:
		if bool(lantern["lit"]):
			continue
		var d := Vector2(p.x - lantern["pos"].x, p.z - lantern["pos"].z).length()
		if d < best_d:
			best_d = d
			best = lantern
	return best


func _nearest_mote(p: Vector3) -> Dictionary:
	var best: Dictionary = {}
	var best_d := 1e20
	for mote in motes:
		var d := Vector2(p.x - mote["pos"].x, p.z - mote["pos"].z).length()
		if d < best_d:
			best_d = d
			best = mote
	return best


func _all_lit() -> bool:
	if lanterns.is_empty():
		return false
	for lantern in lanterns:
		if not bool(lantern["lit"]):
			return false
	return true


func _capacity() -> int:
	return mini(int(T["capacity_max"]), int(T["carry_capacity"]) + int(T["capacity_per_light"]) * successful_lights)


func _dawn_threshold() -> int:
	return ceili(float(T["dawn_lantern_ratio"]) * lanterns.size())


func _lit_count() -> int:
	var count := 0
	for lantern in lanterns:
		if bool(lantern["lit"]):
			count += 1
	return count


func _lantern_cost(lantern: Dictionary) -> int:
	return int(T["relight_cost"]) if bool(lantern.get("ever_lit", false)) else int(T["new_light_cost"])


func _lantern_can_receive(lantern: Dictionary) -> bool:
	if bool(lantern["lit"]):
		return int(lantern["fuel"]) < int(T["lantern_fuel_max"]) and carried > 0
	return carried >= _lantern_cost(lantern)


func _nearest_receiving_lantern(p: Vector3) -> Dictionary:
	var best: Dictionary = {}
	var best_d := float(T["interact_radius"])
	var best_id := "~"
	for lantern in lanterns:
		if not _lantern_can_receive(lantern):
			continue
		var d := Vector2(p.x - lantern["pos"].x, p.z - lantern["pos"].z).length()
		var id := str(lantern["id"])
		if d < best_d or (is_equal_approx(d, best_d) and id < best_id):
			best_d = d
			best_id = id
			best = lantern
	return best


func _nearest_lantern(p: Vector3, max_distance: float) -> Dictionary:
	var best: Dictionary = {}
	var best_d := max_distance
	for lantern in lanterns:
		var d := Vector2(p.x - lantern["pos"].x, p.z - lantern["pos"].z).length()
		if d < best_d:
			best_d = d
			best = lantern
	return best


func _weakest_lit_lantern() -> Dictionary:
	var best: Dictionary = {}
	var best_fuel := 1e20
	var best_d := 1e20
	var best_id := "~"
	for lantern in lanterns:
		if not bool(lantern["lit"]):
			continue
		var fuel := int(lantern["fuel"])
		var d := Vector2(pos.x - lantern["pos"].x, pos.z - lantern["pos"].z).length()
		var id := str(lantern["id"])
		if fuel < best_fuel or (fuel == best_fuel and (d < best_d or (d == best_d and id < best_id))):
			best_fuel = fuel
			best_d = d
			best_id = id
			best = lantern
	return best


func _compass_target() -> Dictionary:
	var unlit := _nearest_unlit_lantern(pos)
	if not unlit.is_empty():
		return unlit
	return _weakest_lit_lantern()


func _wander_target(from: Vector3) -> Dictionary:
	var best: Dictionary = {}
	var best_fuel := 1e20
	var best_d := 1e20
	var best_id := "~"
	for lantern in lanterns:
		if not bool(lantern["lit"]):
			continue
		var fuel := int(lantern["fuel"])
		var d := Vector2(from.x - lantern["pos"].x, from.z - lantern["pos"].z).length()
		var id := str(lantern["id"])
		if fuel < best_fuel or (fuel == best_fuel and (d < best_d or (d == best_d and id < best_id))):
			best_fuel = fuel
			best_d = d
			best_id = id
			best = lantern
	return best


func _push_shades(lantern: Dictionary) -> void:
	for shade in shades:
		var d := Vector2(shade["pos"].x - lantern["pos"].x, shade["pos"].z - lantern["pos"].z)
		if d.length() > float(T["fuel_push_radius_m"]):
			continue
		var dir := d.normalized() if d.length() > 0.01 else Vector2.RIGHT
		shade["pos"] += Vector3(dir.x, 0.0, dir.y) * float(T["fuel_push_m"])
		shade["stun"] = 0.0
		shade["state"] = "wander"
		shade["drain_target"] = ""


func _drain_lanterns(delta: float) -> void:
	var units := {}
	for lantern in lanterns:
		if bool(lantern["lit"]):
			var lantern_id := str(lantern["id"])
			units[lantern_id] = float(units.get(lantern_id, 0.0)) + float(T["ambient_drain_per_s"])
	for shade in shades:
		if str(shade.get("state", "")) == "drain" and str(shade.get("drain_target", "")) != "":
			var shade_target := str(shade["drain_target"])
			units[shade_target] = float(units.get(shade_target, 0.0)) + float(T["shade_drain_per_s"])
	for lantern in lanterns:
		if not bool(lantern["lit"]):
			continue
		var u := float(units.get(str(lantern["id"]), 0.0))
		if u <= 0.0:
			continue
		lantern["drain_acc"] = float(lantern["drain_acc"]) + u * delta
		var changed := false
		while float(lantern["drain_acc"]) >= 1.0 and int(lantern["fuel"]) > 0:
			lantern["drain_acc"] = float(lantern["drain_acc"]) - 1.0
			lantern["fuel"] = int(lantern["fuel"]) - 1
			changed = true
		lantern["deposited"] = int(lantern["fuel"])
		if int(lantern["fuel"]) <= 0:
			lantern["fuel"] = 0
			lantern["deposited"] = 0
			lantern["lit"] = false
			lantern["drain_acc"] = 0.0
			changed = true
		if changed:
			_refresh_lantern(lantern)


func _update_game(delta: float) -> void:
	if state != "playing":
		return
	if bool(settings["admin"]):
		if cheat_invincible:
			invuln = max(invuln, 2.0)
		if cheat_fuel:
			carried = _capacity()
			for lantern in lanterns:
				lantern["lit"] = true
				lantern["fuel"] = int(T["lantern_fuel_max"])
				_refresh_lantern(lantern)
		if cheat_reveal:
			for lantern in lanterns:
				lantern["light"].light_energy = max(float(lantern["light"].light_energy), 2.0)
				lantern["light"].omni_range = max(float(lantern["light"].omni_range), 18.0)
	sim_time += delta
	time_left -= delta
	dash_cd = max(0.0, dash_cd - delta)
	pulse_cd = max(0.0, pulse_cd - delta)
	invuln = max(0.0, invuln - delta)
	wind_shield = max(0.0, wind_shield - delta)

	var input_vec := Vector2.ZERO
	if Input.is_action_pressed("move_forward"):
		input_vec.y -= 1.0
	if Input.is_action_pressed("move_back"):
		input_vec.y += 1.0
	if Input.is_action_pressed("move_left"):
		input_vec.x -= 1.0
	if Input.is_action_pressed("move_right"):
		input_vec.x += 1.0
	if input_vec.length() > 1.0:
		input_vec = input_vec.normalized()
	var forward := Vector3(-sin(cam_yaw), 0.0, -cos(cam_yaw))
	var right := Vector3(cos(cam_yaw), 0.0, -sin(cam_yaw))
	move_dir = forward * (-input_vec.y) + right * input_vec.x
	if move_dir.length() > 1.0:
		move_dir = move_dir.normalized()

	var dash_down := Input.is_action_pressed("dash")
	if dash_down and not dash_held and dash_cd <= 0.0 and on_ground and move_dir.length() > 0.05:
		dash_dir = move_dir.normalized()
		dash_t = float(T["dash_duration_s"])
		dash_cd = float(T["dash_cooldown_s"])
		audio.play("dash")
	dash_held = dash_down

	var speed_scale := 2.0 if bool(settings["admin"]) and cheat_speed else 1.0
	var velocity := Vector3.ZERO
	if dash_t > 0.0:
		dash_t = max(0.0, dash_t - delta)
		velocity = dash_dir * float(T["dash_speed_m_s"]) * speed_scale
	else:
		velocity = move_dir * float(T["player_speed"]) * speed_scale
	_try_move(velocity * delta)

	var wind := _wind_at(pos)
	if wind != Vector3.ZERO and wind_shield <= 0.0:
		pos += wind * float(T["strong_wind_speed_m_s"]) * delta
		if audio != null and randf() < delta * 2.0:
			audio.play("wind", -16.0)

	var jump_down := Input.is_action_pressed("jump")
	if jump_down and not jump_held and on_ground:
		vy = float(T["jump_velocity_m_s"])
		on_ground = false
		audio.play("jump")
	jump_held = jump_down

	var height = _surface_height(pos.x, pos.z)
	if on_ground:
		if height == null:
			on_ground = false
		elif abs(float(height) - pos.y) <= float(T["step_height_m"]):
			pos.y = float(height)
		else:
			on_ground = false

	if not on_ground:
		pos.y += vy * delta
		vy -= float(T["gravity_m_s2"]) * delta
		if jump_down and vy < -float(T["glide_fall_speed_m_s"]):
			vy = -float(T["glide_fall_speed_m_s"])
		height = _surface_height(pos.x, pos.z)
		if height != null and pos.y <= float(height) and vy <= 0.0:
			pos.y = float(height)
			vy = 0.0
			on_ground = true

	if on_ground:
		var pad := _jump_pad_at(pos.x, pos.z, pos.y)
		if not pad.is_empty():
			vy = float(pad.get("launch_velocity_m_s", 14.0))
			on_ground = false
			audio.play("jump")
		if _wind_at(pos) == Vector3.ZERO:
			safe_pos = pos

	var interact_down := Input.is_action_pressed("interact")
	if interact_down and not interact_held:
		_interact()
	interact_held = interact_down

	var pulse_down := Input.is_action_pressed("pulse")
	if pulse_down and not pulse_held and pulse_cd <= 0.0 and carried >= int(T["pulse_cost"]):
		carried -= int(T["pulse_cost"])
		pulse_cd = float(T["pulse_cooldown_s"])
		for shade in shades:
			if shade["stun"] > 0.0:
				continue
			var d := Vector2(shade["pos"].x - pos.x, shade["pos"].z - pos.z)
			if d.length() <= float(T["pulse_radius"]):
				var dir := d.normalized() if d.length() > 0.01 else Vector2.ZERO
				shade["pos"] += Vector3(dir.x, 0.0, dir.y) * float(T["pulse_push_m"])
				shade["stun"] = float(T["pulse_stun_s"])
				score += int(T["score"]["per_stun"])
		audio.play("pulse")
	pulse_held = pulse_down

	for charm in charms:
		if not bool(charm["collected"]) and Vector2(pos.x - charm["pos"].x, pos.z - charm["pos"].z).length() <= float(T["wind_charm_radius_m"]):
			charm["collected"] = true
			wind_shield = float(T["wind_charm_duration_s"])
			audio.play("charm")

	var wisp_speed := float(T.get("night%d_lost_wisp_speed_m_s" % night, T["lost_wisp_speed_m_s"]))
	for wisp in wisps:
		var target := _nearest_unlit_lantern(wisp["pos"])
		if not target.is_empty():
			var d := Vector2(target["pos"].x - wisp["pos"].x, target["pos"].z - wisp["pos"].z)
			var length := d.length()
			if length > 0.05:
				wisp["pos"] += Vector3(d.x / length, 0.0, d.y / length) * minf(length, wisp_speed * delta)
		if wind_shield <= 0.0 and Vector2(pos.x - wisp["pos"].x, pos.z - wisp["pos"].z).length() <= float(T["lost_wisp_radius_m"]):
			var d := Vector2(pos.x - wisp["pos"].x, pos.z - wisp["pos"].z)
			var length := d.length()
			if length > 0.01:
				pos += Vector3(d.x / length, 0.0, d.y / length) * float(T["lost_wisp_push_m_s"]) * delta

	var shade_speed := float(T.get("night%d_shade_speed" % night, T["shade_speed"]))
	for shade in shades:
		shade["drain_target"] = ""
		if shade["stun"] > 0.0:
			shade["stun"] = max(0.0, shade["stun"] - delta)
			shade["state"] = "stunned"
			continue
		var safe := false
		for lantern in lanterns:
			if bool(lantern["lit"]) and int(lantern["fuel"]) >= int(T["safe_fuel_threshold"]) and Vector2(shade["pos"].x - lantern["pos"].x, shade["pos"].z - lantern["pos"].z).length() <= float(T["safe_radius"]):
				safe = true
				break
		if safe:
			shade["state"] = "wander"
			continue
		var d := Vector2(pos.x - shade["pos"].x, pos.z - shade["pos"].z)
		var distance := d.length()
		if distance <= float(T["shade_chase_radius_m"]):
			shade["state"] = "chase"
			if distance > 0.05:
				shade["pos"] += Vector3(d.x / distance, 0.0, d.y / distance) * minf(distance, shade_speed * delta)
			if distance <= float(T["shade_hit_radius"]) and invuln <= 0.0:
				_hit_by_shade()
				if state != "playing":
					return
		else:
			var target: Dictionary = {}
			var target_d := 1e20
			var target_id := "~"
			for lantern in lanterns:
				if not bool(lantern["lit"]):
					continue
				var ld := Vector2(shade["pos"].x - lantern["pos"].x, shade["pos"].z - lantern["pos"].z).length()
				if ld <= float(T["shade_drain_radius_m"]) and (ld < target_d or (ld == target_d and str(lantern["id"]) < target_id)):
					target_d = ld
					target_id = str(lantern["id"])
					target = lantern
			if not target.is_empty():
				shade["state"] = "drain"
				shade["drain_target"] = str(target["id"])
			else:
				shade["state"] = "wander"
				var wander := _wander_target(shade["pos"])
				if not wander.is_empty():
					var wd := Vector2(wander["pos"].x - shade["pos"].x, wander["pos"].z - shade["pos"].z)
					var wl := wd.length()
					if wl > float(T["shade_drain_radius_m"]) + 0.01:
						var move := minf(wl - float(T["shade_drain_radius_m"]), shade_speed * delta)
						shade["pos"] += Vector3(wd.x / wl, 0.0, wd.y / wl) * move

	if state != "playing":
		return
	if not (bool(settings["admin"]) and cheat_fuel):
		_drain_lanterns(delta)
	if state != "playing":
		return
	if pos.y < float(T["fall_y_m"]) and invuln <= 0.0:
		_fall()
		if state != "playing":
			return
	if time_left <= 0.0:
		if _lit_count() >= _dawn_threshold():
			_end_game(true, "dawn")
		else:
			_end_game(false, "not_enough_lanterns")


func _try_move(delta_move: Vector3) -> void:
	var nx := pos.x + delta_move.x
	var nz := pos.z + delta_move.z
	if _can_stand(nx, nz):
		pos.x = nx
		pos.z = nz
	else:
		if _can_stand(nx, pos.z):
			pos.x = nx
		if _can_stand(pos.x, nz):
			pos.z = nz


func _interact() -> void:
	var best := _nearest_receiving_lantern(pos)
	if not best.is_empty():
		var before := int(best["fuel"])
		if bool(best["lit"]):
			var needed := ceili((float(T["lantern_fuel_max"]) - float(before)) / float(T["refuel_fuel_per_mote"]))
			var used := mini(carried, needed)
			carried -= used
			best["fuel"] = mini(int(T["lantern_fuel_max"]), before + used * int(T["refuel_fuel_per_mote"]))
			best["deposited"] = int(best["fuel"])
			audio.play("deposit")
		else:
			var mode := "relight" if bool(best["ever_lit"]) else "new"
			var cost := int(T["relight_cost"]) if mode == "relight" else int(T["new_light_cost"])
			carried -= cost
			best["fuel"] = int(T["lantern_fuel_max"])
			best["deposited"] = int(best["fuel"])
			best["lit"] = true
			best["ever_lit"] = true
			best["drain_acc"] = 0.0
			if mode == "relight":
				best["relit_count"] = int(best["relit_count"]) + 1
			successful_lights += 1
			score += int(T["score"]["per_relight"]) if mode == "relight" else int(T["score"]["per_lantern"])
			audio.play("lantern")
		if before < int(T["safe_fuel_threshold"]) and int(best["fuel"]) >= int(T["safe_fuel_threshold"]):
			_push_shades(best)
		_refresh_lantern(best)
		return
	var mote := _nearest_mote(pos)
	if not mote.is_empty() and Vector2(pos.x - mote["pos"].x, pos.z - mote["pos"].z).length() <= float(T["pickup_radius"]) and carried < _capacity():
		motes.erase(mote)
		if is_instance_valid(mote["node"]):
			mote["node"].queue_free()
		carried += 1
		score += int(T["score"]["per_mote"])
		audio.play("pickup")


func _hit_by_shade() -> void:
	flames = max(0, flames - 1)
	var dropped := int(floor(carried * float(T["hit_drop_ratio"])))
	carried -= dropped
	invuln = float(T["invuln_s"])
	audio.play("hit")
	_flash(Color(0.7, 0.12, 0.18))
	if flames <= 0:
		_end_game(false, "no_flames")


func _fall() -> void:
	flames = max(0, flames - 1)
	var dropped := int(floor(carried * float(T["hit_drop_ratio"])))
	carried -= dropped
	pos = safe_pos
	vy = 0.0
	on_ground = true
	invuln = float(T["invuln_s"])
	audio.play("hit")
	_flash(Color(0.18, 0.35, 0.8))
	if flames <= 0:
		_end_game(false, "no_flames")


func _end_game(did_win: bool, reason: String) -> void:
	if state != "playing":
		return
	state = "won" if did_win else "lost"
	won = did_win
	end_reason = reason
	if did_win:
		score += int(T["score"]["dawn_bonus"]) + flames * int(T["score"]["per_flame_left"])
		audio.play("win")
	else:
		audio.play("lose")
	end_title.text = "BÌNH MINH" if did_win else "MÀN ĐÊM NUỐT CHỬNG"
	end_title.add_theme_color_override("font_color", Color(0.72, 0.95, 0.62) if did_win else Color(1.0, 0.5, 0.45))
	end_detail.text = _reason_text(reason)
	end_score.text = "ĐIỂM  %d" % score
	end_next.visible = did_win and night < 3
	end_leaderboard.visible = ((did_win and night == 3) or not did_win) and not bool(settings["admin"])
	end_root.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_update_hud()


func _reason_text(reason: String) -> String:
	match reason:
		"dawn":
			return "Bình minh đã đến. Bạn giữ được %d/%d ngọn đèn sáng." % [_lit_count(), lanterns.size()]
		"not_enough_lanterns":
			return "Bình minh đã đến nhưng bạn chỉ giữ %d/%d đèn. Cần ít nhất %d đèn sáng." % [_lit_count(), lanterns.size(), _dawn_threshold()]
		"no_flames":
			return "Ngọn lửa cuối cùng đã tắt. Hãy thử lại đêm nay."
		_:
			return reason


func _flash(color: Color) -> void:
	if bool(settings["reduce_motion"]):
		return
	var rect := ColorRect.new()
	rect.color = Color(color.r, color.g, color.b, 0.42)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_root.add_child(rect)
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	var tween := create_tween()
	tween.tween_property(rect, "color:a", 0.0, 0.45)
	tween.tween_callback(rect.queue_free)


func _update_camera(delta: float) -> void:
	var target := pos + Vector3(0.0, 1.25, 0.0)
	var distance := cam_distance
	if state == "menu" or state == "intro" or state == "controls" or state == "settings":
		target = Vector3(-5.0, 2.2, 0.0)
		distance = 16.0
		if not bool(settings["reduce_motion"]):
			cam_yaw += delta * 0.08
	var horizontal := cos(cam_pitch) * distance
	var offset := Vector3(sin(cam_yaw) * horizontal, 2.0 - sin(cam_pitch) * distance, cos(cam_yaw) * horizontal)
	var desired := target + offset
	if delta <= 0.0:
		camera.position = desired
	else:
		camera.position = camera.position.lerp(desired, 1.0 - exp(-9.0 * delta))
	camera.look_at(target, Vector3.UP)


func _process(delta: float) -> void:
	if state == "playing":
		_update_game(minf(delta, 0.05))
		_update_camera(delta)
		_update_visuals(delta)
		_update_hud()
		_update_compass()
	elif state == "menu" or state == "intro" or state == "controls" or state == "settings":
		_update_camera(delta)
		_update_visuals(delta)
	elif state == "paused" or state == "won" or state == "lost":
		_update_visuals(delta)
		_update_compass()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton or (event is InputEventKey and event.pressed):
		if audio != null:
			audio.unlock()
	if event is InputEventMouseMotion and state == "playing":
		cam_yaw -= event.relative.x * 0.0024 * float(settings["sensitivity"])
		cam_pitch = clampf(cam_pitch - event.relative.y * 0.0019 * float(settings["sensitivity"]), -0.78, 0.22)
	if event is InputEventKey and event.pressed and not event.echo:
		if rebind_action != "":
			_bind_key(event.physical_keycode)
			return
		if event.ctrl_pressed and event.shift_pressed and bool(settings["admin"]):
			_handle_admin_key(event.physical_keycode)
			return
		if event.physical_keycode == KEY_ESCAPE:
			if state == "playing":
				_pause_game()
			elif state == "paused":
				_resume_game()
			elif state == "intro" or state == "controls" or state == "settings" or state == "leaderboard":
				_show_menu()


func _handle_admin_key(keycode: int) -> void:
	match keycode:
		KEY_1:
			cheat_invincible = not cheat_invincible
		KEY_2:
			cheat_fuel = not cheat_fuel
		KEY_3:
			if state == "playing":
				_end_game(true, "dawn")
		KEY_4:
			cheat_speed = not cheat_speed
		KEY_5:
			cheat_reveal = not cheat_reveal
		KEY_6:
			var turn_on := not (cheat_invincible and cheat_fuel and cheat_speed and cheat_reveal)
			cheat_invincible = turn_on
			cheat_fuel = turn_on
			cheat_speed = turn_on
			cheat_reveal = turn_on


func _update_visuals(delta: float) -> void:
	player.position = pos
	var reduced := bool(settings["reduce_motion"])
	var face_movement := str(settings["facing"]) == "movement" and move_dir.length() > 0.05
	var desired_yaw := atan2(move_dir.x, move_dir.z) if face_movement else atan2(-sin(cam_yaw), -cos(cam_yaw))
	player.rotation.y = lerp_angle(player.rotation.y, desired_yaw, minf(1.0, delta * 12.0))
	if move_dir.length() > 0.05 and on_ground and not reduced:
		player_body.position.y = 0.85 + sin(sim_time * 9.0) * 0.025
	else:
		player_body.position.y = 0.85
	player_light.light_energy = 1.1 + (0.0 if reduced else sin(sim_time * 4.0) * 0.15)
	for mote in motes:
		var bob := 0.0 if reduced else sin(sim_time * 2.2 + float(mote["phase"])) * 0.13
		mote["node"].position = Vector3(mote["pos"].x, mote["pos"].y + 0.45 + bob, mote["pos"].z)
		if not reduced:
			mote["node"].rotate_y(delta * 1.8)
	for shade in shades:
		var h = _surface_height(shade["pos"].x, shade["pos"].z)
		var y := (float(h) if h != null else 0.0) + 0.75
		shade["node"].position = Vector3(shade["pos"].x, y, shade["pos"].z)
		shade["mat"].emission_energy_multiplier = 2.2 if str(shade.get("state", "")) == "drain" else 1.2
		if shade["stun"] > 0.0:
			shade["node"].rotate_y(delta * 8.0)
	for wisp in wisps:
		wisp["node"].position = Vector3(wisp["pos"].x, wisp["pos"].y + 0.8 + sin(sim_time * 3.0 + wisp["pos"].x) * 0.15, wisp["pos"].z)
	for charm in charms:
		if bool(charm["collected"]):
			charm["node"].visible = false
		else:
			charm["node"].position = Vector3(charm["pos"].x, charm["pos"].y + 0.9 + sin(sim_time * 2.5 + charm["pos"].z) * 0.12, charm["pos"].z)
			charm["node"].rotate_y(delta * 2.0)
	if not bell.is_empty() and is_instance_valid(bell["node"]):
		bell["light"].light_energy = 1.1 + sin(sim_time * 2.0) * 0.2


func _update_hud() -> void:
	if hud_root == null:
		return
	hud_flames.text = "LỬA  %d/3" % flames
	var seconds := int(ceil(max(0.0, time_left)))
	hud_timer.text = "%02d:%02d" % [int(seconds / 60), seconds % 60]
	hud_timer.add_theme_color_override("font_color", Color(1.0, 0.45, 0.4) if time_left < 10.0 else Color(0.82, 0.92, 1.0))
	hud_night.text = "ĐÊM %d  •  %s" % [night, str(map.get("name", ""))]
	hud_score.text = "ĐIỂM  %d" % score
	var lit := _lit_count()
	var threshold := _dawn_threshold()
	hud_lanterns.text = "ĐÈN  %d/%d  •  mốc %d" % [lit, lanterns.size(), threshold]
	hud_capacity.text = "TÚI  %d/%d" % [carried, _capacity()]
	hud_slots_label.text = "ĐOM ĐÓM  %d/%d" % [carried, _capacity()]
	var colorblind := str(settings["color_mode"]) == "colorblind"
	hud_lanterns.add_theme_color_override("font_color", Color(0.72, 0.95, 1.0) if colorblind else Color(1.0, 0.82, 0.42))
	var target := _nearest_lantern(pos, 12.0)
	if target.is_empty():
		target = _nearest_lantern(pos, 1e9)
	if target.is_empty():
		hud_fuel_label.text = "DẦU  --"
		hud_fuel.value = 0.0
		hud_fuel.modulate = Color(1.0, 1.0, 1.0, 0.5)
	else:
		var fuel := int(target["fuel"])
		var target_state := "SÁNG" if bool(target["lit"]) else "TẮT"
		hud_fuel_label.text = "DẦU  %s  %s  %d/100" % [str(target["id"]), target_state, fuel]
		hud_fuel.value = float(fuel)
		var blink := fuel < int(T["safe_fuel_threshold"]) and int(sim_time * 2.0) % 2 == 0
		var alpha := 0.35 if blink else 1.0
		hud_fuel.modulate = Color(0.75, 0.92, 1.0, alpha) if colorblind else Color(1.0, 0.7, 0.45, alpha)
	if wind_shield > 0.0:
		hud_wind.text = "BÙA GIÓ  %.1fs" % wind_shield
	elif _wind_at(pos) != Vector3.ZERO:
		hud_wind.text = "GIÓ MẠNH"
	else:
		hud_wind.text = ""
	for i in hud_slots.size():
		hud_slots[i].visible = i < _capacity()
		if i < carried:
			hud_slots[i].color = Color(0.4, 0.9, 1.0) if colorblind else Color(1.0, 0.72, 0.2)
		else:
			hud_slots[i].color = Color(0.12, 0.16, 0.24, 0.9)
	hud_dash.value = 1.0 if dash_cd <= 0.0 else 1.0 - dash_cd / max(0.001, float(T["dash_cooldown_s"]))
	hud_pulse.value = 1.0 if pulse_cd <= 0.0 else 1.0 - pulse_cd / max(0.001, float(T["pulse_cooldown_s"]))
	hud_dash_label.text = "Lướt" if dash_cd <= 0.0 else "Lướt %.1f" % dash_cd
	hud_pulse_label.text = "Xung" if pulse_cd <= 0.0 else "Xung %.1f" % pulse_cd
	hud_fps.text = "%d FPS" % Engine.get_frames_per_second()
	hud_prompt.text = _prompt_text()
	hud_warning.text = _warning_text()
	hud_warning.visible = hud_warning.text != ""
	var low_fuel := false
	for lantern in lanterns:
		if bool(lantern["lit"]) and int(lantern["fuel"]) < int(T["safe_fuel_threshold"]):
			low_fuel = true
			break
	var warning_alpha := 0.35 if low_fuel and int(sim_time * 2.0) % 2 == 0 else 1.0
	hud_warning.modulate = Color(1.0, 1.0, 1.0, warning_alpha)
	_update_compass()


func _prompt_text() -> String:
	var lantern := _nearest_receiving_lantern(pos)
	if not lantern.is_empty():
		if bool(lantern["lit"]):
			var needed := ceili((float(T["lantern_fuel_max"]) - float(lantern["fuel"])) / float(T["refuel_fuel_per_mote"]))
			var used := mini(carried, needed)
			return "E  Nạp dầu  •  %d/100  •  dùng %d đom" % [int(lantern["fuel"]), used]
		var mode := "Thắp lại" if bool(lantern["ever_lit"]) else "Thắp đèn mới"
		return "E  %s  •  %d đom" % [mode, _lantern_cost(lantern)]
	var near := _nearest_lantern(pos, float(T["interact_radius"]))
	if not near.is_empty():
		if bool(near["lit"]):
			if int(near["fuel"]) >= int(T["lantern_fuel_max"]):
				return "Đèn đã đầy dầu"
			return "Cần đom đóm để nạp dầu"
		return "Cần %d đom để %s" % [_lantern_cost(near), "thắp lại" if bool(near["ever_lit"]) else "thắp đèn mới"]
	var mote := _nearest_mote(pos)
	if not mote.is_empty() and Vector2(pos.x - mote["pos"].x, pos.z - mote["pos"].z).length() <= float(T["pickup_radius"]):
		if carried >= _capacity():
			return "Đã đầy %d đom đóm" % _capacity()
		return "E  Nhặt đom đóm"
	if _lit_count() >= _dawn_threshold():
		return "Giữ đèn sáng tới bình minh"
	return ""


func _warning_text() -> String:
	if flames <= 1:
		return "⚠ NGỌN LỬA CUỐI CÙNG!"
	if time_left <= 10.0:
		return "⚠ 10 GIÂY CUỐI — BÌNH MINH SẮP ĐẾN!"
	for lantern in lanterns:
		if bool(lantern["lit"]) and int(lantern["fuel"]) < int(T["safe_fuel_threshold"]):
			return "⚠ DẦU ĐÈN DƯỚI 30 — VÙNG AN TOÀN ĐÃ MẤT"
	for shade in shades:
		if Vector2(pos.x - shade["pos"].x, pos.z - shade["pos"].z).length() <= 5.0:
			return "⚠ BÓNG TỐI ĐANG ĐẾN GẦN"
	for wisp in wisps:
		if wind_shield <= 0.0 and Vector2(pos.x - wisp["pos"].x, pos.z - wisp["pos"].z).length() <= 3.0:
			return "⚠ BÙA GIÓ ĐÃ HẾT!"
	return ""


func _update_compass() -> void:
	if hud_compass_arrow == null:
		return
	var lantern := _compass_target()
	if lantern.is_empty():
		hud_compass_arrow.visible = false
		hud_compass_label.text = "Không còn đèn"
		return
	var to := Vector2(lantern["pos"].x - pos.x, lantern["pos"].z - pos.z)
	hud_compass_arrow.visible = true
	hud_compass_arrow.rotation = atan2(to.x, -to.y) + cam_yaw
	var tag := "Đèn yếu nhất" if bool(lantern["lit"]) else "Đèn gần nhất"
	hud_compass_label.text = "%s  %.0fm  •  %d/100" % [tag, to.length(), int(lantern["fuel"])]


func _build_world() -> void:
	for child in world_root.get_children():
		child.queue_free()
	lanterns.clear()
	motes.clear()
	shades.clear()
	wisps.clear()
	charms.clear()
	wind_zones = map.get("wind_zones", [])
	jump_pads.clear()
	bell = {}
	rng.seed = 1000 + night
	_build_water()
	_build_moon()
	_build_stars()
	_build_platforms()
	_build_ground_details()
	_build_rocks()
	_build_lanterns()
	_build_motes()
	_build_shades()
	_build_wisps()
	_build_charms()
	_build_bell()
	_build_wind_zones()
	_build_jump_pads()


func _build_water() -> void:
	var plane := PlaneMesh.new()
	plane.size = Vector2(240.0, 240.0)
	var water := MeshInstance3D.new()
	water.mesh = plane
	water.position = Vector3(0.0, -1.6, 0.0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.02, 0.09, 0.2, 0.9)
	mat.metallic = 0.5
	mat.roughness = 0.1
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = Color(0.01, 0.045, 0.12)
	mat.emission_energy_multiplier = 0.7
	water.material_override = mat
	world_root.add_child(water)


func _build_moon() -> void:
	var moon := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 3.6
	mesh.height = 7.2
	mesh.radial_segments = 32
	mesh.rings = 16
	moon.mesh = mesh
	moon.position = Vector3(38.0, 22.0, -64.0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.92, 0.72)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.84, 0.55)
	mat.emission_energy_multiplier = 1.5
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	moon.material_override = mat
	world_root.add_child(moon)


func _build_stars() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.8, 0.86, 1.0)
	mat.emission_enabled = true
	mat.emission = Color(0.7, 0.8, 1.0)
	mat.emission_energy_multiplier = 2.6
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for i in 140:
		var star := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = rng.randf_range(0.12, 0.28)
		sphere.height = sphere.radius * 2.0
		star.mesh = sphere
		var angle := rng.randf_range(0.0, TAU)
		var radius := rng.randf_range(55.0, 110.0)
		star.position = Vector3(cos(angle) * radius, rng.randf_range(18.0, 70.0), sin(angle) * radius)
		star.material_override = mat
		world_root.add_child(star)


func _build_platforms() -> void:
	for platform in map.get("platforms", []):
		var kind := str(platform.get("type", ""))
		if kind == "circle":
			var center: Array = platform["center"]
			var radius := float(platform["radius_m"])
			var height := float(platform.get("height_m", 0.0))
			var cylinder := CylinderMesh.new()
			cylinder.top_radius = radius
			cylinder.bottom_radius = radius
			cylinder.height = max(0.4, height + 0.4)
			cylinder.radial_segments = 72
			cylinder.rings = 4
			var node := MeshInstance3D.new()
			node.mesh = cylinder
			node.position = Vector3(float(center[0]), height - cylinder.height * 0.5, float(center[1]))
			node.material_override = _ground_material(height)
			world_root.add_child(node)
			_add_edge_ring(float(center[0]), float(center[1]), radius, height)
		elif kind == "rect":
			var mn: Array = platform["min"]
			var mx: Array = platform["max"]
			var height := float(platform.get("height_m", 0.0))
			var box := BoxMesh.new()
			box.size = Vector3(float(mx[0]) - float(mn[0]), 0.4, float(mx[1]) - float(mn[1]))
			var node := MeshInstance3D.new()
			node.mesh = box
			node.position = Vector3((float(mn[0]) + float(mx[0])) * 0.5, height - 0.2, (float(mn[1]) + float(mx[1])) * 0.5)
			node.material_override = _ground_material(height)
			world_root.add_child(node)
		elif kind == "ramp":
			var mn: Array = platform["min"]
			var mx: Array = platform["max"]
			var low := float(platform.get("height_min_m", 0.0))
			var high := float(platform.get("height_max_m", low))
			var span_z := float(mx[1]) - float(mn[1])
			var span_x := float(mx[0]) - float(mn[0])
			var box := BoxMesh.new()
			var length := sqrt(span_z * span_z + (high - low) * (high - low))
			box.size = Vector3(span_x, 0.4, length)
			var node := MeshInstance3D.new()
			node.mesh = box
			node.position = Vector3((float(mn[0]) + float(mx[0])) * 0.5, (low + high) * 0.5, (float(mn[1]) + float(mx[1])) * 0.5)
			node.rotation.x = -atan((high - low) / span_z) if span_z != 0.0 else 0.0
			node.material_override = _ground_material(high)
			world_root.add_child(node)


func _build_ground_details() -> void:
	var ring_mat := StandardMaterial3D.new()
	ring_mat.albedo_color = Color(0.12, 0.24, 0.2)
	ring_mat.roughness = 0.9
	for platform in map.get("platforms", []):
		if str(platform.get("type", "")) != "circle":
			continue
		var center: Array = platform["center"]
		var radius := float(platform["radius_m"])
		var height := float(platform.get("height_m", 0.0))
		if height > 0.1 or radius < 18.0:
			continue
		for ring_radius in [8.0, 15.0, 22.0, 29.0, 35.0]:
			if ring_radius >= radius - 1.5:
				continue
			var ring := MeshInstance3D.new()
			var torus := TorusMesh.new()
			torus.inner_radius = ring_radius - 0.06
			torus.outer_radius = ring_radius + 0.06
			torus.rings = 96
			torus.ring_segments = 4
			ring.mesh = torus
			ring.position = Vector3(float(center[0]), height + 0.015, float(center[1]))
			ring.material_override = ring_mat
			world_root.add_child(ring)
	var tuft_mat := StandardMaterial3D.new()
	tuft_mat.albedo_color = Color(0.1, 0.26, 0.16)
	tuft_mat.roughness = 0.95
	for i in 100:
		var angle := rng.randf_range(0.0, TAU)
		var radius := sqrt(rng.randf()) * 38.0
		var p := Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
		var h = _surface_height(p.x, p.z)
		if h == null or float(h) > 0.2:
			continue
		p.y = float(h)
		var tuft := MeshInstance3D.new()
		var cone := CylinderMesh.new()
		cone.top_radius = 0.0
		cone.bottom_radius = rng.randf_range(0.08, 0.16)
		cone.height = rng.randf_range(0.3, 0.7)
		tuft.mesh = cone
		tuft.position = p + Vector3(0.0, cone.height * 0.5, 0.0)
		tuft.rotation = Vector3(rng.randf_range(-0.12, 0.12), rng.randf_range(0.0, TAU), rng.randf_range(-0.12, 0.12))
		tuft.material_override = tuft_mat
		world_root.add_child(tuft)


func _ground_material(height: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.roughness = 0.82
	mat.emission_enabled = true
	if height <= 0.1:
		mat.albedo_color = Color(0.16, 0.34, 0.28)
		mat.emission = Color(0.025, 0.055, 0.04)
		mat.emission_energy_multiplier = 0.9
	elif height < 6.0:
		mat.albedo_color = Color(0.25, 0.23, 0.31)
		mat.emission = Color(0.045, 0.035, 0.065)
		mat.emission_energy_multiplier = 0.8
	else:
		mat.albedo_color = Color(0.35, 0.3, 0.41)
		mat.emission = Color(0.07, 0.05, 0.09)
		mat.emission_energy_multiplier = 0.8
	return mat


func _build_rocks() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.16, 0.18, 0.23)
	mat.roughness = 0.92
	for i in 34:
		var angle := rng.randf_range(0.0, TAU)
		var radius := sqrt(rng.randf()) * 36.0
		var p := Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
		var h = _surface_height(p.x, p.z)
		if h == null:
			continue
		p.y = float(h)
		var rock := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radius = rng.randf_range(0.18, 0.55)
		mesh.height = mesh.radius * rng.randf_range(0.35, 0.8)
		rock.mesh = mesh
		rock.position = p + Vector3(0.0, mesh.height * 0.35, 0.0)
		rock.rotation = Vector3(rng.randf_range(-0.3, 0.3), rng.randf_range(0.0, TAU), rng.randf_range(-0.3, 0.3))
		rock.material_override = mat
		world_root.add_child(rock)


func _add_edge_ring(cx: float, cz: float, radius: float, height: float) -> void:
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = max(0.5, radius - 0.12)
	torus.outer_radius = radius + 0.18
	torus.rings = 96
	torus.ring_segments = 6
	ring.mesh = torus
	ring.position = Vector3(cx, height + 0.02, cz)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.12, 0.38, 0.34)
	mat.emission_enabled = true
	mat.emission = Color(0.06, 0.3, 0.26)
	mat.emission_energy_multiplier = 0.9
	ring.material_override = mat
	world_root.add_child(ring)


func _build_lanterns() -> void:
	for item in map.get("lanterns", []):
		var p := _v3(item["pos"])
		var node := Node3D.new()
		node.position = p
		world_root.add_child(node)
		var post := MeshInstance3D.new()
		var post_mesh := CylinderMesh.new()
		post_mesh.top_radius = 0.11
		post_mesh.bottom_radius = 0.16
		post_mesh.height = 2.7
		post.mesh = post_mesh
		post.position = Vector3(0.0, 1.35, 0.0)
		var post_mat := StandardMaterial3D.new()
		post_mat.albedo_color = Color(0.14, 0.1, 0.08)
		post.material_override = post_mat
		node.add_child(post)
		var cage := MeshInstance3D.new()
		var cage_mesh := SphereMesh.new()
		cage_mesh.radius = 0.56
		cage_mesh.height = 1.12
		cage.mesh = cage_mesh
		cage.position = Vector3(0.0, 2.95, 0.0)
		var cage_mat := StandardMaterial3D.new()
		cage_mat.albedo_color = Color(0.2, 0.32, 0.5)
		cage_mat.emission_enabled = true
		cage_mat.emission = Color(0.15, 0.3, 0.65)
		cage_mat.emission_energy_multiplier = 0.8
		cage.material_override = cage_mat
		node.add_child(cage)
		var light := OmniLight3D.new()
		light.position = Vector3(0.0, 2.95, 0.0)
		light.light_color = Color(0.45, 0.62, 1.0)
		light.light_energy = 1.0
		light.omni_range = 9.0
		light.shadow_enabled = false
		node.add_child(light)
		var label := Label3D.new()
		label.position = Vector3(0.0, 3.85, 0.0)
		label.font_size = 30
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.outline_size = 6
		label.modulate = Color(0.75, 0.85, 1.0)
		label.text = "%s  TẮT  0/100" % str(item.get("id", "L"))
		node.add_child(label)
		var lantern := {"id": str(item.get("id", "L")), "pos": p, "fuel": 0, "deposited": 0, "lit": false,
			"ever_lit": false, "relit_count": 0, "drain_acc": 0.0, "node": node, "cage": cage, "mat": cage_mat, "light": light, "label": label}
		lanterns.append(lantern)
		_refresh_lantern(lantern)


func _refresh_lantern(lantern: Dictionary) -> void:
	var lit := bool(lantern["lit"])
	var fuel := int(lantern["fuel"])
	var colorblind := str(settings["color_mode"]) == "colorblind"
	var mat = lantern["mat"]
	if lit:
		if colorblind:
			mat.albedo_color = Color(0.82, 0.96, 1.0)
			mat.emission = Color(0.35, 0.85, 1.0)
			lantern["light"].light_color = Color(0.55, 0.9, 1.0)
			lantern["label"].modulate = Color(0.8, 0.98, 1.0)
		else:
			mat.albedo_color = Color(1.0, 0.72, 0.25)
			mat.emission = Color(1.0, 0.48, 0.1)
			lantern["light"].light_color = Color(1.0, 0.66, 0.28)
			lantern["label"].modulate = Color(1.0, 0.86, 0.48)
		mat.emission_energy_multiplier = 2.8
		lantern["light"].light_energy = 1.7
		lantern["light"].omni_range = 11.0
		lantern["label"].text = "%s  SÁNG  %d/100" % [str(lantern["id"]), fuel]
	else:
		mat.albedo_color = Color(0.24, 0.26, 0.3) if colorblind else Color(0.2, 0.32, 0.5)
		mat.emission = Color(0.08, 0.08, 0.1) if colorblind else Color(0.15, 0.3, 0.65)
		mat.emission_energy_multiplier = 0.4
		lantern["light"].light_color = Color(0.5, 0.55, 0.6) if colorblind else Color(0.45, 0.62, 1.0)
		lantern["light"].light_energy = 0.35
		lantern["light"].omni_range = 5.0
		lantern["label"].modulate = Color(0.72, 0.74, 0.78) if colorblind else Color(0.75, 0.85, 1.0)
		lantern["label"].text = "%s  TẮT  %d/100" % [str(lantern["id"]), fuel]


func _build_motes() -> void:
	var spawn: Dictionary = map.get("mote_spawn", {})
	var count := int(spawn.get("count", 0))
	var center: Array = spawn.get("center", [0, 0])
	var radius := float(spawn.get("radius_m", 30.0))
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.78, 0.3)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.55, 0.12)
	mat.emission_energy_multiplier = 2.4
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for i in count:
		var p := Vector3.ZERO
		var found := false
		for attempt in 50:
			var angle := rng.randf_range(0.0, TAU)
			var r := sqrt(rng.randf()) * radius
			p = Vector3(float(center[0]) + cos(angle) * r, 0.0, float(center[1]) + sin(angle) * r)
			var h = _surface_height(p.x, p.z)
			if h != null:
				p.y = float(h)
				found = true
				break
		if not found:
			continue
		var node := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 0.16
		sphere.height = 0.32
		node.mesh = sphere
		node.material_override = mat
		world_root.add_child(node)
		motes.append({"id": "M%d" % (i + 1), "pos": p, "node": node, "phase": rng.randf_range(0.0, TAU)})


func _build_shades() -> void:
	for item in map.get("shade_spawn", []):
		var p := _v3(item["pos"])
		var h = _surface_height(p.x, p.z)
		p.y = float(h) if h != null else 0.0
		var node := Node3D.new()
		node.position = Vector3(p.x, p.y + 0.75, p.z)
		world_root.add_child(node)
		var sphere := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radius = 0.72
		mesh.height = 1.44
		sphere.mesh = mesh
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.055, 0.025, 0.1)
		mat.emission_enabled = true
		mat.emission = Color(0.16, 0.03, 0.25)
		mat.emission_energy_multiplier = 1.2
		sphere.material_override = mat
		node.add_child(sphere)
		var eye_mat := StandardMaterial3D.new()
		eye_mat.albedo_color = Color(1.0, 0.2, 0.15)
		eye_mat.emission_enabled = true
		eye_mat.emission = Color(1.0, 0.1, 0.05)
		eye_mat.emission_energy_multiplier = 2.5
		for side in [-0.24, 0.24]:
			var eye := MeshInstance3D.new()
			var eye_mesh := SphereMesh.new()
			eye_mesh.radius = 0.09
			eye_mesh.height = 0.18
			eye.mesh = eye_mesh
			eye.position = Vector3(float(side), 0.2, -0.62)
			eye.material_override = eye_mat
			node.add_child(eye)
		shades.append({"id": str(item.get("id", "S")), "pos": p, "node": node, "mat": mat,
			"stun": 0.0, "state": "wander", "drain_target": ""})


func _build_wisps() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.3, 0.9, 1.0)
	mat.emission_enabled = true
	mat.emission = Color(0.2, 0.7, 1.0)
	mat.emission_energy_multiplier = 2.6
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for item in map.get("wisp_spawn", []):
		var p := _v3(item["pos"])
		var node := Node3D.new()
		node.position = Vector3(p.x, p.y + 0.8, p.z)
		world_root.add_child(node)
		var sphere := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radius = 0.28
		mesh.height = 0.56
		sphere.mesh = mesh
		sphere.material_override = mat
		node.add_child(sphere)
		var light := OmniLight3D.new()
		light.light_color = Color(0.25, 0.75, 1.0)
		light.light_energy = 0.9
		light.omni_range = 5.0
		light.shadow_enabled = false
		node.add_child(light)
		wisps.append({"id": str(item.get("id", "W")), "pos": p, "node": node})


func _build_charms() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.4, 1.0, 0.62)
	mat.emission_enabled = true
	mat.emission = Color(0.18, 0.9, 0.4)
	mat.emission_energy_multiplier = 2.4
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for item in map.get("charm_spawn", []):
		var p := _v3(item["pos"])
		var node := Node3D.new()
		node.position = Vector3(p.x, p.y + 0.9, p.z)
		world_root.add_child(node)
		var sphere := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radius = 0.3
		mesh.height = 0.6
		sphere.mesh = mesh
		sphere.material_override = mat
		node.add_child(sphere)
		var ring := MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = 0.42
		torus.outer_radius = 0.52
		torus.rings = 24
		torus.ring_segments = 8
		ring.mesh = torus
		ring.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		ring.material_override = mat
		node.add_child(ring)
		charms.append({"id": str(item.get("id", "C")), "pos": p, "node": node, "collected": false})


func _build_bell() -> void:
	var data = map.get("bell_tower")
	if data == null:
		return
	var p := _v3(data["pos"])
	var base_height := float(data.get("base_height_m", 8.0))
	var node := Node3D.new()
	node.position = Vector3(p.x, base_height, p.z)
	world_root.add_child(node)
	var base := MeshInstance3D.new()
	var base_mesh := CylinderMesh.new()
	base_mesh.top_radius = 3.0
	base_mesh.bottom_radius = 3.2
	base_mesh.height = 0.45
	base.mesh = base_mesh
	base.position = Vector3(0.0, 0.22, 0.0)
	var stone := StandardMaterial3D.new()
	stone.albedo_color = Color(0.18, 0.18, 0.24)
	base.material_override = stone
	node.add_child(base)
	for sx in [-1.8, 1.8]:
		for sz in [-1.8, 1.8]:
			var post := MeshInstance3D.new()
			var post_mesh := CylinderMesh.new()
			post_mesh.top_radius = 0.13
			post_mesh.bottom_radius = 0.17
			post_mesh.height = 2.7
			post.mesh = post_mesh
			post.position = Vector3(float(sx), 1.5, float(sz))
			post.material_override = stone
			node.add_child(post)
	var roof := MeshInstance3D.new()
	var roof_mesh := CylinderMesh.new()
	roof_mesh.top_radius = 0.0
	roof_mesh.bottom_radius = 2.8
	roof_mesh.height = 1.1
	roof.mesh = roof_mesh
	roof.position = Vector3(0.0, 3.55, 0.0)
	var roof_mat := StandardMaterial3D.new()
	roof_mat.albedo_color = Color(0.2, 0.12, 0.16)
	roof_mat.roughness = 0.8
	roof.material_override = roof_mat
	node.add_child(roof)
	var bell_mesh := MeshInstance3D.new()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.8
	cone.bottom_radius = 1.5
	cone.height = 2.2
	bell_mesh.mesh = cone
	bell_mesh.position = Vector3(0.0, 1.7, 0.0)
	var gold := StandardMaterial3D.new()
	gold.albedo_color = Color(1.0, 0.72, 0.25)
	gold.metallic = 0.7
	gold.roughness = 0.25
	gold.emission_enabled = true
	gold.emission = Color(0.45, 0.2, 0.02)
	gold.emission_energy_multiplier = 1.2
	bell_mesh.material_override = gold
	node.add_child(bell_mesh)
	var light := OmniLight3D.new()
	light.position = Vector3(0.0, 1.8, 0.0)
	light.light_color = Color(1.0, 0.7, 0.3)
	light.light_energy = 1.1
	light.omni_range = 16.0
	light.shadow_enabled = false
	node.add_child(light)
	var label := Label3D.new()
	label.position = Vector3(0.0, 4.8, 0.0)
	label.font_size = 32
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.outline_size = 7
	label.modulate = Color(1.0, 0.86, 0.45)
	label.text = "THÁP CHUÔNG"
	node.add_child(label)
	bell = {"pos": p, "node": node, "light": light}


func _build_wind_zones() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.2, 0.65, 1.0, 0.055)
	mat.emission_enabled = true
	mat.emission = Color(0.15, 0.5, 1.0)
	mat.emission_energy_multiplier = 0.35
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for zone in wind_zones:
		var mn: Array = zone["min"]
		var mx: Array = zone["max"]
		var node := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(float(mx[0]) - float(mn[0]), 4.5, float(mx[1]) - float(mn[1]))
		node.mesh = box
		node.position = Vector3((float(mn[0]) + float(mx[0])) * 0.5, 2.25, (float(mn[1]) + float(mx[1])) * 0.5)
		node.material_override = mat
		world_root.add_child(node)
		var label := Label3D.new()
		label.position = node.position + Vector3(0.0, 2.8, 0.0)
		label.font_size = 26
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.outline_size = 6
		label.modulate = Color(0.55, 0.9, 1.0)
		label.text = "GIÓ MẠNH"
		world_root.add_child(label)


func _build_jump_pads() -> void:
	for platform in map.get("platforms", []):
		if str(platform.get("type", "")) != "jump_pad":
			continue
		var center: Array = platform["center"]
		var p := Vector3(float(center[0]), float(platform.get("height_m", 0.0)), float(center[1]))
		var node := MeshInstance3D.new()
		var cylinder := CylinderMesh.new()
		cylinder.top_radius = float(platform["radius_m"])
		cylinder.bottom_radius = float(platform["radius_m"])
		cylinder.height = 0.18
		node.mesh = cylinder
		node.position = p + Vector3(0.0, 0.09, 0.0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.2, 0.8, 1.0)
		mat.emission_enabled = true
		mat.emission = Color(0.1, 0.55, 1.0)
		mat.emission_energy_multiplier = 1.8
		node.material_override = mat
		world_root.add_child(node)
		var label := Label3D.new()
		label.position = p + Vector3(0.0, 1.0, 0.0)
		label.font_size = 22
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.outline_size = 5
		label.modulate = Color(0.65, 0.95, 1.0)
		label.text = "NHẢY"
		world_root.add_child(label)
		jump_pads.append({"pos": p, "launch": float(platform.get("launch_velocity_m_s", 14.0))})
