# Vast A6000 baseline — vanilla + worker, 2026-10-31

Added alongside the 2026-10-30 vanilla baselines; same suites, n=3, llama-server build 12019, context 50k, medium deadline 1800s.

| config | pass | turns (reps) | wall (reps) |
|---|---|---|---|
| BF16-bare-easy | 2/3 | 17 10 25 | 1:11 0:38 2:10 |
| BF16-bare-medium | 1/3 | 111 36 56 | 19:53 4:00 9:29 |
| BF16-worker-easy | 2/3 | 50 34 47 | 4:37 3:27 3:37 |
| BF16-worker-medium | 2/3 | 70 47 58 | 7:43 5:47 8:33 |
| Q4_K_M-bare-easy | 0/3 | 19 17 16 | 1:19 0:48 0:41 |
| Q4_K_M-bare-medium | 1/3 | 73 73 98 | 9:45 10:12 14:42 |
| Q4_K_M-worker-easy | 1/3 | 56 58 45 | 3:41 3:30 2:29 |
| Q4_K_M-worker-medium | 0/3 | 93 85 76 | 9:06 6:20 6:04 |
| Q8_0-bare-easy | 1/3 | 10 44 16 | 0:25 5:35 1:07 |
| Q8_0-bare-medium | 0/3 | 9 105 44 | 0:26 26:46 4:38 |
| Q8_0-worker-easy | 2/3 | 39 27 36 | 2:58 2:05 4:18 |
| Q8_0-worker-medium | 1/3 | 52 70 79 | 4:29 5:18 6:03 |
