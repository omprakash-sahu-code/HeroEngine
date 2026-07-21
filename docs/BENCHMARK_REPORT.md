# HeroEngine Benchmark Report

**Generated:** 2026-07-21 10:29:35  
**Git Commit:** `97ab336` | **Python:** `3.12.10` | **Platform:** `Windows 11 (64bit)`  
**CPU:** AMD64 Family 23 Model 104 Stepping 1, AuthenticAMD | **GPU:** ModernGL / OpenGL Hardware Accelerated  

## Scenario Metrics Summary

### Scenario: `VISION` (Status: SUCCESS)
| Metric | Min (ms) | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | StdDev |
|---|---|---|---|---|---|---|---|
| `frame_processing_latency_ms` | 4.4574 | 5.7929 | 5.548 | 7.4839 | 8.9294 | 14.3261 | 0.9181 |

### Scenario: `GESTURE` (Status: SUCCESS)
| Metric | Min (ms) | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | StdDev |
|---|---|---|---|---|---|---|---|
| `classification_latency_ms` | 0.001 | 0.0012 | 0.0011 | 0.0016 | 0.0018 | 0.3331 | 0.001 |

### Scenario: `RENDER` (Status: SUCCESS)
| Metric | Min (ms) | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | StdDev |
|---|---|---|---|---|---|---|---|
| `particle_update_latency_1000_ms` | 0.0445 | 0.0527 | 0.0476 | 0.0676 | 0.0937 | 0.4778 | 0.0126 |
| `particle_update_latency_5000_ms` | 0.1815 | 0.1918 | 0.1891 | 0.2289 | 0.2722 | 0.4615 | 0.0176 |
| `particle_update_latency_10000_ms` | 0.3514 | 0.3721 | 0.367 | 0.4236 | 0.5222 | 0.8844 | 0.0367 |

### Scenario: `NETWORK` (Status: FAILED)
> [!WARNING]
> Failure Reason: 'OSCTransport' object has no attribute 'serialize'

### Scenario: `MEMORY` (Status: SUCCESS)
| Metric | Min (ms) | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | StdDev |
|---|---|---|---|---|---|---|---|
| `gc_pause_latency_ms` | 5.1278 | 8.7365 | 7.221 | 15.8275 | 21.3848 | 52.3926 | 4.7586 |
