---
document_number: SHV-PD-SPEC-0104
title: "Storage battery string Specification"
revision: "A"
status: APPROVED
classification: INTERNAL
author: "Venn Nash"
approved_by: "Aldric Voss"
date: 2024-04-29
language: en
---

**INTERNAL**

# Storage battery string Specification

| | |
|---|---|
| Document number | SHV-PD-SPEC-0104 |
| Revision | A |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Venn Nash |
| Approved by | Aldric Voss |
| Date | 2024-04-29 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the storage battery string (PD-SBS) of the Power Distribution on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-PD-05 (WBS 1.3.5), owned by Nils Errant.

The prime supplier for flight hardware is Naboo Hydroponic Supply. Responsible engineer: Venn Nash.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-PD-DWG-0204 | Storage battery string general arrangement drawing |
| SHV-PD-BOM-0304 | Storage battery string bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-HR-PD | Interface Control Document: Hypermatter Reactor / Power Distribution |
| SHV-ICD-SA-PD | Interface Control Document: Solar Collector Array / Power Distribution |
| SHV-ICD-PD-LS | Interface Control Document: Power Distribution / Life Support & Atmospherics |
| SHV-ICD-PD-HB | Interface Control Document: Power Distribution / Docking & Hangar Bays |
| SHV-ICD-PD-SY | Interface Control Document: Power Distribution / Shipyard Slipways |
| SHV-ICD-PD-PR | Interface Control Document: Power Distribution / Propulsion & Station-Keeping |
| SHV-ICD-PD-AG | Interface Control Document: Power Distribution / Hydroponics & Food Production |
| SHV-ICD-PD-TR | Interface Control Document: Power Distribution / Internal Transit |
| SHV-ICD-PD-RL | Interface Control Document: Power Distribution / Research Laboratories |

## 4. Description

Power distribution carries reactor and solar output to the zone substations over superconducting bus conduits, with backup generator banks and storage battery strings for life-critical loads.

The storage battery string is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| PD-SBS-R01 | The storage battery string shall provide a storage capacity of 101 GWh. | 101 GWh | ±2.5% | Inspection |
| PD-SBS-R02 | The storage battery string shall not exceed a discharge time of 5.0 h. | 5.0 h | ±2.5% | Test |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| PD-SBS-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| PD-SBS-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| PD-SBS-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| PD-SBS-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| PD-SBS-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the PD test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2024-04-29 | Initial release. | Venn Nash |

**INTERNAL**
