---
document_number: SHV-HB-SPEC-0011
title: "Main hangar bay Specification"
revision: "C"
status: REJECTED
classification: INTERNAL
author: "Noa Greaves"
approved_by: "Dorian Hask"
date: 2025-09-28
language: en
---

**INTERNAL**

# Main hangar bay Specification

| | |
|---|---|
| Document number | SHV-HB-SPEC-0011 |
| Revision | C |
| Status | REJECTED |
| Classification | INTERNAL |
| Author | Noa Greaves |
| Approved by | Dorian Hask |
| Date | 2025-09-28 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the main hangar bay (HB-MHB) of the Docking & Hangar Bays on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-HB-02 (WBS 1.6.2), owned by Danna Wade.

The prime supplier for flight hardware is Raxus Coolant Works. Responsible engineer: Noa Greaves.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-HB-DWG-0201 | Main hangar bay general arrangement drawing |
| SHV-HB-BOM-0301 | Main hangar bay bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-PD-HB | Interface Control Document: Power Distribution / Docking & Hangar Bays |
| SHV-ICD-HB-SY | Interface Control Document: Docking & Hangar Bays / Shipyard Slipways |
| SHV-ICD-HB-CN | Interface Control Document: Docking & Hangar Bays / Computer Core & Data Network |
| SHV-ICD-SF-HB | Interface Control Document: Superstructure & Frame / Docking & Hangar Bays |

## 4. Description

The docking and hangar bays receive, service and launch passenger shuttles, cargo haulers and visiting ships behind magnetic atmosphere containment fields.

The main hangar bay is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| HB-MHB-R01 | The main hangar bay shall provide a bay count of 384 ea. | 384 ea | ±0.5% | Analysis |
| HB-MHB-R02 | The main hangar bay shall provide a atmosphere field rating of 99.5 %. | 99.5 % | ±2.5% | Test |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| HB-MHB-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| HB-MHB-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| HB-MHB-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| HB-MHB-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| HB-MHB-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the HB test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2024-11-02 | Initial release. | Noa Greaves |
| B | 2025-03-14 | Updated requirement values after design review. | Noa Greaves |
| C | 2025-09-28 | Bay count set to 384 ea (rejected). | Noa Greaves |

**INTERNAL**
