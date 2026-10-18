---
document_number: SHV-CN-TR-0007
title: "Functional test report: Central computer core (SN-CN-7246)"
revision: "1"
status: APPROVED
classification: INTERNAL
author: "Kesia Renner"
approved_by: "Riven Fairholm"
date: 2025-07-28
language: en
---

**INTERNAL**

# Functional test report: Central computer core (SN-CN-7246)

| | |
|---|---|
| Document number | SHV-CN-TR-0007 |
| Revision | 1 |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Kesia Renner |
| Approved by | Riven Fairholm |
| Date | 2025-07-28 |

## 1. Item under test

- **Component:** Central computer core (CN-CCO)
- **Serial number:** SN-CN-7246
- **Specification:** SHV-CN-SPEC-0101 Rev B
- **Procedure:** TP-CN-CCO-02

## 2. Test set-up

The test was performed on 2025-07-28 at the Station Integration Test Facility, Zone Z05. Test engineer: Kesia Renner. Witness: Riven Fairholm.

- Data acquisition rack DAQ-12
- Calibrated field probe set
- Spectral alignment rig

## 3. Results

| Requirement | Parameter | Required | Tolerance | Measured | Result |
|---|---|---|---|---|---|
| CN-CCO-R01 | Processing nodes | 5,485 ea | ±0.5% | 5,480 ea | PASS |
| CN-CCO-R02 | Storage | 1,899 PB | ±0.5% | 1,897.1 PB | PASS |

## 4. Anomalies

None.

## 5. Conclusion

Overall result: PASS. The unit is released for integration.

**INTERNAL**
