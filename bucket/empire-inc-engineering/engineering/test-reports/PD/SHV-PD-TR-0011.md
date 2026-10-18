---
document_number: SHV-PD-TR-0011
title: "Functional test report: Storage battery string (SN-PD-9688)"
revision: "1"
status: APPROVED
classification: INTERNAL
author: "Oren Pike"
approved_by: "Venn Nash"
date: 2026-02-02
language: en
---

**INTERNAL**

# Functional test report: Storage battery string (SN-PD-9688)

| | |
|---|---|
| Document number | SHV-PD-TR-0011 |
| Revision | 1 |
| Status | APPROVED |
| Classification | INTERNAL |
| Author | Oren Pike |
| Approved by | Venn Nash |
| Date | 2026-02-02 |

## 1. Item under test

- **Component:** Storage battery string (PD-SBS)
- **Serial number:** SN-PD-9688
- **Specification:** SHV-PD-SPEC-0104 Rev A
- **Procedure:** TP-PD-SBS-04

## 2. Test set-up

The test was performed on 2026-02-02 at the Kuat Orbital Depot acceptance bay. Test engineer: Oren Pike. Witness: Venn Nash.

- Calibrated field probe set
- Precision metrology arm
- Data acquisition rack DAQ-12

## 3. Results

| Requirement | Parameter | Required | Tolerance | Measured | Result |
|---|---|---|---|---|---|
| PD-SBS-R01 | Storage capacity | 101 GWh | ±2.5% | 100.8 GWh | PASS |
| PD-SBS-R02 | Discharge time | 5.0 h | ±2.5% | 5.16 h | FAIL |

## 4. Anomalies

Out-of-tolerance result recorded; non-conformance report NCR-2026-0016 raised.

## 5. Conclusion

Overall result: FAIL. The unit is held pending disposition of the non-conformance.

**INTERNAL**
