"""Megger DDA-6000 — dimensional parameters.

Every value is millimetres unless noted. Values marked [DOC] come from Megger's
published datasheet / instruction manual for the DDA-3000 and DDA-6000 Universal
Circuit Breaker Test Sets (Part No. 17177 Rev. 5). Values marked [INF] are
inferred: they are engineering reconstructions consistent with the documented
envelope, mass and feature list, not published figures.

Documented facts this model is built on
---------------------------------------
[DOC] Overall size, DDA-6000:   46 x 55 x 28 in  (H x W x D) = 1168 x 1397 x 711 mm
[DOC] Mass:                     1200 lb (545 kg)
[DOC] Enclosure:                sheet-metal, low centre of gravity, tow ring,
                                lifting eyes, large locking swivel casters
                                (all four swivel, all four lock)
[DOC] Output:                   60 000 A instantaneous maximum
[DOC] Input:                    460 V single phase
[DOC] Duty:                     rated continuous current 30 min on / 30 min off
[DOC] Control:                  DDA-1 digital instrumentation and control system,
                                DSP based, full digital SCR control, digital
                                sampling of output current
[DOC] Metering:                 5-digit displays, 0.281 in (7 mm) numerals;
                                memory ammeter, timer, voltmeter
[DOC] Ammeter ranges:           200 / 2 000 / 20 000 / 200 000 A, default 200 kA
[DOC] Ammeter modes:            MEM (memory) / CONT (continuous)
[DOC] Output control:           multi-position OUTPUT SELECTOR (coarse) plus
                                VERNIER CONTROL (fine); variable pulse time and
                                firing-angle control
[DOC] Panel buttons:            START (energises output), STOP (de-energises)
[DOC] Panel lamps:              OUTPUT ENERGIZED, THERMAL WARNING, THERMAL
                                SHUTDOWN, GROUND INTERLOCK open, OVER RANGE
[DOC] Also:                     input circuit breaker ON/OFF, external (remote)
                                initiate circuit, stab adapter board, CBS-1 and
                                CBS-2 stab sets, 15 ft 4/0 input leads (p/n
                                17163), 10 ft 4/0 interconnect leads (p/n 17164)

Not documented anywhere reachable, therefore inferred
-----------------------------------------------------
Internal component layout, transformer and SCR geometry, panel graphic
arrangement, sheet-metal detailing and colour. These are reconstructed from the
documented envelope and mass and from standard primary-injection test-set
practice. See MODEL_NOTES in this package.
"""

IN = 25.4

# ───────────────────────────── overall envelope [DOC] ─────────────────────────
W = 55.0 * IN          # 1397.0  width, left-right
D = 28.0 * IN          #  711.2  depth, front-back
H = 46.0 * IN          # 1168.4  height, floor to top of cabinet
MASS_KG = 545.0

# ───────────────────────────── running gear [INF] ─────────────────────────────
CASTER_WHEEL_DIA = 152.4        # 6 in heavy swivel caster
CASTER_WHEEL_W = 51.0
CASTER_PLATE = 108.0            # top-plate square
CASTER_SWIVEL_H = 54.0          # swivel housing + plate above wheel top
CASTER_OFFSET = 38.0            # swivel offset, wheel axis behind kingpin
BASE_Z = CASTER_WHEEL_DIA + CASTER_SWIVEL_H     # 206.4 underside of cabinet
CASTER_INSET_X = 140.0
CASTER_INSET_Y = 115.0

# ───────────────────────────── cabinet shell [INF] ────────────────────────────
BODY_H = H - BASE_Z             # 962.0 cabinet body height
SHEET = 1.9                     # sheet-metal thickness (14 ga)
PLINTH_H = 95.0                 # structural base / skid
CORNER_R = 14.0                 # formed corner radius on skins
FRAME_TUBE = 45.0               # internal frame RHS section

# control panel: recessed into the upper front face, tipped back for the operator
PANEL_TILT_DEG = 14.0
PANEL_Z0 = 646.0                # bottom edge of panel aperture, from floor
PANEL_Z1 = 1096.0               # top edge
PANEL_X0 = 118.0                # left edge of panel aperture, from cabinet left
PANEL_X1 = W - 118.0
PANEL_RECESS = 58.0             # how far the panel face sits behind the skin
PANEL_THK = 3.2

# lower front: vent bank on the left, output compartment on the right
VENT_X0 = 95.0
VENT_X1 = 700.0
VENT_Z0 = 300.0
VENT_Z1 = 600.0
LOUVER_H = 20.0
LOUVER_GAP = 34.0

OUTPUT_BAY_X0 = 760.0
OUTPUT_BAY_X1 = W - 95.0
OUTPUT_BAY_Z0 = 262.0
OUTPUT_BAY_Z1 = 600.0

# ───────────────────────────── output terminals [INF] ─────────────────────────
# Two output pads (single-phase secondary) on heavy copper bar, studded for the
# stab adapter board or bolted leads.
BUS_W = 180.0                   # pad width
BUS_T = 20.0                    # copper thickness
BUS_PITCH = 240.0               # centre-to-centre of the two pads
BUS_Z = 430.0                   # pad centreline height
STUD_DIA = 16.0
STUD_LEN = 46.0

# ───────────────────────────── main transformer [INF] ─────────────────────────
# Shell-form laminated core, centre leg wound. Sized so core + copper dominate
# the documented 545 kg.
# Sized so that core steel + copper + enclosure land near the documented 545 kg;
# build.py prints the modelled mass so the reconstruction stays honest.
CORE_W = 700.0                  # overall core width
CORE_H = 430.0                  # overall core height
CORE_STACK = 125.0              # lamination stack depth
CORE_YOKE = 98.0                # top/bottom yoke thickness
CORE_LEG = 88.0                 # outer leg width
CORE_CENTRE_LEG = 180.0         # centre leg width
LAM_PITCH = 11.0                # drawn lamination banding pitch

COIL_PRI_T = 38.0               # primary winding radial build
COIL_SEC_T = 34.0               # secondary (high-current) radial build
COIL_H = 200.0                  # winding height on the centre leg
COIL_CLEAR = 10.0               # clearance core to winding

XFMR_X = 470.0                  # transformer centre, cabinet coordinates
XFMR_Y = 400.0
XFMR_Z = BASE_Z + PLINTH_H + CORE_H / 2

# ───────────────────────────── SCR / phase control [INF] ──────────────────────
HS_W = 150.0                    # heatsink extrusion width
HS_H = 300.0
HS_D = 150.0
HS_FIN_T = 5.0
HS_FINS = 13
SCR_PUCK_DIA = 86.0             # press-pack thyristor
SCR_PUCK_H = 28.0

# ───────────────────────────── misc internals [INF] ───────────────────────────
FAN_DIA = 254.0                 # 10 in axial fan
FAN_DEPTH = 89.0
CT_OD = 185.0                   # measuring CT on the output bus
CT_ID = 112.0
CT_W = 72.0
MCB_W = 190.0                   # input circuit breaker body
MCB_H = 260.0
MCB_D = 150.0
ELEC_W = 430.0                  # control electronics chassis
ELEC_H = 165.0
ELEC_D = 300.0

# ───────────────────────────── finishes ───────────────────────────────────────
# Colour is NOT documented; this is a neutral industrial scheme.
C_CABINET = (178, 182, 186, 255)     # light grey powder coat
C_CABINET_DK = (150, 155, 160, 255)
C_PANEL = (44, 47, 53, 255)          # charcoal control panel
C_PLINTH = (72, 76, 82, 255)
C_COPPER = (184, 108, 58, 255)
C_COPPER_DK = (150, 86, 46, 255)
C_STEEL_LAM = (112, 118, 128, 255)   # silicon-steel laminations
C_ALU = (168, 174, 182, 255)
C_BLACK = (34, 36, 40, 255)
C_RUBBER = (28, 29, 32, 255)
C_ZINC = (146, 152, 160, 255)
C_INSUL = (62, 48, 40, 255)          # winding insulation / varnish
C_WIRE = (150, 92, 50, 255)
C_PCB = (28, 92, 66, 255)
C_LAMP_RED = (210, 62, 52, 255)
C_LAMP_AMB = (228, 150, 40, 255)
C_LAMP_GRN = (64, 190, 110, 255)
C_LAMP_WHT = (228, 232, 238, 255)
C_YELLOW = (226, 178, 36, 255)
C_BRASS = (196, 158, 74, 255)
