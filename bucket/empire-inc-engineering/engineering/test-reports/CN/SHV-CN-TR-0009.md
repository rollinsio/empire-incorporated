---
document_number: SHV-CN-TR-0009
title: "Acceptance test report: Central computer core (SN-CN-1157)"
revision: "1"
status: APPROVED
classification: INTERNAL
author: "Ferris Ardent"
approved_by: "Riven Fairholm"
date: 2024-01-13
language: en
---

**INTERNAL**

# Acceptance test report: Central computer core (SN-CN-1157)

| | |
|---|---|
| Document number | SHV-CN-TR-0009 |
| Revision | 1 |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Ferris Ardent |
| Approved by | Riven Fairholm |
| Date | 2024-01-13 |

## 1. Item under test

- **Component:** Central computer core (CN-CCO)
- **Serial number:** SN-CN-1157
- **Specification:** SHV-CN-SPEC-0101 Rev B
- **Procedure:** TP-CN-CCO-06

## 2. Test set-up

The test was performed on 2024-01-13 at the Station Integration Test Facility, Zone Z18. Test engineer: Ferris Ardent. Witness: Riven Fairholm.

- Thermal vacuum chamber TV-3
- Spectral alignment rig
- Calibrated field probe set

## 3. Results

| Requirement | Parameter | Required | Tolerance | Measured | Result |
|---|---|---|---|---|---|
| CN-CCO-R01 | Processing nodes | 5,485 ea | ±0.5% | 5,500 ea | PASS |
| CN-CCO-R02 | Storage | 1,899 PB | ±0.5% | 1,913.1 PB | FAIL |

## 4. Anomalies

Out-of-tolerance result recorded; non-conformance report NCR-2024-0017 raised.

## 5. Conclusion

Overall result: FAIL. The unit is held pending disposition of the non-conformance.

**INTERNAL**
