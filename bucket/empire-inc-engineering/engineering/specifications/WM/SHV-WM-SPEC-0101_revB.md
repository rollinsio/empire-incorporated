---
document_number: SHV-WM-SPEC-0101
title: "Compactor unit Specification"
revision: "B"
status: APPROVED
classification: INTERNAL
author: "Tyce Easton"
approved_by: "Selene Abaroth"
date: 2022-09-13
language: en
---

**INTERNAL**

# Compactor unit Specification

| | |
|---|---|
| Document number | SHV-WM-SPEC-0101 |
| Revision | B |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Tyce Easton |
| Approved by | Selene Abaroth |
| Date | 2022-09-13 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the compactor unit (WM-TCU) of the Waste Management & Recycling on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-WM-02 (WBS 1.10.2), owned by Gessa Fiore.

The prime supplier for flight hardware is Anaxes Turbolift Company. Responsible engineer: Tyce Easton.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-WM-DWG-0201 | Compactor unit general arrangement drawing |
| SHV-WM-BOM-0301 | Compactor unit bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-LS-WM | Interface Control Document: Life Support & Atmospherics / Waste Management & Recycling |

## 4. Description

Waste management collects, compacts, treats and recycles station waste through compactor units, treatment plants and a materials recycling line.

The compactor unit is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| WM-TCU-R01 | The compactor unit shall provide a compaction force of 11.5 MN. | 11.5 MN | ±2.5% | Test |
| WM-TCU-R02 | The compactor unit shall not exceed a cycle time of 7 min. | 7 min | ±2% | Demonstration |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| WM-TCU-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| WM-TCU-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| WM-TCU-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| WM-TCU-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| WM-TCU-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

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
| A | 2022-05-22 | Initial release. | Tyce Easton |
| B | 2022-09-13 | Incorporated interface changes. | Tyce Easton |

**INTERNAL**
