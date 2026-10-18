"""The fixed facts of Empire Incorporated's fictional world.

Everything the ground truth refers to by value (leadership changes, approved
revisions, the schedule baseline) is written down here once, and every
document and table that mentions it reads it from here. All of it is invented
set dressing for a civilian engineering company: none of it describes real
engineering, real people or real organizations.
"""

from datetime import date

from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED

COMPANY = "Empire Incorporated"
COMPANY_SHORT = "Empire Inc."
HQ = "Coruscant Headquarters"

STATION = "Starhaven"
STATION_LONG = "Starhaven Orbital Habitat & Shipyard"

# --------------------------------------------------------------------------
# Departments: (id, code, name, headcount of active employees)
# --------------------------------------------------------------------------
DEPARTMENTS = [
    ("D01", "OCH", "Office of the Chairman", 12),
    ("D02", "PMO", "Program Management Office", 45),
    ("D03", "SCI", "Science & Research", 70),
    ("D04", "AGR", "Agriculture & Food Systems", 40),
    ("D05", "STR", "Structural Engineering", 110),
    ("D06", "RPS", "Reactor & Power Systems", 85),
    ("D07", "PRO", "Propulsion & Station-Keeping", 60),
    ("D08", "SYD", "Shipyard Operations", 90),
    ("D09", "HFO", "Docking & Flight Operations", 55),
    ("D10", "LSH", "Life Support & Habitation", 50),
    ("D11", "CCS", "Computing & Communications", 65),
    ("D12", "QAT", "Quality Assurance & Test", 60),
    ("D13", "CON", "Construction Operations", 105),
    ("D14", "SCM", "Procurement & Supply Chain", 45),
    ("D15", "FIN", "Finance", 35),
    ("D16", "HRA", "Personnel Administration", 25),
    ("D17", "LEG", "Legal & Contracts", 18),
    ("D18", "FAC", "Facilities & Workplace Safety", 30),
]
DEPT_ID = {code: dept_id for dept_id, code, _, _ in DEPARTMENTS}
DEPT_NAME = {code: name for _, code, name, _ in DEPARTMENTS}
ENGINEERING_DEPTS = ("SCI", "AGR", "STR", "RPS", "PRO", "SYD", "HFO", "LSH", "CCS", "QAT", "CON")

# Construction Operations runs the Eriadu Fabrication Yard, whose staff write in German.
GERMAN_SITE = "Eriadu Fabrication Yard"
GERMAN_SITE_DE = "Fertigungswerft Eriadu"

# --------------------------------------------------------------------------
# Station subsystems and their components.
# Component params: (name, unit, low, high, decimals)
# --------------------------------------------------------------------------
SYSTEMS = {
    "HR": {
        "name": "Hypermatter Reactor",
        "dept": "RPS",
        "label": CONFIDENTIAL,
        "summary": "The hypermatter reactor is the station's main power plant. It supplies every zone substation through the power distribution system and is backed by the solar collector array.",
        "components": [
            ("RCV", "Reactor core vessel", [("Core diameter", "km", 1.6, 2.2, 2), ("Wall thickness", "m", 18, 30, 1), ("Design core temperature", "K", 4100, 4600, 0)]),
            ("CFG", "Containment field generator", [("Field strength", "% nominal", 96, 99.9, 2), ("Generator count", "ea", 12, 24, 0)]),
            ("FIA", "Fuel injector assembly", [("Injection rate", "kg/s", 2, 9, 2), ("Injector count", "ea", 64, 128, 0)]),
            ("CMF", "Coolant manifold", [("Flow capacity", "m³/s", 900, 2400, 0), ("Pressure rating", "MPa", 40, 90, 0)]),
            ("RMS", "Reactor monitoring station", [("Sensor channels", "ea", 2000, 6000, 0), ("Scan interval", "ms", 5, 50, 0)]),
        ],
    },
    "TX": {
        "name": "Thermal Control & Heat Rejection",
        "dept": "RPS",
        "label": INTERNAL,
        "summary": "Thermal control carries surplus reactor and habitat heat to the radiator fin arrays on the station surface through heat exchanger stacks, pumped coolant loops and passive heat pipes.",
        "components": [
            ("HXS", "Heat exchanger stack", [("Rejection capacity", "PW", 0.4, 1.2, 2), ("Stack count", "ea", 16, 32, 0)]),
            ("RFA", "Radiator fin array", [("Fin area", "km²", 3, 9, 1), ("Emissivity", "", 0.82, 0.95, 2)]),
            ("CPS", "Coolant pump station", [("Pump flow", "m³/s", 40, 160, 0), ("Pump count", "ea", 6, 18, 0)]),
            ("HPL", "Heat pipe loop", [("Loop length", "km", 2, 8, 2), ("Operating temperature", "K", 280, 340, 0)]),
        ],
    },
    "PD": {
        "name": "Power Distribution",
        "dept": "RPS",
        "label": INTERNAL,
        "summary": "Power distribution carries reactor and solar output to the zone substations over superconducting bus conduits, with backup generator banks and storage battery strings for life-critical loads.",
        "components": [
            ("MBC", "Main bus conduit", [("Conduit rating", "% reactor", 8, 15, 1), ("Conduit length", "km", 40, 90, 0)]),
            ("SUB", "Zone substation", [("Substation rating", "TW", 2, 8, 1), ("Breaker count", "ea", 200, 600, 0)]),
            ("BKG", "Backup generator bank", [("Bank output", "TW", 0.5, 2, 2), ("Start time", "s", 4, 20, 0)]),
            ("SBS", "Storage battery string", [("Storage capacity", "GWh", 40, 160, 0), ("Discharge time", "h", 2, 8, 1)]),
        ],
    },
    "SA": {
        "name": "Solar Collector Array",
        "dept": "RPS",
        "label": INTERNAL,
        "summary": "The solar collector array supplements the reactor with photovoltaic panels on tracking drives around the station's sunward hemisphere.",
        "components": [
            ("SCP", "Solar collector panel", [("Panel area", "m²", 400, 1200, 0), ("Conversion efficiency", "%", 31, 44, 1)]),
            ("SAT", "Array tracking drive", [("Pointing accuracy", "deg", 0.05, 0.5, 2), ("Slew rate", "deg/min", 2, 9, 1)]),
            ("PCU", "Power conditioning unit", [("Rated power", "GW", 1.2, 4.8, 1), ("Conversion loss", "%", 1.5, 4, 1)]),
        ],
    },
    "PR": {
        "name": "Propulsion & Station-Keeping",
        "dept": "PRO",
        "label": CONFIDENTIAL,
        "summary": "Propulsion keeps the station in its assigned orbit and attitude. Station-keeping thrusters and sublight ion engines are commanded by the navigation computer, with attitude control gyroscopes for fine pointing.",
        "components": [
            ("SKT", "Station-keeping thruster", [("Thrust", "kN", 400, 1600, 0), ("Thruster count", "ea", 48, 120, 0)]),
            ("SIE", "Sublight ion engine", [("Engine count", "ea", 18, 36, 0), ("Thrust per engine", "MN", 900, 2400, 0)]),
            ("NAV", "Navigation computer", [("Orbit solution time", "s", 40, 180, 0), ("Ephemeris entries", "M", 120, 400, 0)]),
            ("ACG", "Attitude control gyroscope", [("Angular momentum", "GN·m·s", 2, 9, 1), ("Gyroscope count", "ea", 8, 16, 0)]),
        ],
    },
    "HB": {
        "name": "Docking & Hangar Bays",
        "dept": "HFO",
        "label": INTERNAL,
        "summary": "The docking and hangar bays receive, service and launch passenger shuttles, cargo haulers and visiting ships behind magnetic atmosphere containment fields.",
        "components": [
            ("MHB", "Main hangar bay", [("Bay count", "ea", 300, 400, 0), ("Atmosphere field rating", "%", 99, 99.9, 1)]),
            ("DBY", "Docking bay", [("Clear span", "m", 90, 240, 0), ("Mooring load rating", "t", 400, 2000, 0)]),
            ("CSC", "Cargo shuttle cradle", [("Cradle capacity", "craft", 4, 16, 0), ("Turnaround time", "min", 25, 90, 0)]),
            ("FCT", "Flight control tower", [("Controller stations", "ea", 12, 30, 0)]),
        ],
    },
    "SY": {
        "name": "Shipyard Slipways",
        "dept": "SYD",
        "label": CONFIDENTIAL,
        "summary": "The shipyard builds and refits freighters, liners and survey ships on pressurized slipways and dry docks, served by gantry cranes, a coating shop and outfitting quays.",
        "components": [
            ("SLW", "Slipway", [("Slipway length", "m", 600, 1800, 0), ("Maximum hull mass", "t", 40000, 220000, 0)]),
            ("GCR", "Gantry crane", [("Lift capacity", "t", 800, 4000, 0), ("Crane span", "m", 120, 420, 0)]),
            ("DDK", "Dry dock", [("Dock length", "m", 500, 1500, 0), ("Pressurization time", "h", 6, 30, 1)]),
            ("PSH", "Coating shop", [("Booth count", "ea", 4, 12, 0), ("Cure time", "h", 8, 48, 0)]),
            ("OFQ", "Outfitting quay", [("Berths", "ea", 4, 14, 0), ("Shore power", "MW", 40, 220, 0)]),
        ],
    },
    "LS": {
        "name": "Life Support & Atmospherics",
        "dept": "LSH",
        "label": INTERNAL,
        "summary": "Life support keeps the atmosphere, water, gravity and temperature within crew limits in every inhabited zone.",
        "components": [
            ("ATP", "Atmosphere processor", [("Processing rate", "m³/s", 4000, 12000, 0), ("O2 setpoint", "%", 20.6, 21.2, 1)]),
            ("WRC", "Water reclamation plant", [("Reclamation rate", "%", 94, 99.2, 1), ("Throughput", "m³/h", 6000, 20000, 0)]),
            ("GRV", "Artificial gravity generator", [("Field uniformity", "%", 97, 99.5, 1)]),
            ("TRG", "Thermal regulation loop", [("Setpoint", "°C", 19, 22, 1)]),
        ],
    },
    "HA": {
        "name": "Habitation Blocks",
        "dept": "LSH",
        "label": INTERNAL,
        "summary": "The habitation blocks house the resident crew and their families: quarters, mess halls, the medical centre, schools and recreation decks.",
        "components": [
            ("CRQ", "Crew quarters module", [("Berths", "ea", 1600, 2600, 0)]),
            ("MSH", "Mess hall", [("Seating", "ea", 600, 2000, 0)]),
            ("MED", "Medical centre", [("Beds", "ea", 120, 400, 0), ("Treatment rooms", "ea", 20, 60, 0)]),
            ("SCH", "School and childcare wing", [("Classrooms", "ea", 24, 80, 0)]),
            ("REC", "Recreation deck", [("Deck area", "m²", 8000, 30000, 0)]),
        ],
    },
    "WM": {
        "name": "Waste Management & Recycling",
        "dept": "LSH",
        "label": INTERNAL,
        "summary": "Waste management collects, compacts, treats and recycles station waste through compactor units, treatment plants and a materials recycling line.",
        "components": [
            ("TCU", "Compactor unit", [("Compaction force", "MN", 8, 20, 1), ("Cycle time", "min", 4, 12, 0)]),
            ("WTP", "Waste treatment plant", [("Throughput", "t/day", 1200, 4000, 0)]),
            ("RCY", "Materials recycling line", [("Recovery rate", "%", 72, 94, 1), ("Line throughput", "t/day", 200, 900, 0)]),
        ],
    },
    "AG": {
        "name": "Hydroponics & Food Production",
        "dept": "AGR",
        "label": INTERNAL,
        "summary": "Hydroponics and food production grow fresh produce for the resident crew on stacked grow tiers under controlled lighting, and prepare meals in the central kitchens.",
        "components": [
            ("HGT", "Hydroponic grow tier", [("Growing area", "m²", 2000, 9000, 0), ("Annual yield", "kg/m²", 40, 110, 0)]),
            ("NSD", "Nutrient solution dosing unit", [("Dosing accuracy", "%", 0.5, 3, 1), ("Dosing lines", "ea", 12, 48, 0)]),
            ("LGT", "Grow lighting array", [("Photon flux", "µmol/m²/s", 400, 1100, 0), ("Fixture count", "ea", 2000, 9000, 0)]),
            ("FPK", "Food processing kitchen", [("Meals per day", "ea", 20000, 90000, 0)]),
        ],
    },
    "CN": {
        "name": "Computer Core & Data Network",
        "dept": "CCS",
        "label": INTERNAL,
        "summary": "The computer core and data network connect every station system. Maintenance terminals and data ports give technicians and service droids access to the network.",
        "components": [
            ("CCO", "Central computer core", [("Processing nodes", "ea", 4000, 12000, 0), ("Storage", "PB", 800, 2400, 0)]),
            ("DNB", "Data network backbone", [("Backbone links", "ea", 96, 240, 0), ("Latency", "ms", 1, 9, 1)]),
            ("MDP", "Maintenance data port", [("Port count", "ea", 9000, 16000, 0)]),
            ("MTT", "Maintenance terminal", [("Terminal count", "ea", 3000, 7000, 0)]),
        ],
    },
    "CM": {
        "name": "Communications Relay",
        "dept": "CCS",
        "label": INTERNAL,
        "summary": "Communications covers HoloNet transceivers, comm array dishes and the switches that route passenger, cargo and station traffic.",
        "components": [
            ("HNT", "HoloNet transceiver", [("Channels", "ea", 400, 1200, 0)]),
            ("CMA", "Comm array dish", [("Dish diameter", "m", 60, 180, 0), ("Array count", "ea", 6, 14, 0)]),
            ("TRS", "Traffic routing switch", [("Throughput", "Tbit/s", 2, 12, 1)]),
        ],
    },
    "SF": {
        "name": "Superstructure & Frame",
        "dept": "STR",
        "label": INTERNAL,
        "summary": "The superstructure is the station's load-bearing frame: structural ribs, hull plating sections, the equatorial service ring and the antenna masts.",
        "components": [
            ("HPS", "Hull plating section", [("Plate thickness", "m", 3, 8, 1), ("Section count", "ea", 12000, 30000, 0)]),
            ("RIB", "Structural rib", [("Rib count", "ea", 360, 720, 0), ("Rib depth", "m", 60, 140, 0)]),
            ("ESR", "Equatorial service ring", [("Ring width", "m", 500, 900, 0), ("Ring depth", "m", 200, 500, 0)]),
            ("ANM", "Antenna mast", [("Mast height", "m", 300, 900, 0)]),
        ],
    },
    "TR": {
        "name": "Internal Transit",
        "dept": "STR",
        "label": INTERNAL,
        "summary": "Internal transit moves people and goods around the station: turbolift cars in vertical shafts and a tram that runs around every latitude band.",
        "components": [
            ("TLC", "Turbolift car", [("Car capacity", "persons", 12, 40, 0), ("Car speed", "m/s", 8, 20, 1)]),
            ("TLS", "Turbolift shaft", [("Shaft length", "km", 2, 9, 2), ("Shaft count", "ea", 120, 260, 0)]),
            ("TRM", "Tram car", [("Seats", "ea", 60, 140, 0)]),
            ("TRK", "Tram track segment", [("Segment length", "m", 40, 120, 0), ("Segment count", "ea", 4000, 9000, 0)]),
        ],
    },
    "RL": {
        "name": "Research Laboratories",
        "dept": "SCI",
        "label": INTERNAL,
        "summary": "The research laboratories host materials science, biology and astronomy groups: wet and dry labs, cleanroom suites, a zero-gravity laboratory and the station observatory.",
        "components": [
            ("MLB", "Materials laboratory", [("Bench count", "ea", 40, 120, 0)]),
            ("CLS", "Cleanroom suite", [("Cleanroom class", "class", 4, 7, 0), ("Floor area", "m²", 600, 2400, 0)]),
            ("ZGL", "Zero-gravity laboratory", [("Lab volume", "m³", 2000, 9000, 0)]),
            ("OBS", "Observatory telescope", [("Primary mirror diameter", "m", 6, 14, 1), ("Pointing accuracy", "arcsec", 0.05, 0.5, 2)]),
        ],
    },
    "OC": {
        "name": "Operations Centre",
        "dept": "PMO",
        "label": INTERNAL,
        "summary": "The operations centre is where station operations, traffic control and facility management are run, with a conference suite and a shared operations display wall.",
        "components": [
            ("OPC", "Operations control room", [("Operator stations", "ea", 30, 60, 0)]),
            ("CRM", "Conference suite", [("Seats", "ea", 12, 24, 0)]),
            ("ODW", "Operations display wall", [("Display panels", "ea", 40, 120, 0)]),
        ],
    },
}

# 24 construction zones of the station sphere.
ZONES = [(f"Z{n:02d}", f"Zone {n:02d} ({'North' if n <= 12 else 'South'}ern Hemisphere, band {((n - 1) % 12) + 1})") for n in range(1, 25)]

LOCATIONS = [
    ("LOC-SCA", "Scarif Archive Depot", "DEPOT", "Scarif"),
    ("LOC-ERI", "Eriadu Fabrication Yard", "FACILITY", "Eriadu"),
    ("LOC-KUA", "Kuat Orbital Depot", "DEPOT", "Kuat"),
    ("LOC-FON", "Fondor Staging Ring", "DEPOT", "Fondor"),
    ("LOC-COR", "Coruscant Headquarters Stores", "DEPOT", "Coruscant"),
    ("LOC-EAD", "Eadu Research Campus", "FACILITY", "Eadu"),
    ("LOC-ST4", "Starhaven Receiving Bay R-4", "STATION", "Starhaven"),
]

# --------------------------------------------------------------------------
# Programs
# --------------------------------------------------------------------------
PROGRAMS = [
    # id, code, name, status, start, target, budget (millions of credits)
    ("PRG-SHV", "SHV", STATION_LONG, "ACTIVE", date(2020, 1, 6), date(2027, 6, 30), 1_240_000),
    ("PRG-CSL", "CSL", "Cargo Shuttle Production Line Expansion", "ACTIVE", date(2023, 3, 1), date(2026, 12, 15), 38_500),
    ("PRG-SCA", "SCA", "Scarif Records Archive Modernization", "ACTIVE", date(2024, 2, 12), date(2026, 11, 30), 9_200),
    ("PRG-EAD", "EAD", "Eadu Agricultural Research Campus", "ACTIVE", date(2022, 8, 1), date(2026, 10, 31), 21_700),
    ("PRG-HQC", "HQC", "Coruscant Office Consolidation", "ACTIVE", date(2025, 1, 6), date(2027, 3, 31), 1_150),
]
MAIN_PROGRAM = "PRG-SHV"

# --------------------------------------------------------------------------
# Named people. Everyone else is generated. Key: short handle used in code.
# --------------------------------------------------------------------------
KEY_PEOPLE = {
    # handle: first, last, dept, title, grade, access level, hire, species, homeworld, departure
    "ashworth": ("Helena", "Ashworth", "OCH", "Chairman & Chief Executive", 15, RESTRICTED, date(2004, 3, 1), "Human", "Coruscant", None),
    "quillon": ("Marcus", "Quillon", "OCH", "Chief Operating Officer", 14, RESTRICTED, date(2008, 6, 1), "Human", "Chandrila", None),
    "tarrow": ("Edmund", "Tarrow", "PMO", "Program Executive, Starhaven", 14, RESTRICTED, date(2006, 9, 4), "Human", "Eriadu", None),
    "merriweather": ("Lucan", "Merriweather", "SCI", "Director, Science & Research", 13, RESTRICTED, date(2010, 2, 15), "Human", "Corulag", None),
    "ferrante": ("Rosalind", "Ferrante", "AGR", "Director, Agriculture & Food Systems", 13, RESTRICTED, date(2014, 5, 12), "Human", "Naboo", date(2026, 6, 14)),
    "stroud": ("Garrick", "Stroud", "PMO", "Head of Station Operations", 13, RESTRICTED, date(2011, 7, 1), "Human", "Brentaal", None),
    "valcourt": ("Petra", "Valcourt", "SYD", "Director, Shipyard Operations", 13, RESTRICTED, date(2009, 4, 20), "Human", "Fondor", None),
    "sallow": ("Imogen", "Sallow", "PMO", "Chief of Staff to the Program Executive", 11, CONFIDENTIAL, date(2013, 10, 7), "Human", "Corulag", None),
    "quayle": ("Ferris", "Quayle", "FAC", "Director, Facilities & Workplace Safety", 13, RESTRICTED, date(2007, 1, 8), "Human", "Alsakan", None),
    "kalvane": ("Idris", "Kalvane", "PMO", "Chief Engineer, Station Integration", 12, RESTRICTED, date(2012, 8, 13), "Human", "Corulag", None),
    "voss": ("Aldric", "Voss", "PMO", "Senior Advisor, Program Management Office", 12, RESTRICTED, date(2011, 2, 7), "Human", "Carida", None),
    "kestrel": ("Mira", "Kestrel", "RPS", "Director, Reactor & Power Systems", 13, RESTRICTED, date(2015, 6, 22), "Human", "Chandrila", None),
    "doyle": ("Hesker", "Doyle", "STR", "Director, Structural Engineering", 13, RESTRICTED, date(2005, 1, 10), "Human", "Kuat", date(2025, 11, 14)),
    "tolle": ("Brenna", "Tolle", "STR", "Director, Structural Engineering", 13, RESTRICTED, date(2016, 4, 4), "Human", "Brentaal", None),
    "corvesh": ("Lenn", "Corvesh", "AGR", "Interim Director, Agriculture & Food Systems", 12, RESTRICTED, date(2017, 9, 18), "Human", "Raxus", None),
    "merrow": ("Cael", "Merrow", "PRO", "Director, Propulsion & Station-Keeping", 13, RESTRICTED, date(2012, 3, 5), "Human", "Corellia", None),
    "hask": ("Dorian", "Hask", "HFO", "Director, Docking & Flight Operations", 13, RESTRICTED, date(2013, 5, 27), "Human", "Lothal", None),
    "abaroth": ("Selene", "Abaroth", "LSH", "Director, Life Support & Habitation", 13, RESTRICTED, date(2014, 1, 13), "Human", "Alsakan", None),
    "orrun": ("Tavi", "Orrun", "CCS", "Director, Computing & Communications", 13, RESTRICTED, date(2013, 11, 4), "Human", "Coruscant", None),
    "harrowgate": ("Wendell", "Harrowgate", "QAT", "Director, Quality Assurance & Test", 13, RESTRICTED, date(2010, 8, 30), "Human", "Lothal", None),
    "brandt": ("Ulrike", "Brandt", "CON", "Direktorin Bauausführung (Director, Construction Operations)", 13, RESTRICTED, date(2012, 6, 18), "Human", "Eriadu", None),
    "solberg": ("Rennick", "Solberg", "SCM", "Director, Procurement & Supply Chain", 13, RESTRICTED, date(2014, 2, 3), "Human", "Kuat", None),
    "varga": ("Odessa", "Varga", "FIN", "Chief Financial Officer", 13, RESTRICTED, date(2009, 9, 14), "Human", "Coruscant", None),
    "amaranth": ("Pell", "Amaranth", "HRA", "Director, Personnel Administration", 13, RESTRICTED, date(2015, 3, 30), "Human", "Chandrila", None),
    "ashgrove": ("Corvin", "Ashgrove", "LEG", "General Counsel", 13, RESTRICTED, date(2011, 10, 24), "Human", "Alderaan", None),
}

# Departure reasons for the key people who have left.
DEPARTURE_REASONS = {
    "ferrante": "Retired",
    "doyle": "Retired",
}

# Department heads over time. (dept, handle, start, end) — end None means current.
DEPARTMENT_HEADS = [
    ("OCH", "ashworth", date(2004, 3, 1), None),
    ("PMO", "tarrow", date(2019, 6, 3), None),
    ("SCI", "merriweather", date(2016, 1, 11), None),
    ("AGR", "ferrante", date(2019, 10, 1), date(2026, 6, 14)),
    ("AGR", "corvesh", date(2026, 6, 15), None),
    ("STR", "doyle", date(2015, 7, 1), date(2025, 11, 14)),
    ("STR", "tolle", date(2025, 11, 15), None),
    ("RPS", "voss", date(2018, 4, 2), date(2026, 1, 31)),
    ("RPS", "kestrel", date(2026, 2, 1), None),
    ("PRO", "merrow", date(2019, 2, 4), None),
    ("SYD", "valcourt", date(2017, 5, 15), None),
    ("HFO", "hask", date(2020, 9, 7), None),
    ("LSH", "abaroth", date(2020, 3, 2), None),
    ("CCS", "orrun", date(2019, 11, 18), None),
    ("QAT", "harrowgate", date(2018, 1, 8), None),
    ("CON", "brandt", date(2020, 1, 13), None),
    ("SCM", "solberg", date(2021, 4, 5), None),
    ("FIN", "varga", date(2017, 10, 2), None),
    ("HRA", "amaranth", date(2021, 8, 2), None),
    ("LEG", "ashgrove", date(2016, 6, 6), None),
    ("FAC", "quayle", date(2015, 2, 2), None),
]

# Program leadership over time (program, handle, role, start, end).
PROGRAM_ROLES = [
    ("PRG-SHV", "tarrow", "EXECUTIVE_SPONSOR", date(2020, 1, 6), None),
    ("PRG-SHV", "merriweather", "PROGRAM_DIRECTOR", date(2020, 1, 6), date(2026, 7, 3)),
    ("PRG-SHV", "tarrow", "PROGRAM_DIRECTOR", date(2026, 7, 4), None),
    ("PRG-EAD", "merriweather", "EXECUTIVE_SPONSOR", date(2022, 8, 1), None),
    ("PRG-EAD", "ferrante", "PROGRAM_DIRECTOR", date(2022, 8, 1), date(2026, 6, 14)),
    ("PRG-EAD", "corvesh", "PROGRAM_DIRECTOR", date(2026, 6, 15), None),
    ("PRG-SCA", "varga", "EXECUTIVE_SPONSOR", date(2024, 2, 12), None),
    ("PRG-SCA", "orrun", "PROGRAM_DIRECTOR", date(2024, 2, 12), None),
    ("PRG-CSL", "stroud", "EXECUTIVE_SPONSOR", date(2023, 3, 1), None),
    ("PRG-CSL", "hask", "PROGRAM_DIRECTOR", date(2023, 3, 1), None),
    ("PRG-HQC", "quillon", "EXECUTIVE_SPONSOR", date(2025, 1, 6), None),
    ("PRG-HQC", "amaranth", "PROGRAM_DIRECTOR", date(2025, 1, 6), None),
]

# --------------------------------------------------------------------------
# Documents with several revisions, of which exactly one is approved.
# --------------------------------------------------------------------------
SCHEDULE_BASELINE = {
    "doc_number": "SHV-PMO-PLN-0001",
    "approved_revision": "3",
    "revisions": {
        "2": (date(2027, 12, 31), "SUPERSEDED"),
        "3": (date(2027, 6, 30), "APPROVED"),
        "4": (date(2027, 3, 31), "DRAFT"),
    },
}

# doc_number -> (system, component, parameter, unit, {revision: (value, status)})
CONFLICTING_SPECS = {
    "SHV-HA-SPEC-0003": ("HA", "CRQ", "Berths", "ea", {"A": (1800, "SUPERSEDED"), "B": (2050, "APPROVED"), "C": (2400, "IN_REVIEW")}),
    "SHV-HB-SPEC-0011": ("HB", "MHB", "Bay count", "ea", {"A": (312, "SUPERSEDED"), "B": (357, "APPROVED"), "C": (384, "REJECTED")}),
    "SHV-HR-SPEC-0002": ("HR", "RCV", "Design core temperature", "K", {"C": (4250, "SUPERSEDED"), "D": (4400, "APPROVED"), "E": (4600, "DRAFT")}),
    "SHV-LS-SPEC-0005": ("LS", "WRC", "Reclamation rate", "%", {"A": (96.5, "SUPERSEDED"), "B": (98.2, "APPROVED")}),
    "SHV-TX-SPEC-0007": ("TX", "RFA", "Fin area", "km²", {"A": (4.2, "SUPERSEDED"), "B": (5.6, "SUPERSEDED"), "C": (6.3, "APPROVED"), "D": (5.1, "DRAFT")}),
}

# --------------------------------------------------------------------------
# Test logins, one per label: (username, access level, how the employee is picked).
# None = no employee record; (dept, level) = first matching ordinary employee.
# --------------------------------------------------------------------------
LOGINS = [
    ("visitor.public", "PUBLIC", None),
    ("staff.internal", INTERNAL, ("HFO", INTERNAL)),
    ("analyst.confidential", CONFIDENTIAL, ("FIN", CONFIDENTIAL)),
    ("hr.restricted", RESTRICTED, ("HRA", RESTRICTED)),
]
