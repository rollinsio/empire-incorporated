---
document_number: SHV-TX-SPEC-0103
title: "Coolant pump station Specification"
revision: "C"
status: APPROVED
classification: INTERNAL
author: "Rhett Starke"
approved_by: "Aldric Voss"
date: 2024-12-28
language: en
---

**INTERNAL**

# Coolant pump station Specification

| | |
|---|---|
| Document number | SHV-TX-SPEC-0103 |
| Revision | C |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Rhett Starke |
| Approved by | Aldric Voss |
| Date | 2024-12-28 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the coolant pump station (TX-CPS) of the Thermal Control & Heat Rejection on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-TX-04 (WBS 1.2.4), owned by Tamsin Quarrel.

The prime supplier for flight hardware is Mustafar Refinery Cooperative. Responsible engineer: Rhett Starke.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-TX-DWG-0203 | Coolant pump station general arrangement drawing |
| SHV-TX-BOM-0303 | Coolant pump station bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-HR-TX | Interface Control Document: Hypermatter Reactor / Thermal Control & Heat Rejection |

## 4. Description

Thermal control carries surplus reactor and habitat heat to the radiator fin arrays on the station surface through heat exchanger stacks, pumped coolant loops and passive heat pipes.

The coolant pump station is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| TX-CPS-R01 | The coolant pump station shall provide a pump flow of 104 m³/s. | 104 m³/s | ±2% | Test |
| TX-CPS-R02 | The coolant pump station shall provide a pump count of 12 ea. | 12 ea | ±2.5% | Inspection |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| TX-CPS-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| TX-CPS-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| TX-CPS-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| TX-CPS-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| TX-CPS-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

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
| A | 2024-06-11 | Initial release. | Rhett Starke |
| B | 2024-09-29 | Incorporated interface changes. | Rhett Starke |
| C | 2024-12-28 | Updated requirement values after design review. | Rhett Starke |

**INTERNAL**
