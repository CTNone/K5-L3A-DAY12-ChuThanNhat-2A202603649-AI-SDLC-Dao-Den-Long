extends Node

const RATE := 22050
var streams: Dictionary = {}
var music_player: AudioStreamPlayer
var sfx_players: Array[AudioStreamPlayer] = []
var rng := RandomNumberGenerator.new()


func _ready() -> void:
	rng.seed = 424242
	_ensure_bus("Music", "Master")
	_ensure_bus("SFX", "Master")
	_build_streams()
	music_player = AudioStreamPlayer.new()
	music_player.bus = "Music"
	music_player.stream = streams["music"]
	music_player.volume_db = -20.0
	add_child(music_player)
	music_player.play()


func _ensure_bus(bus_name: String, send: String) -> void:
	if AudioServer.get_bus_index(bus_name) >= 0:
		return
	var index := AudioServer.get_bus_count()
	AudioServer.add_bus(index)
	AudioServer.set_bus_name(index, bus_name)
	AudioServer.set_bus_send(index, send)


func _build_streams() -> void:
	streams["music"] = _music_loop()
	streams["pickup"] = _tone(880.0, 0.12, 0.32, 0.55)
	streams["deposit"] = _chime([660.0, 990.0], 0.16, 0.34)
	streams["lantern"] = _chime([523.25, 659.25, 783.99], 0.22, 0.34)
	streams["pulse"] = _sweep(220.0, 70.0, 0.36, 0.34)
	streams["hit"] = _noise_hit(0.30, 0.42)
	streams["charm"] = _chime([1046.5, 1318.5], 0.16, 0.30)
	streams["wind"] = _noise_hit(0.22, 0.16)
	streams["jump"] = _sweep(300.0, 560.0, 0.16, 0.20)
	streams["dash"] = _noise_hit(0.14, 0.22)
	streams["win"] = _chime([523.25, 659.25, 783.99, 1046.5, 1318.5], 0.18, 0.36)
	streams["lose"] = _chime([220.0, 196.0, 146.83], 0.28, 0.34)
	streams["ui"] = _tone(520.0, 0.055, 0.18, 0.70)


func _music_loop() -> AudioStreamWAV:
	var seconds := 8.0
	var count := int(seconds * RATE)
	var samples := PackedFloat32Array()
	samples.resize(count)
	var chords := [[110.0, 165.0, 220.0], [98.0, 146.83, 196.0], [130.81, 196.0, 261.63], [110.0, 164.81, 220.0]]
	for i in count:
		var t := float(i) / RATE
		var chord: Array = chords[int(t / 2.0) % chords.size()]
		var s := 0.0
		for f in chord:
			s += sin(TAU * float(f) * t) * 0.045
			s += sin(TAU * float(f) * 2.0 * t) * 0.012
		s += sin(TAU * 55.0 * t) * 0.035
		s *= 0.72 + 0.28 * sin(TAU * 0.125 * t)
		var edge: float = min(t, seconds - t)
		if edge < 0.12:
			s *= edge / 0.12
		samples[i] = s
	return _wav(samples, true)


func _tone(freq: float, seconds: float, volume: float, decay: float) -> AudioStreamWAV:
	var count := int(seconds * RATE)
	var samples := PackedFloat32Array()
	samples.resize(count)
	for i in count:
		var t := float(i) / RATE
		var env: float = pow(max(0.0, 1.0 - t / seconds), decay)
		samples[i] = sin(TAU * freq * t) * volume * env
	return _wav(samples)


func _chime(freqs: Array, step: float, volume: float) -> AudioStreamWAV:
	var count := int((step * freqs.size() + 0.12) * RATE)
	var samples := PackedFloat32Array()
	samples.resize(count)
	for n in freqs.size():
		var start := int(n * step * RATE)
		var freq: float = freqs[n]
		for i in int(step * RATE):
			var idx := start + i
			if idx >= count:
				break
			var t := float(i) / RATE
			var env := exp(-t * 7.0)
			samples[idx] += sin(TAU * freq * t) * volume * env
	return _wav(samples)


func _sweep(from_hz: float, to_hz: float, seconds: float, volume: float) -> AudioStreamWAV:
	var count := int(seconds * RATE)
	var samples := PackedFloat32Array()
	samples.resize(count)
	var phase := 0.0
	for i in count:
		var t := float(i) / RATE
		var f: float = lerp(from_hz, to_hz, t / seconds)
		phase += TAU * f / RATE
		var env: float = pow(max(0.0, 1.0 - t / seconds), 1.4)
		samples[i] = sin(phase) * volume * env
	return _wav(samples)


func _noise_hit(seconds: float, volume: float) -> AudioStreamWAV:
	var count := int(seconds * RATE)
	var samples := PackedFloat32Array()
	samples.resize(count)
	for i in count:
		var t := float(i) / RATE
		var env := exp(-t * 11.0)
		samples[i] = (rng.randf_range(-1.0, 1.0) * 0.6 + sin(TAU * 70.0 * t) * 0.4) * volume * env
	return _wav(samples)


func _wav(samples: PackedFloat32Array, looped := false) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		data.encode_s16(i * 2, int(clamp(samples[i], -1.0, 1.0) * 32767.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = RATE
	stream.stereo = false
	stream.data = data
	if looped:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		stream.loop_begin = 0
		stream.loop_end = samples.size()
	return stream


func play(name: String, volume_db := 0.0) -> void:
	if not streams.has(name):
		return
	var player := AudioStreamPlayer.new()
	player.stream = streams[name]
	player.bus = "SFX"
	player.volume_db = volume_db
	add_child(player)
	player.finished.connect(_on_sfx_finished.bind(player))
	sfx_players.append(player)
	if sfx_players.size() > 16:
		var oldest: AudioStreamPlayer = sfx_players.pop_front()
		if is_instance_valid(oldest):
			oldest.queue_free()
	player.play()


func _on_sfx_finished(player: AudioStreamPlayer) -> void:
	sfx_players.erase(player)
	if is_instance_valid(player):
		player.queue_free()


func set_bus_volume(bus_name: String, value: float) -> void:
	var index := AudioServer.get_bus_index(bus_name)
	if index >= 0:
		AudioServer.set_bus_volume_db(index, linear_to_db(clamp(value, 0.0001, 1.0)))


func set_master_volume(value: float) -> void:
	set_bus_volume("Master", value)


func set_music_volume(value: float) -> void:
	set_bus_volume("Music", value)


func set_sfx_volume(value: float) -> void:
	set_bus_volume("SFX", value)
