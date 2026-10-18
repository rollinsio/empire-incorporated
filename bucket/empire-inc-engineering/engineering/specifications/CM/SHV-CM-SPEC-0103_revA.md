---
document_number: SHV-CM-SPEC-0103
title: "Traffic routing switch Specification"
revision: "A"
status: APPROVED
classification: INTERNAL
author: "Edda Palin"
approved_by: "Tavi Orrun"
date: 2025-03-25
language: en
---

**INTERNAL**

# Traffic routing switch Specification

| | |
|---|---|
| Document number | SHV-CM-SPEC-0103 |
| Revision | A |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Edda Palin |
| Approved by | Tavi Orrun |
| Date | 2025-03-25 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the traffic routing switch (CM-TRS) of the Communications Relay on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-CM-04 (WBS 1.13.4), owned by Rafe Craddock.

The prime supplier for flight hardware is Mekuun Fabrication. Responsible engineer: Edda Palin.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-CM-DWG-0203 | Traffic routing switch general arrangement drawing |
| SHV-CM-BOM-0303 | Traffic routing switch bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-CN-CM | Interface Control Document: Computer Core & Data Network / Communications Relay |

## 4. Description

Communications covers HoloNet transceivers, comm array dishes and the switches that route passenger, cargo and station traffic.

The traffic routing switch is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| CM-TRS-R01 | The traffic routing switch shall provide a throughput of 8.2 Tbit/s. | 8.2 Tbit/s | ±1% | Analysis |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| CM-TRS-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| CM-TRS-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| CM-TRS-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| CM-TRS-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| CM-TRS-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the CM test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2025-03-25 | Initial release. | Edda Palin |

**INTERNAL**
