---
document_number: SHV-SA-SPEC-0102
title: "Array tracking drive Specification"
revision: "D"
status: APPROVED
classification: INTERNAL
author: "Nadia Mathers"
approved_by: "Aldric Voss"
date: 2022-07-29
language: en
---

**INTERNAL**

# Array tracking drive Specification

| | |
|---|---|
| Document number | SHV-SA-SPEC-0102 |
| Revision | D |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Nadia Mathers |
| Approved by | Aldric Voss |
| Date | 2022-07-29 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the array tracking drive (SA-SAT) of the Solar Collector Array on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-SA-03 (WBS 1.4.3), owned by Edric Welles.

The prime supplier for flight hardware is Brentaal Logistics Guild. Responsible engineer: Nadia Mathers.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-SA-DWG-0202 | Array tracking drive general arrangement drawing |
| SHV-SA-BOM-0302 | Array tracking drive bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-SA-PD | Interface Control Document: Solar Collector Array / Power Distribution |

## 4. Description

The solar collector array supplements the reactor with photovoltaic panels on tracking drives around the station's sunward hemisphere.

The array tracking drive is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| SA-SAT-R01 | The array tracking drive shall provide a pointing accuracy of 0.42 deg. | 0.42 deg | ±2% | Test |
| SA-SAT-R02 | The array tracking drive shall provide a slew rate of 6.6 deg/min. | 6.6 deg/min | ±5% | Inspection |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| SA-SAT-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| SA-SAT-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| SA-SAT-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| SA-SAT-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| SA-SAT-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the SA test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2020-12-06 | Initial release. | Nadia Mathers |
| B | 2021-04-13 | Updated requirement values after design review. | Nadia Mathers |
| C | 2022-03-30 | Incorporated interface changes. | Nadia Mathers |
| D | 2022-07-29 | Incorporated interface changes. | Nadia Mathers |

**INTERNAL**
