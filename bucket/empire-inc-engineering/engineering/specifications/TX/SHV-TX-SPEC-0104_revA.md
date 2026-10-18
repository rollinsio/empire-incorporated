---
document_number: SHV-TX-SPEC-0104
title: "Heat pipe loop Specification"
revision: "A"
status: APPROVED
classification: INTERNAL
author: "Fallon Darrow"
approved_by: "Aldric Voss"
date: 2024-04-26
language: en
---

**INTERNAL**

# Heat pipe loop Specification

| | |
|---|---|
| Document number | SHV-TX-SPEC-0104 |
| Revision | A |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Fallon Darrow |
| Approved by | Aldric Voss |
| Date | 2024-04-26 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the heat pipe loop (TX-HPL) of the Thermal Control & Heat Rejection on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-TX-05 (WBS 1.2.5), owned by Emrys Bresk.

The prime supplier for flight hardware is Scarif Data Systems. Responsible engineer: Fallon Darrow.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-TX-DWG-0204 | Heat pipe loop general arrangement drawing |
| SHV-TX-BOM-0304 | Heat pipe loop bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-HR-TX | Interface Control Document: Hypermatter Reactor / Thermal Control & Heat Rejection |

## 4. Description

Thermal control carries surplus reactor and habitat heat to the radiator fin arrays on the station surface through heat exchanger stacks, pumped coolant loops and passive heat pipes.

The heat pipe loop is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| TX-HPL-R01 | The heat pipe loop shall provide a loop length of 5.78 km. | 5.78 km | ±2.5% | Analysis |
| TX-HPL-R02 | The heat pipe loop shall provide a operating temperature of 282 K. | 282 K | ±5% | Test |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| TX-HPL-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| TX-HPL-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| TX-HPL-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| TX-HPL-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| TX-HPL-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the TX test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2024-04-26 | Initial release. | Fallon Darrow |

**INTERNAL**
