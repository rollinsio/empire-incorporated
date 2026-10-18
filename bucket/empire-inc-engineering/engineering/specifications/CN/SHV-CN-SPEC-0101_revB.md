---
document_number: SHV-CN-SPEC-0101
title: "Central computer core Specification"
revision: "B"
status: APPROVED
classification: INTERNAL
author: "Riven Fairholm"
approved_by: "Tavi Orrun"
date: 2023-04-04
language: en
---

**INTERNAL**

# Central computer core Specification

| | |
|---|---|
| Document number | SHV-CN-SPEC-0101 |
| Revision | B |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Riven Fairholm |
| Approved by | Tavi Orrun |
| Date | 2023-04-04 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the central computer core (CN-CCO) of the Computer Core & Data Network on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-CN-02 (WBS 1.12.2), owned by Rafe Craddock.

The prime supplier for flight hardware is Eriadu Steelworks. Responsible engineer: Riven Fairholm.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-CN-DWG-0201 | Central computer core general arrangement drawing |
| SHV-CN-BOM-0301 | Central computer core bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-HR-CN | Interface Control Document: Hypermatter Reactor / Computer Core & Data Network |
| SHV-ICD-HB-CN | Interface Control Document: Docking & Hangar Bays / Computer Core & Data Network |
| SHV-ICD-CN-CM | Interface Control Document: Computer Core & Data Network / Communications Relay |
| SHV-ICD-CN-OC | Interface Control Document: Computer Core & Data Network / Operations Centre |
| SHV-ICD-CN-TR | Interface Control Document: Computer Core & Data Network / Internal Transit |
| SHV-ICD-RL-CN | Interface Control Document: Research Laboratories / Computer Core & Data Network |

## 4. Description

The computer core and data network connect every station system. Maintenance terminals and data ports give technicians and service droids access to the network.

The central computer core is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| CN-CCO-R01 | The central computer core shall provide a processing nodes of 5,485 ea. | 5,485 ea | ±0.5% | Test |
| CN-CCO-R02 | The central computer core shall provide a storage of 1,899 PB. | 1,899 PB | ±0.5% | Demonstration |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| CN-CCO-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| CN-CCO-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| CN-CCO-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| CN-CCO-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| CN-CCO-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the CN test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2022-12-07 | Initial release. | Riven Fairholm |
| B | 2023-04-04 | Updated requirement values after design review. | Riven Fairholm |

**INTERNAL**
