---
document_number: SHV-CN-TR-0006
title: "Functional test report: Maintenance data port (SN-CN-4206)"
revision: "1"
status: APPROVED
classification: INTERNAL
author: "Rain Calder"
approved_by: "Dorne Lancer"
date: 2023-09-25
language: en
---

**INTERNAL**

# Functional test report: Maintenance data port (SN-CN-4206)

| | |
|---|---|
| Document number | SHV-CN-TR-0006 |
| Revision | 1 |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Rain Calder |
| Approved by | Dorne Lancer |
| Date | 2023-09-25 |

## 1. Item under test

- **Component:** Maintenance data port (CN-MDP)
- **Serial number:** SN-CN-4206
- **Specification:** SHV-CN-SPEC-0103 Rev A
- **Procedure:** TP-CN-MDP-07

## 2. Test set-up

The test was performed on 2023-09-25 at the Station Integration Test Facility, Zone Z18. Test engineer: Rain Calder. Witness: Dorne Lancer.

- Containment field analyser
- Calibrated field probe set
- Spectral alignment rig

## 3. Results

| Requirement | Parameter | Required | Tolerance | Measured | Result |
|---|---|---|---|---|---|
| CN-MDP-R01 | Port count | 12,761 ea | ±0.5% | 12,846 ea | FAIL |

## 4. Anomalies

Out-of-tolerance result recorded; non-conformance report NCR-2023-0013 raised.

## 5. Conclusion

Overall result: FAIL. The unit is held pending disposition of the non-conformance.

**INTERNAL**
