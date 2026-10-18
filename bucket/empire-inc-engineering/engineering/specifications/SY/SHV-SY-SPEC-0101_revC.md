---
document_number: SHV-SY-SPEC-0101
title: "Slipway Specification"
revision: "C"
status: APPROVED
classification: CONFIDENTIAL
author: "Vela Warrick"
approved_by: "Petra Valcourt"
date: 2023-07-11
language: en
---

**CONFIDENTIAL**

# Slipway Specification

| | |
|---|---|
| Document number | SHV-SY-SPEC-0101 |
| Revision | C |
| Status | APPROVED |
| Classification | CONFIDENTIAL |
| Author | Vela Warrick |
| Approved by | Petra Valcourt |
| Date | 2023-07-11 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the slipway (SY-SLW) of the Shipyard Slipways on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-SY-02 (WBS 1.7.2), owned by Jessa Rhydon.

The prime supplier for flight hardware is Anaxes Turbolift Company. Responsible engineer: Vela Warrick.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-SY-DWG-0201 | Slipway general arrangement drawing |
| SHV-SY-BOM-0301 | Slipway bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-PD-SY | Interface Control Document: Power Distribution / Shipyard Slipways |
| SHV-ICD-HB-SY | Interface Control Document: Docking & Hangar Bays / Shipyard Slipways |
| SHV-ICD-SF-SY | Interface Control Document: Superstructure & Frame / Shipyard Slipways |

## 4. Description

The shipyard builds and refits freighters, liners and survey ships on pressurized slipways and dry docks, served by gantry cranes, a coating shop and outfitting quays.

The slipway is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| SY-SLW-R01 | The slipway shall provide a slipway length of 879 m. | 879 m | ±2.5% | Analysis |
| SY-SLW-R02 | The slipway shall provide a maximum hull mass of 192,342 t. | 192,342 t | ±1% | Analysis |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| SY-SLW-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| SY-SLW-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| SY-SLW-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| SY-SLW-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| SY-SLW-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the SY test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2022-04-21 | Initial release. | Vela Warrick |
| B | 2022-12-14 | Clarified verification methods. | Vela Warrick |
| C | 2023-07-11 | Incorporated interface changes. | Vela Warrick |

**CONFIDENTIAL**
