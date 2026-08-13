"""E3 feasibility spike: text-vectorized card semantics.

Verdict (2026-08-13, Forge cardsfolder HEAD, 33,308 cards): even
stdlib TF-IDF over oracle text separates Spell Snare/Force Spike
(E2 distance 0 -> cosine .26) while keeping Cancel/Counterspell at
1.00 and removal/counter classes ~orthogonal. Session C should:
  1. bucket numeric tokens (damage, MV thresholds) - Shock/Lightning
     Strike at .17 shows raw TF-IDF over-weights short-text diffs;
  2. SVD to 32-48 dims, append to E2's 91 mechanical dims;
  3. try a neural sentence embedder first, keep TF-IDF+SVD as the
     validated offline fallback;
  4. gate on: Snare/Spike separated, P8 swap pairs stay close,
     class structure preserved.
Group 1 (known-top-of-library, hand differential) remains hand-built
STATE features - embeddings cannot encode what was seen.
Run: python3 rl/e3_text_spike.py /path/to/forge-src
"""
