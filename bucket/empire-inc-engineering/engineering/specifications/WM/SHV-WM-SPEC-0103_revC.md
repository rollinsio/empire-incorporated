---
document_number: SHV-WM-SPEC-0103
title: "Materials recycling line Specification"
revision: "C"
status: APPROVED
classification: INTERNAL
author: "Ilka Warrick"
approved_by: "Selene Abaroth"
date: 2022-12-12
language: en
---

**INTERNAL**

# Materials recycling line Specification

| | |
|---|---|
| Document number | SHV-WM-SPEC-0103 |
| Revision | C |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Ilka Warrick |
| Approved by | Selene Abaroth |
| Date | 2022-12-12 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the materials recycling line (WM-RCY) of the Waste Management & Recycling on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-WM-04 (WBS 1.10.4), owned by Ines Everhart.

The prime supplier for flight hardware is Anaxes Turbolift Company. Responsible engineer: Ilka Warrick.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-WM-DWG-0203 | Materials recycling line general arrangement drawing |
| SHV-WM-BOM-0303 | Materials recycling line bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-LS-WM | Interface Control Document: Life Support & Atmospherics / Waste Management & Recycling |

## 4. Description

Waste management collects, compacts, treats and recycles station waste through compactor units, treatment plants and a materials recycling line.

The materials recycling line is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| WM-RCY-R01 | The materials recycling line shall provide a recovery rate of 80.9 %. | 80.9 % | ±5% | Demonstration |
| WM-RCY-R02 | The materials recycling line shall provide a line throughput of 883 t/day. | 883 t/day | ±2.5% | Inspection |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| WM-RCY-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| WM-RCY-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| WM-RCY-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| WM-RCY-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| WM-RCY-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the WM test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2022-02-25 | Initial release. | Ilka Warrick |
| B | 2022-07-13 | Incorporated interface changes. | Ilka Warrick |
| C | 2022-12-12 | Editorial corrections. | Ilka Warrick |

**INTERNAL**
