---
document_number: SHV-LS-SPEC-0103
title: "Artificial gravity generator Specification"
revision: "C"
status: APPROVED
classification: INTERNAL
author: "Wren Ambrose"
approved_by: "Selene Abaroth"
date: 2023-05-31
language: en
---

**INTERNAL**

# Artificial gravity generator Specification

| | |
|---|---|
| Document number | SHV-LS-SPEC-0103 |
| Revision | C |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Wren Ambrose |
| Approved by | Selene Abaroth |
| Date | 2023-05-31 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the artificial gravity generator (LS-GRV) of the Life Support & Atmospherics on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-LS-04 (WBS 1.8.4), owned by Treva Bresk.

The prime supplier for flight hardware is Abregado Droid Works. Responsible engineer: Wren Ambrose.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-LS-DWG-0203 | Artificial gravity generator general arrangement drawing |
| SHV-LS-BOM-0303 | Artificial gravity generator bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-PD-LS | Interface Control Document: Power Distribution / Life Support & Atmospherics |
| SHV-ICD-LS-HA | Interface Control Document: Life Support & Atmospherics / Habitation Blocks |
| SHV-ICD-LS-WM | Interface Control Document: Life Support & Atmospherics / Waste Management & Recycling |
| SHV-ICD-LS-AG | Interface Control Document: Life Support & Atmospherics / Hydroponics & Food Production |

## 4. Description

Life support keeps the atmosphere, water, gravity and temperature within crew limits in every inhabited zone.

The artificial gravity generator is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| LS-GRV-R01 | The artificial gravity generator shall provide a field uniformity of 97.8 %. | 97.8 % | ±5% | Inspection |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| LS-GRV-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| LS-GRV-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| LS-GRV-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| LS-GRV-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| LS-GRV-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the LS test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2022-02-11 | Initial release. | Wren Ambrose |
| B | 2022-12-03 | Clarified verification methods. | Wren Ambrose |
| C | 2023-05-31 | Clarified verification methods. | Wren Ambrose |

**INTERNAL**
