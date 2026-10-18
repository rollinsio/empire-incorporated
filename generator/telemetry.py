"""Time-series data: daily construction progress per zone and hourly sensor readings."""

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from generator import canon
from generator.config import AS_OF
from generator.labels import CONFIDENTIAL, INTERNAL
from generator.rand import stream

PROGRESS_START = date(2023, 1, 2)
SENSOR_START = datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)
SENSOR_END = datetime(2026, 9, 30, 23, 0, tzinfo=timezone.utc)

# The planted stall: Zone 17 gains almost nothing in Q2 2026 (quadanium shortage, see PO and ticket data).
STALLED_ZONE = "Z17"
STALL_START, STALL_END = date(2026, 4, 1), date(2026, 6, 30)

# The planted reactor temperature excursion; the heat exchanger downstream of it follows.
PEAK_SENSOR = "HR-CORE-T01"
PEAK_AT = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)
PEAK_VALUE = 4812.6

FOLLOWER_SENSOR = "TX-HXS-T01"
FOLLOWER_PEAK = 702.4

# sensor_id, system, zone, metric, unit, baseline, noise, label
SENSORS = [
    ("HR-CORE-T01", "HR", "Z12", "reactor_core_temperature", "K", 4380, 18, CONFIDENTIAL),
    ("HR-CORE-T02", "HR", "Z13", "reactor_core_temperature", "K", 4376, 18, CONFIDENTIAL),
    ("HR-CFG-F01", "HR", "Z12", "containment_field_strength", "% nominal", 99.2, 0.15, CONFIDENTIAL),
    ("HR-CFG-F02", "HR", "Z13", "containment_field_strength", "% nominal", 99.1, 0.15, CONFIDENTIAL),
    ("HR-OUT-P01", "HR", "Z12", "reactor_output", "% rated", 41, 2.5, CONFIDENTIAL),
    ("TX-HXS-T01", "TX", "Z11", "heat_exchanger_outlet_temperature", "K", 610, 12, INTERNAL),
    ("TX-HXS-T02", "TX", "Z14", "heat_exchanger_outlet_temperature", "K", 604, 12, INTERNAL),
    ("TX-CPS-F01", "TX", "Z12", "coolant_pump_flow", "m³/s", 96, 4, INTERNAL),
    ("PD-SUB-L01", "PD", "Z03", "substation_load", "% rated", 52, 6, INTERNAL),
    ("PD-SUB-L02", "PD", "Z07", "substation_load", "% rated", 48, 6, INTERNAL),
    ("PD-SUB-L03", "PD", "Z15", "substation_load", "% rated", 57, 6, INTERNAL),
    ("PD-SUB-L04", "PD", "Z21", "substation_load", "% rated", 44, 6, INTERNAL),
    ("SA-PCU-P01", "SA", "Z02", "solar_array_output", "GW", 2.9, 0.3, INTERNAL),
    ("SA-PCU-P02", "SA", "Z05", "solar_array_output", "GW", 3.1, 0.3, INTERNAL),
    ("HB-MHB-P01", "HB", "Z06", "hangar_pressure", "kPa", 101.2, 0.6, INTERNAL),
    ("HB-MHB-P02", "HB", "Z18", "hangar_pressure", "kPa", 101.0, 0.6, INTERNAL),
    ("HB-CSC-C01", "HB", "Z06", "docking_cycles", "count/h", 14, 5, INTERNAL),
    ("SY-GCR-L01", "SY", "Z22", "gantry_crane_load", "t", 1250, 180, CONFIDENTIAL),
    ("LS-ATP-O01", "LS", "Z04", "oxygen_fraction", "%", 20.9, 0.05, INTERNAL),
    ("LS-ATP-O02", "LS", "Z09", "oxygen_fraction", "%", 20.9, 0.05, INTERNAL),
    ("LS-ATP-O03", "LS", "Z16", "oxygen_fraction", "%", 20.9, 0.05, INTERNAL),
    ("LS-ATP-C01", "LS", "Z04", "carbon_dioxide", "ppm", 610, 40, INTERNAL),
    ("LS-ATP-C02", "LS", "Z16", "carbon_dioxide", "ppm", 640, 40, INTERNAL),
    ("LS-WRC-R01", "LS", "Z10", "water_reclamation_rate", "%", 97.4, 0.4, INTERNAL),
    ("LS-TRG-T01", "LS", "Z04", "cabin_temperature", "°C", 20.6, 0.4, INTERNAL),
    ("LS-TRG-T02", "LS", "Z16", "cabin_temperature", "°C", 20.4, 0.4, INTERNAL),
    ("LS-GRV-U01", "LS", "Z08", "gravity_uniformity", "%", 98.6, 0.2, INTERNAL),
    ("HA-CRQ-O01", "HA", "Z19", "berth_occupancy", "berths", 212, 8, INTERNAL),
    ("AG-HGT-H01", "AG", "Z20", "grow_tier_humidity", "%", 68, 3, INTERNAL),
    ("CN-CCO-U01", "CN", "Z05", "core_utilization", "%", 38, 7, INTERNAL),
    ("CN-DNB-L01", "CN", "Z05", "backbone_latency", "ms", 3.1, 0.4, INTERNAL),
    ("CM-HNT-Q01", "CM", "Z02", "holonet_queue_depth", "messages", 220, 60, INTERNAL),
    ("WM-TCU-C01", "WM", "Z20", "compactor_cycles", "count/h", 3.2, 1.0, INTERNAL),
    ("TR-TRM-R01", "TR", "Z09", "tram_riders", "persons/h", 840, 120, INTERNAL),
    ("SF-RIB-S01", "SF", "Z12", "rib_strain", "µε", 410, 25, INTERNAL),
    ("SF-RIB-S02", "SF", "Z06", "rib_strain", "µε", 380, 25, INTERNAL),
    ("SF-HPS-V01", "SF", "Z17", "hull_vibration", "mm/s", 1.8, 0.3, INTERNAL),
]


@dataclass
class Telemetry:
    progress: list[dict]
    sensors: list[dict]
    readings: list[dict]


def _progress(rng) -> list[dict]:
    rows = []
    days = (AS_OF - PROGRESS_START).days + 1
    for zone, _ in canon.ZONES:
        midpoint = rng.uniform(0.45, 0.75) * days
        steepness = rng.uniform(5.5, 8.5) / days
        base_crew = rng.randint(800, 2400)
        percent = 0.0
        for offset in range(days):
            day = PROGRESS_START + timedelta(days=offset)
            target = 100 / (1 + math.exp(-steepness * (offset - midpoint)))
            # Track the S-curve, but never faster than a zone can physically build (so the stalled zone recovers gradually).
            gain = min(max(0.0, target - percent) * rng.uniform(0.6, 1.0), 0.35)
            if zone == STALLED_ZONE and STALL_START <= day <= STALL_END:
                gain = rng.uniform(0.0, 0.004)
            percent = min(99.9, percent + gain)
            weekday = day.weekday() < 6
            crew = int(base_crew * (0.6 + 0.4 * target / 100) * (1 if weekday else 0.35) * rng.uniform(0.9, 1.1))
            if zone == STALLED_ZONE and STALL_START <= day <= STALL_END:
                crew = int(crew * 0.15)
            incidents = 1 if rng.random() < 0.012 else 0
            if rng.random() < 0.002:
                incidents += 1
            rows.append({
                "progress_date": day, "zone_code": zone, "percent_complete": round(percent, 3),
                "crew_on_shift": crew, "hours_worked": crew * 10, "safety_incidents": incidents,
            })
    return rows


def _readings(rng) -> tuple[list[dict], list[dict]]:
    sensors = [
        {"sensor_id": sensor_id, "system_code": system, "zone_code": zone, "metric": metric, "unit": unit, "sensitivity": label}
        for sensor_id, system, zone, metric, unit, _, _, label in SENSORS
    ]
    readings = []
    hours = int((SENSOR_END - SENSOR_START).total_seconds() // 3600) + 1
    for sensor_id, _, _, _, _, baseline, noise, _ in SENSORS:
        drift = 0.0
        for hour in range(hours):
            at = SENSOR_START + timedelta(hours=hour)
            drift = 0.97 * drift + rng.gauss(0, noise * 0.3)
            daily = math.sin(2 * math.pi * (at.hour / 24)) * noise * 0.8
            value = baseline + drift + daily + rng.gauss(0, noise * 0.5)
            if sensor_id == PEAK_SENSOR and at == PEAK_AT:
                value = PEAK_VALUE
            elif sensor_id == PEAK_SENSOR and abs((at - PEAK_AT).total_seconds()) <= 3 * 3600:
                value = baseline + (PEAK_VALUE - baseline) * (1 - abs((at - PEAK_AT).total_seconds()) / (4 * 3600))
            elif sensor_id == FOLLOWER_SENSOR and abs((at - PEAK_AT).total_seconds()) <= 2 * 3600:
                value = FOLLOWER_PEAK - abs((at - PEAK_AT).total_seconds()) / 3600 * 30
            readings.append({"sensor_id": sensor_id, "reading_at": at, "value": round(value, 2)})
    # Nothing but the planted peak may reach it.
    ceiling = PEAK_VALUE - 1
    for row in readings:
        if row["sensor_id"] == PEAK_SENSOR and row["reading_at"] != PEAK_AT and row["value"] >= ceiling:
            row["value"] = round(ceiling - 1, 2)
    return sensors, readings


def build() -> Telemetry:
    rng = stream("telemetry")
    progress = _progress(rng)
    sensors, readings = _readings(rng)
    return Telemetry(progress, sensors, readings)
