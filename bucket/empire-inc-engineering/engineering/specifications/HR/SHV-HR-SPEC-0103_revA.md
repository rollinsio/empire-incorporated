---
document_number: SHV-HR-SPEC-0103
title: "Fuel injector assembly Specification"
revision: "A"
status: APPROVED
classification: CONFIDENTIAL
author: "Alira Aster"
approved_by: "Aldric Voss"
date: 2023-09-08
language: en
---

**CONFIDENTIAL**

# Fuel injector assembly Specification

| | |
|---|---|
| Document number | SHV-HR-SPEC-0103 |
| Revision | A |
| Status | APPROVED |
| Classification | CONFIDENTIAL |
| Author | Alira Aster |
| Approved by | Aldric Voss |
| Date | 2023-09-08 |

## 1. Purpose

This specification defines the performance, interface and verification requirements for the fuel injector assembly (HR-FIA) of the Hypermatter Reactor on Starhaven Orbital Habitat & Shipyard.

## 2. Scope

Fabrication and installation are performed under work package WP-SHV-HR-04 (WBS 1.1.4), owned by Edda Lancer.

The prime supplier for flight hardware is Kuat Precision Instruments. Responsible engineer: Alira Aster.

## 3. Applicable documents

| Document | Title |
|---|---|
| SHV-SYS-SPEC-0001 | Starhaven Master System Specification |
| SHV-HR-DWG-0203 | Fuel injector assembly general arrangement drawing |
| SHV-HR-BOM-0303 | Fuel injector assembly bill of materials |
| SHV-QA-PLN-0004 | Starhaven Verification and Test Plan |
| SHV-QA-STD-0002 | Station Workmanship Standard |
| SHV-ICD-HR-TX | Interface Control Document: Hypermatter Reactor / Thermal Control & Heat Rejection |
| SHV-ICD-HR-PD | Interface Control Document: Hypermatter Reactor / Power Distribution |
| SHV-ICD-HR-CN | Interface Control Document: Hypermatter Reactor / Computer Core & Data Network |

## 4. Description

The hypermatter reactor is the station's main power plant. It supplies every zone substation through the power distribution system and is backed by the solar collector array.

The fuel injector assembly is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test.

## 5. Performance requirements

| ID | Requirement | Value | Tolerance | Verification |
|---|---|---|---|---|
| HR-FIA-R01 | The fuel injector assembly shall provide a injection rate of 7.79 kg/s. | 7.79 kg/s | ±2.5% | Demonstration |
| HR-FIA-R02 | The fuel injector assembly shall provide a injector count of 128 ea. | 128 ea | ±1% | Analysis |

### 5.1 General requirements

| ID | Requirement | Verification |
|---|---|---|
| HR-FIA-G01 | Maintainability: Line-replaceable units shall be replaceable by a crew of four within one shift. | Inspection |
| HR-FIA-G02 | Safety: Single faults shall not cause loss of the zone or injury to crew. | Analysis |
| HR-FIA-G03 | Workmanship: Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002. | Inspection |
| HR-FIA-G04 | Marking: Every assembly shall carry its drawing number, revision and serial number. | Analysis |
| HR-FIA-G05 | Documentation: Acceptance data packages shall be delivered with every unit. | Inspection |

## 6. Environmental conditions

| Condition | Value |
|---|---|
| Operating pressure | Vacuum to 110 kPa |
| Radiation, total dose | Station design environment, class R3 |
| Thermal cycling | 200 cycles, operating range |
| Vibration | Station-keeping manoeuvre profile, level 2 |
| Electromagnetic compatibility | Station EMC standard, category B |

## 7. Verification

Each requirement is verified by the method stated in section 5, following SHV-QA-PLN-0004. Acceptance test reports are filed under the HR test-report series.

## 8. Revision history

| Rev | Date | Description | Author |
|---|---|---|---|
| A | 2023-09-08 | Initial release. | Alira Aster |

**CONFIDENTIAL**
