---
document_number: SHV-PR-SPEC-0101
title: "Station-keeping thruster Specification"
revision: "B"
status: APPROVED
classification: CONFIDENTIAL
author: "Jory Aster"
approved_by: "Cael Merrow"
date: 2025-05-31
language: en
---

**CONFIDENTIAL**

# Station-keeping thruster Specification

| | |
|---|---|
| Document number | SHV-PR-SPEC-0101 |
| Revision | B |
| Status | APPROVED |
| Classification | CONFIDENTIAL |
| Author | Jory Aster |
| Approved by | Cael Merrow |
| Date | 2025-05-31 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the station-keeping thruster (PR-SKT) of the Propulsion & Station-Keeping on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-PR-02 (WBS 1.5.2), owned by Tilda Falkner.

The prime supplier for flight hardware is Scarif Data Systems. Responsible engineer: Jory Aster.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-PR-DWG-0201 | Station-keeping thruster general arrangement drawing |
| SHV-PR-BOM-0301 | Station-keeping thruster bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-PD-PR | Interface Control Document: Power Distribution / Propulsion & Station-Keeping |

## 4. Description

Propulsion keeps the station in its assigned orbit and attitude. Station-keeping thrusters and sublight ion engines are commanded by the navigation computer, with attitude control gyroscopes for fine pointing.

The station-keeping thruster is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| PR-SKT-R01 | The station-keeping thruster shall provide a thrust of 1,579 kN. | 1,579 kN | ±2.5% | Inspection |
| PR-SKT-R02 | The station-keeping thruster shall provide a thruster count of 84 ea. | 84 ea | ±2% | Inspection |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| PR-SKT-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| PR-SKT-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| PR-SKT-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| PR-SKT-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| PR-SKT-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the PR test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2025-01-17 | Initial release. | Jory Aster |
| B | 2025-05-31 | Updated requirement values after design review. | Jory Aster |

**CONFIDENTIAL**
