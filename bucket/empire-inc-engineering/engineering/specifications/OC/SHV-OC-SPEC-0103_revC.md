---
document_number: SHV-OC-SPEC-0103
title: "Operations display wall Specification"
revision: "C"
status: APPROVED
classification: INTERNAL
author: "Hale Voren"
approved_by: "Edmund Tarrow"
date: 2022-04-04
language: en
---

**INTERNAL**

# Operations display wall Specification

| | |
|---|---|
| Document number | SHV-OC-SPEC-0103 |
| Revision | C |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Hale Voren |
| Approved by | Edmund Tarrow |
| Date | 2022-04-04 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the operations display wall (OC-ODW) of the Operations Centre on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-OC-04 (WBS 1.17.4), owned by Isolde Sable.

The prime supplier for flight hardware is Corellian Bulk Fasteners. Responsible engineer: Hale Voren.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-OC-DWG-0203 | Operations display wall general arrangement drawing |
| SHV-OC-BOM-0303 | Operations display wall bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-CN-OC | Interface Control Document: Computer Core & Data Network / Operations Centre |

## 4. Description

The operations centre is where station operations, traffic control and facility management are run, with a conference suite and a shared operations display wall.

The operations display wall is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| OC-ODW-R01 | The operations display wall shall provide a display panels of 75 ea. | 75 ea | ±5% | Demonstration |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| OC-ODW-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| OC-ODW-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| OC-ODW-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| OC-ODW-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| OC-ODW-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the OC test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2021-07-08 | Initial release. | Hale Voren |
| B | 2021-11-28 | Updated requirement values after design review. | Hale Voren |
| C | 2022-04-04 | Clarified verification methods. | Hale Voren |

**INTERNAL**
