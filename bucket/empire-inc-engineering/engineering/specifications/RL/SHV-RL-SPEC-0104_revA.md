---
document_number: SHV-RL-SPEC-0104
title: "Observatory telescope Specification"
revision: "A"
status: APPROVED
classification: INTERNAL
author: "Darek Fairholm"
approved_by: "Lucan Merriweather"
date: 2023-10-31
language: en
---

**INTERNAL**

# Observatory telescope Specification

| | |
|---|---|
| Document number | SHV-RL-SPEC-0104 |
| Revision | A |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Darek Fairholm |
| Approved by | Lucan Merriweather |
| Date | 2023-10-31 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the observatory telescope (RL-OBS) of the Research Laboratories on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-RL-05 (WBS 1.16.5), owned by Esme Crestwell.

The prime supplier for flight hardware is Alsakan Instruments. Responsible engineer: Darek Fairholm.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-RL-DWG-0204 | Observatory telescope general arrangement drawing |
| SHV-RL-BOM-0304 | Observatory telescope bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-PD-RL | Interface Control Document: Power Distribution / Research Laboratories |
| SHV-ICD-RL-CN | Interface Control Document: Research Laboratories / Computer Core & Data Network |

## 4. Description

The research laboratories host materials science, biology and astronomy groups: wet and dry labs, cleanroom suites, a zero-gravity laboratory and the station observatory.

The observatory telescope is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| RL-OBS-R01 | The observatory telescope shall provide a primary mirror diameter of 10.1 m. | 10.1 m | ±0.5% | Analysis |
| RL-OBS-R02 | The observatory telescope shall provide a pointing accuracy of 0.37 arcsec. | 0.37 arcsec | ±5% | Test |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| RL-OBS-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| RL-OBS-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| RL-OBS-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| RL-OBS-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| RL-OBS-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the RL test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2023-10-31 | Initial release. | Darek Fairholm |

**INTERNAL**
