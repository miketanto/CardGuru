#!/usr/bin/env python3
"""Phase 13 Amendment 1: apply the make-or-break rule to the 2,048 level (rl/PHASE13-BC.md)."""
import math, re, sys
LOG = sys.argv[1] if len(sys.argv) > 1 else '/home/user/CardGuru/rl/artifacts/v7/13/c/phase13.log'
POINT = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
lines = open(LOG).read().splitlines()
lev = [l for l in lines if l.startswith('L13|level|') and f'trained={POINT}|' in l]
if not lev:
    print(f'MB|PENDING|no level line at trained={POINT}'); sys.exit(0)
L = lev[-1]
def kn(key):
    m = re.search(key + r'=(\d+)/(\d+)', L); return (int(m[1]), int(m[2])) if m else (0, 0)
s, t, a = kn('sampled_cp7'), kn('twostage_cp7'), kn('argmax_cp7')
k = w = 0
for l in lines:
    m = re.match(r'L13\|block\|.*trained=(\d+)->(\d+)\|opp=cp7\|W/L/D/S=(\d+)/(\d+)/(\d+)/(\d+)', l)
    if m and int(m[1]) >= POINT - 1024 and int(m[2]) <= POINT:
        k += int(m[3]); w += sum(int(m[i]) for i in (3, 4, 5, 6))
lo_b = wilson(k, w)[0]
a_ok = s[0] >= 43 or t[0] >= 43
b_ok = w > 0 and lo_b > 0.311
v = 'MAKE' if (a_ok or b_ok) else 'BREAK'
print(f'MB|{v}|point={POINT}|sampled={s[0]}/{s[1]}|twostage={t[0]}/{t[1]}|argmax={a[0]}/{a[1]}(not a MAKE readout)'
      f'|rule_a={"met" if a_ok else "not met"}(>=43/100)|cp7_train_blocks={k}/{w} lower={lo_b:.3f}|rule_b={"met" if b_ok else "not met"}(lower>0.311)')
