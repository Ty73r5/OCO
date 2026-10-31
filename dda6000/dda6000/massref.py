"""Which density each part is made of, for the modelled-mass sanity check."""
MATERIAL = {
    "plinth": "steel", "frame": "steel", "tow_ring": "steel", "lift_eyes": "steel",
    "skin_left": "steel", "skin_right": "steel", "skin_back": "steel", "skin_top": "steel",
    "skin_front": "steel", "louver_bank": "steel", "rear_grille": "steel",
    "panel_recess": "steel", "panel_plate": "alu", "panel_subchassis": "steel",
    "core": "lam", "core_clamps": "steel", "coil_primary": "copper",
    "coil_secondary": "copper", "coil_insulation": "plastic",
    "scr_heatsinks": "alu", "scr_pucks": "copper", "scr_clamp": "steel",
    "snubber_pcb": "pcb", "input_breaker": "plastic", "input_terminals": "plastic",
    "control_chassis": "steel", "dda1_board": "pcb", "psu": "steel", "wiring": "copper",
    "ct_output": "steel", "terminal_guard": "plastic", "stab_board": "copper",
    "keypad": "plastic", "lcd": "glass",
}
PREFIX = (
    ("caster_", "steel"), ("tyre_", "rubber"), ("bus_", "copper"), ("pad_", "copper"),
    ("fan_", "plastic"), ("meter_", "glass"), ("sel_", "plastic"), ("knob_", "plastic"),
    ("sw_", "steel"), ("btn_", "plastic"), ("lamp_", "plastic"), ("conn_", "steel"),
)
# Winding fill factors: a wound coil is not solid metal.
# Some members are drawn as simplified solids that stand in for channel, tube or
# wound sections. The fill factor converts that solid back to a believable mass.
FILL = {
    "coil_primary": 0.52,       # round wire in a wound coil
    "coil_secondary": 0.88,     # heavy strap, tightly wound
    "wiring": 0.45,             # stranded cable in a loom
    "frame": 0.18,              # drawn solid, actually RHS tube
    "plinth": 0.25,             # drawn solid, actually formed channel
    "core_clamps": 0.45,
    "scr_pucks": 0.55,          # press-pack is part ceramic
    "psu": 1.0,
    "input_breaker": 0.60,
    "stab_board": 0.30,         # insulating board carrying copper stabs
    "tow_ring": 0.70,
    "lift_eyes": 0.80,
    "caster_fl": 0.50, "caster_fr": 0.50, "caster_rl": 0.50, "caster_rr": 0.50,
}


def material(name):
    if name in MATERIAL:
        return MATERIAL[name]
    for pre, mat in PREFIX:
        if name.startswith(pre):
            return mat
    return "steel"
