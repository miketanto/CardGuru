# NL → DSL Query Generation: Prior Art and Application to MTG Mechanical Search

**Research brief — August 2026**

Context: building a mechanical search engine over Forge card-script DSL primitives. The wall is
translating natural-language queries into correct DSL queries. This document establishes that the
problem is a well-studied one, collects the transferable findings, and proposes a diagnosis.

**Provenance note:** references marked ✅ were verified against sources in August 2026. References
marked ⚠️ are from background knowledge and were *not* re-verified — check them before relying on
specific numbers.

---

## 1. The problem has a name

This is **semantic parsing**, specifically *DSL generation* or *natural language interfaces to
databases* (NLIDB). Text-to-SQL is its largest instance; the structure is identical across domains.

✅ Grammar Prompting (Wang, Wang, Wang, Cao, Saurous & Kim, NeurIPS 2023, `2305.19234`) frames it
directly: semantic parsing requires an LLM to translate a natural-language utterance into an
executable program in a DSL, and DSLs "incorporate domain-specific abstractions and semantics that
are difficult to characterize via just a few demonstrations." Critically, DSLs are "by definition
specialized and thus unlikely to have been encountered often enough (or at all) during pretraining."

**That last point is the core difficulty and it applies maximally to Forge's DSL.** A frontier model
has seen enormous amounts of SQL. It has seen approximately zero `SP$ DealDamage | ValidTgts$ ...`.

### Instances of the same problem across domains

| Domain | Target language | Key resources |
|---|---|---|
| Relational DB | SQL | Spider, BIRD, Spider 2.0, BEAVER |
| Graph DB | Cypher | Neo4j Text2Cypher, SynthCypher, CypherBench, SpCQL |
| Semantic web | SPARQL | LC-QuAD, QALD ⚠️ |
| Planning | PDDL | Grammar Prompting eval suite ✅ |
| Chemistry | SMILES | Grammar Prompting eval suite ✅ |
| Calendar / geography | SMCalFlow, GeoQuery, Overnight | classic semantic parsing benchmarks ✅ |
| Logic | FOL / symbolic forms | ACL 2025 Industry GCD paper ✅ |
| Code search | Semgrep / ast-grep patterns | ⚠️ closest structural analogue to our task |

---

## 2. Finding: the bottleneck is schema linking, not syntax

The dominant error mode across text-to-SQL is not malformed queries. It is **selecting the wrong
schema elements** — mapping natural-language mentions onto the right tables and columns.

✅ Evidence, per the survey in `2604.25149` (Semantic Layers for Reliable LLM-Powered Data Analytics):

- **RESDSQL** (Li et al., 2023) decouples schema linking from SQL skeleton parsing, using a
  ranking-enhanced cross-encoder to filter schema items; significant gains on Spider robustness variants.
- **DIN-SQL** (Pourreza & Rafiei, 2023) decomposes the task into four modules "with schema linking as
  the first and most critical step," reaching 85.3% on Spider with GPT-4.
- **C3** (Dong et al., 2023) adds a calibration module specifically targeting "LLMs' tendency to select
  extra or wrong columns," reducing such errors by 11%.

✅ Continuing 2026 work treats it as the open problem: **EviLink** (`2605.29670`, multi-path schema
linking with uncertainty-guided evidence acquisition), **LinkAlign** (`2503.18596`, scalable
multi-database linking), **Rethinking Schema Linking** (`2510.14296`, context-aware bidirectional
retrieval), and **MAC-SQL** (Wang et al., 2024, Selector agent for minimal schema subsets).

**Application:** if generated queries parse fine but return the wrong cards, this is the failure mode.
Effort belongs in primitive selection, not grammar.

---

## 3. Counter-finding: schema linking may be unnecessary at our scale

✅ **"The Death of Schema Linking? Text-to-SQL in the Age of Well-Reasoned Language Models"**
(OpenReview `fglyh5pa7d`) argues the opposite for modern models: newer LLMs "accurately identify
relevant schema during SQL generation, even in the presence of substantial irrelevant data." Their
pipeline forgoes schema linking whenever the full schema fits in context, which "eliminates errors due
to faulty schema linking by ensuring that no schema information is omitted." **Ranked first on BIRD at
71.83%.**

The scale argument matters for us:

- ✅ Enterprise databases contain "on the order of 10³ columns" (`2606.28601`).
- ✅ BEAVER (`2409.02038v3`) reports that even BIRD databases average 6.8 tables / 72.5 columns, while
  Spider 2.0 averages 52.6 tables / 803.6 columns.
- **Forge's DSL vocabulary is a few hundred primitives.** It fits in context comfortably.

**Recommendation: try full-vocabulary-in-context as the baseline before building any retriever.**
Retrieval-based schema linking solves a problem we may not have, and it introduces a failure mode
(dropping the one primitive that mattered) that we currently don't have.

If the vocabulary later proves too large, ✅ **DBCC** (`2606.28601`) is the relevant technique — a
query-agnostic, database-side rewrite into a higher-density representation, reducing input by up to
two orders of magnitude (2.6M → 34.7K tokens on the hardest Spider 2.0-Snow bucket) while raising
strict schema-linking recall from 0% to 56.5%, and 63.1% under Claude Opus 4.7.

---

## 4. Finding: grammar constraints guarantee validity but aren't a silver bullet

✅ **Grammar prompting** (`2305.19234`) augments each demonstration with a *specialized* BNF grammar
minimally sufficient to generate that example. At inference the model first predicts a grammar for
the input, then generates according to it. This beat both standard prompting and plain
constrained decoding in few-shot semantic parsing.

✅ **Honest caveats from the same paper** — worth internalizing before investing here:

- Constrained decoding "significantly increases the number of API calls."
- Constraints were "not always beneficial for metrics beyond correctness" — they reduced diversity in
  molecule generation and hurt object selection in PDDL planning.
- Grammar prompting improved over standard prompting *even with unconstrained decoding*, meaning much
  of the gain comes from showing the model the grammar, not from enforcing it.

✅ **Grammar-Constrained Decoding Makes LLMs Better Logical Parsers** (ACL 2025 Industry,
`2025.acl-industry.34`) reports GCD "consistently improves both syntactic correctness and semantic
accuracy," and — relevant if we ever want a small local model — that grammar constraints "can serve as
an effective substitute for in-context examples, especially beneficial for resource-constrained
applications using smaller models."

⚠️ Tooling not verified this session: PICARD (incremental parsing during beam search), Outlines,
XGrammar, llguidance, llama.cpp GBNF.

**Recommendation:** write the BNF for the Forge query DSL regardless — it's needed for grammar
prompting, which is the cheaper half of the win. Add enforced decoding only if syntax errors show up
in the error taxonomy.

---

## 5. Finding: synthetic data works, and we are unusually well positioned

✅ **SynthCypher / Auto-Cypher** (`2412.12612`) is the closest methodological analogue. An
LLM-supervised **generation-verification** framework produced 29.8k Text2Cypher instances; fine-tuning
LLaMa-3.1-8B, Mistral-7B and Qwen-7B on it yielded **up to 40% improvement** on the Text2Cypher test
split and 30% on a Cypher-adapted SPIDER. Their motivation is telling: the earlier Neo4j Labs
GPT-4o-generated dataset, produced "without any validation steps on a limited domain set, with only 6
query types," yielded **only 50% correctly executable Cypher**. Verification is what made it work.

✅ Related: **KG2Cypher** (`2606.27742`) is a data-centric pipeline for enterprise KGs whose schemas
can't be published — relevant if we later need domain-private variants. `2505.05118` catalogs further
datasets: SyntheT2C, CySpider, Rel2Graph, S2CTrans, SpCQL (10,000 pairs).

**Our advantage: SynthCypher had to invent its programs. We already have ~30,000 real ones.**

⚠️ The technique to use is the **Overnight** method (Wang, Berant & Liang, ACL 2015): generate
canonical utterances directly from the grammar, then paraphrase them into natural language. Inverted
for our case:

```
Forge card script  →  canonical NL description (deterministic, template-based)
                   →  LLM paraphrase into player-style phrasings (n variants)
                   →  (NL, DSL query) training/eval pairs
```

Every pair is correct by construction, because the DSL side came first. This is free supervision at a
scale no hand-annotation effort can reach, and it also produces the eval set.

---

## 6. Finding: grade on execution, not string similarity

✅ Neo4j's Text2Cypher benchmarking used two procedures: **translation** (textual comparison of
predicted against reference queries, e.g. Google BLEU) and **execution** (run both queries, compare
outputs, ExactMatch). ✅ Mind the Query (Chauhan et al., 2025) similarly emphasizes execution-grounded
benchmarking with validation checks.

For mechanical search, execution accuracy means **result-set comparison** — Jaccard or exact set match
over returned card names. Two syntactically different queries returning identical card sets are both
correct. String match would score one of them wrong.

### Benchmark-design warning

✅ The BIRD benchmark has documented integrity problems worth learning from (per a June 2026 analysis):
22 gold SQL queries are outright wrong; when corrected, **model rankings reverse** — zero-shot GPT-3.5
outperforms DIN-SQL and MAC-SQL, systems specifically designed to beat it. The financial domain
carries a 49% noise rate. A benchmark whose rankings flip on cleanup is measuring annotation artifacts.

✅ For calibration on how far the field actually is: leading BIRD systems reach ~81.95% test accuracy
against ~92.96% human performance, and the gap closed "mainly through elaborate multi-step pipelines,
not raw model capability." On the harder enterprise BEAVER benchmark (`2409.02038v3`), agentic methods
with GPT-5.2 achieve **10.8% execution accuracy**.

**Implication: do not expect a clean 90%. Design the product to degrade gracefully and show its work.**

---

## 7. Diagnosis: the likely MTG-specific wall is vocabulary, not parsing

Players do not speak in DSL primitives. They say *tutor*, *wrath*, *blink*, *sac outlet*, *removal*,
*goes wide*, *ramp*, *stax*. None of these are Forge primitives; several map to disjunctive families
of primitives, and some are format-dependent.

This is exactly the gap BIRD was built to measure:

✅ BIRD "introduces external knowledge evidence — domain hints, value mappings, and synonym definitions
— alongside its 12,751 question-SQL pairs" (`2604.25149`), and ✅ "the 20 pp swing from adding knowledge
evidence is a reproducible and important finding."

Twenty points. That is larger than any prompting or architecture gain in this document.

✅ The known limitation: BIRD's evidence is "hand-written, per-query, by annotators with domain
expertise," which "is not a realistic deployment scenario." ✅ But the **SEED** paper (2025) showed
"automatically generated evidence can match or exceed hand-written evidence in some settings."

### Recommendation: build a slang → DSL-pattern alias layer as a first-class artifact

- Structure: `community_term → { DSL pattern (possibly disjunctive), CR rules, canonical gloss, format caveats }`
- **Mine it, don't hand-author it.** Candidate sources: EDHREC theme/tag pages, Scryfall's own
  community tags, deck-archetype taxonomies, MTG Wiki slang glossary, Stack Exchange usage.
- Version it separately from the ontology; slang drifts faster than rules.
- Treat it as retrievable evidence injected at query time — the automated analogue of BIRD evidence.

---

## 8. Diagnostic decision tree

Classify failures before choosing a fix. Build the error taxonomy first.

| Symptom | Diagnosis | Fix |
|---|---|---|
| Query is malformed / won't parse | Syntax | Grammar prompting (§4); enforced decoding if persistent |
| Parses, returns nothing | Over-constrained primitive selection | Schema linking / calibration (§2); relaxation-and-retry loop |
| Parses, returns wrong cards | Wrong primitives chosen | Full-vocabulary context (§3); more few-shot pairs (§5) |
| Parses, plausible cards, misses the intent | **Vocabulary mismatch** | Alias layer (§7) — this is likely the wall |
| Right for simple queries, wrong for compound ones | Compositional generalization | Decomposition (DIN-SQL pattern); synthetic compound examples |

---

## 9. Recommended pipeline

1. **Write the BNF** for the query DSL. Needed for grammar prompting and for validating synthetic data.
2. **Generate the corpus** via inverted Overnight: card script → canonical NL → LLM paraphrase. Verify
   every pair by execution (SynthCypher's lesson: unverified generation gave 50% executability).
3. **Baseline: full vocabulary in context**, grammar-prompted, few-shot with retrieved similar examples.
   Do not build a retriever until this is measured.
4. **Build the alias layer** and inject it as retrieved evidence. Measure the delta — expect this to be
   the largest single gain.
5. **Evaluate on execution** (result-set overlap), with a held-out split from real user phrasings, not
   only synthetic paraphrases.
6. **Add a repair loop**: on empty or error results, feed the failure back for one revision attempt.
7. Only then consider fine-tuning a small model on the synthetic corpus (the SynthCypher +40% result
   suggests this is worth it once the data exists).

---

## 10. Reading list, in order

1. `2305.19234` — Grammar Prompting (NeurIPS 2023) — the framing paper, read first
2. OpenReview `fglyh5pa7d` — The Death of Schema Linking? — why you may not need a retriever
3. `2412.12612` — Auto-Cypher / SynthCypher — the data-generation blueprint
4. `2604.25149` — Semantic Layers — best compact survey of the schema-linking literature
5. `2025.acl-industry.34` — GCD for logical parsing — constrained decoding, honestly assessed
6. `2409.02038v3` — BEAVER — the sobering realistic-difficulty benchmark
7. `2606.28601` — DBCC — if vocabulary scale ever becomes the problem
8. ⚠️ Wang, Berant & Liang (ACL 2015), *Building a Semantic Parser Overnight* — the paraphrase method
9. `2606.27742` — KG2Cypher — deployment-oriented pipeline design

---

## 11. Open questions for our case

- Does the Forge DSL vocabulary actually fit in context with enough per-primitive documentation to be
  useful, or does the documentation dominate the token budget?
- Can canonical NL be generated from card scripts deterministically, or does `Count$` (whose semantics
  live in `AbilityUtils.xCount`, not the script) break templating for a significant fraction of cards?
- Is result-set overlap the right metric, or does ranking matter enough to need a graded measure?
- How much of the alias layer can be mined automatically before hand-curation becomes necessary?
- Does a query DSL for *search* even need to be the Forge DSL, or should we design a separate query
  language over the extracted graph and keep Forge's syntax purely as the ingestion format? **This is
  probably the most important unresolved design question and it should be settled before more effort
  goes into the parser.**
