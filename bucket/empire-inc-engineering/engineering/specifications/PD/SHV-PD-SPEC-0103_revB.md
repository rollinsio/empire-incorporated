---
document_number: SHV-PD-SPEC-0103
title: "Backup generator bank Specification"
revision: "B"
status: APPROVED
classification: INTERNAL
author: "Fallon Darrow"
approved_by: "Aldric Voss"
date: 2023-02-01
language: en
---

**INTERNAL**

# Backup generator bank Specification

| | |
|---|---|
| Document number | SHV-PD-SPEC-0103 |
| Revision | B |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Fallon Darrow |
| Approved by | Aldric Voss |
| Date | 2023-02-01 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the backup generator bank (PD-BKG) of the Power Distribution on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-PD-04 (WBS 1.3.4), owned by Ulric Kirwan.

The prime supplier for flight hardware is Garel Composite Mills. Responsible engineer: Fallon Darrow.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-PD-DWG-0203 | Backup generator bank general arrangement drawing |
| SHV-PD-BOM-0303 | Backup generator bank bill of materials |
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

The backup generator bank is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| PD-BKG-R01 | The backup generator bank shall provide a bank output of 1.35 TW. | 1.35 TW | ±2% | Inspection |
| PD-BKG-R02 | The backup generator bank shall not exceed a start time of 14 s. | 14 s | ±2.5% | Analysis |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| PD-BKG-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| PD-BKG-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| PD-BKG-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| PD-BKG-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| PD-BKG-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

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
| A | 2022-10-01 | Initial release. | Fallon Darrow |
| B | 2023-02-01 | Updated requirement values after design review. | Fallon Darrow |

**INTERNAL**
