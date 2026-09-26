# #96 factual-evidence lab — H100 wave 1 (`greg-h100-wave-1`)

26 September 2026. Host `matura-greg` (Brev `sx8ihq0wx`, H100 PCIe 80 GB). Runtime: Ollama 0.34.4 (executable `ad9c5344…2ff4`), `gemma4:12b-it-q4_K_M` (digest `4eb23ef1…b05c`), context 32768. The unchanged bare config (`3d9c5018…`, CRLF pin) is used: thinking off, 1024 output cap, 420 s timeout, temperature omitted. The server and runner share one `unshare -rn` namespace with loopback only. The runtime profile is `scripts/Bukareszt/runtime_profiles/h100-matura-greg-ollama-0.34.4.json` (canonical SHA `a8af3f3c…93af`).

**Status: W1 graded by root (17:54Z): bare 1/5 vs corrected-selective 1/5, no gain; corrected-selective is not expanded. W2 awaits the independent Sol reviewer.** Independent grading is requested on #11. The numbers below are descriptive only; they do not count as score evidence. I do not grade my own track.

## Envelope and ledger

| | used | wave cap |
|---|---|---|
| calls | **72** = 70 experiment calls (W1 10, W2 60; 0 errors, 0 retries) + 2 readiness calls | 120 (48 left) |
| requested output/reasoning tokens | **73,728** = 71,680 experiment (70 × 1024; reasoning off) + 2,048 readiness | 240,000 (166,272 left) |
| actual prompt / completion tokens | 67,780 / 9,636 | – |
| mechanism families | **4**: corrected-selective-rag, retrieve-verify-answer, question-to-relation, fact-cards (bare = comparator) | 4 |
| wave window | first launch 17:36:55Z (deadline 19:06:55Z); last call 17:42:05Z; summed request latency 165.9 s | 90 min |

The window cap was well respected: the last call came about 5.3 minutes after the first launch.

**Timing and cost:**
- **Rate:** `rate_unverified: true`. As a planning proxy only, I use the central instance's $3.28/hour. This is not a bill, and it is not a cap; the provider charge must be reconciled separately.
- **Instance:** `matura-greg` has been up since ≈16:49Z.
- **This session's use:** setup plus wave ran 17:25Z–17:43Z, ≈18 min, which is ≈$1.0 at the proxy rate.
- **Qualification:** the 2 synthetic readiness calls (answers `4e62aaee…`) are not rows in `ledger.jsonl`, but per root (17:54Z) they **count toward the envelope**. `wave_state.json` records them under `external`, and `wave_run.py` adds them before every cap check.

Ledger: `ledger.jsonl` (one row per attempt, including arm, role and tokens).

## Inputs (question-only; no keys)

- **Source-v2:** built locally with root's `bootstrap.py` + `repair-v2.py`. The SHA-256 is `6615fea2…15a4`, the canonical value.
- **W1:** the 5 source-v2 items that the corrected PR #104 gate admits (z2, z5.1, z7, z18, z24).
  - Pairs: bare `b083dc8f…`, selective `673eec56…`.
  - Selection: the router and gate only; no scores used.
- **W2 subset S10** (`subset-s10.jsonl`, SHA `c250d92b…a5c0`):
  - Pool: the 26 items the question-only router marks external_fact/mixed.
  - Order: `sha256("issue96-subset:"+id)`.
  - Chosen: the first 6 that the published bare RTX review scored below max, plus the first 4 at max (previously correct controls).
  - Items: z20.2, z23.2, z14.1, z19.2, z25, z7 | controls z17.1, z8.2, z18, z12.3.
  - No answer text, keys or past improvements were used.

## Mechanisms (`scripts/Bukareszt/wave_mechanisms.py`)

Every arm is `[#57 untrusted-reference block] + original prompt (verbatim suffix, images unchanged)`, or the original prompt when there is nothing to add. Auxiliary calls are text-only.

| arm | family | calls/case | prompts changed |
|---|---|---|---|
| W1-selective | corrected-selective-rag (PR #104 gate, 1 compact passage) | 1 | 5/5 (by construction) |
| W2-verify | retrieve-verify-answer: top-3 for the decontaminated query; the model marks which passages are needed | 2 | **3/10** (model said BRAK on 7) |
| W2-relquery | question-to-relation: the model writes an entity/relation/period query; top-2 compact windows | 2 | 10/10 |
| W2-factcard | fact cards: ≤5 verbatim dated/entity sentences from the top-3 chunks | 1 | 9/10 |

All 30 W2 evidence prefixes replay exactly from the recorded auxiliary outputs: 30/30 final-prompt SHA-256 matches (`evidence.jsonl`).

## Descriptive observations (ungraded)

- **Decisions mostly unchanged:** most decision/letter first lines are identical to bare across arms (z18, z7, z23.2, z12.3, W1 z2/z5.1/z24).
- **z14.1** flips from bare "Tak" to "Nie" in all three W2 mechanisms. Bare had 0 there in the published review; the flip needs grading.
- **z19.2** (bare 0, factual loss): relquery answers with a named person, while bare, verify and factcard give structured answers. It needs grading.
- **The verifier is conservative:** it rejected the retrieved passages for 7/10 items, which matches the low-coverage finding for the pinned 107-article corpus.
- **Relquery drifts on some items:** some model-written queries anchor on the wrong topic (z23.2 "Referendum 2015"; z25 is generic). Its insertions are therefore not gated for relevance; this is a known risk of the family.

## Files

- `answers.jsonl`: exact final answers with arm, ID, finish reason, usage, latency and prompt hash.
- `aux_outputs.jsonl`: auxiliary outputs, i.e. verifier verdicts and written queries.
- `evidence.jsonl`: the exact inserted evidence, verbatim CC BY-SA Wikipedia excerpts; attribution in `agentsLog/Bukareszt/ATTRIBUTION.md`.
- `ledger.jsonl`, `w1-plan.json`, `w2-plan.json`.

Full provider responses, exam prompts and page images stay private on the host and in the local backup (`agentsLog/Bukareszt/private/wave/`): W1 raw `52eac28a…`, W2 raw `7ac3e5be…`.
