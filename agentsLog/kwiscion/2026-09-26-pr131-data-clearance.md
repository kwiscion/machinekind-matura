# PR131 independent data-clearance addendum

**Clear the canonical90-row export for one bounded essay pilot.** This completes the four historical checks left open in the prior independent export audit. It is data clearance, not runtime qualification or launch authorization. Reviewed head `fc9a7f4a07ae649228dfd12acf545361e5111d23`, merged as `38e5beb`;34 essays and56 repair pairs represent34 unique essay targets.

## Historical checks

- Verden: the execution is recorded in the782 entry of the [Royal Frankish Annals](https://www.thelatinlibrary.com/annalesregnifrancorum.html). The rejected date card is absent from accepted fact bindings; the exported sentence retains the execution without a date.
- Poland: [Yalta](https://avalon.law.yale.edu/wwii/yalta.asp) promises northern/western compensation and defers delimitation; [Potsdam](https://avalon.law.yale.edu/20th_century/decade17.asp) places specified territory under provisional Polish administration. The exported essay excludes the incorrect Yalta land-list card and states that Yalta did not determine the extent.
- Lithuania: the [official Seimas history](https://www.lrs.lt/sip/portal.show?p_k=2&p_r=35660) confirms11March1990. Direct access to the cited legal-register page was blocked; official parliamentary history supplies independent corroboration. The wrong August1991 card and its off-topic defect are excluded.
- Reparations: the [Peace Palace Library](https://peacepalacelibrary.nl/blog/2011/german-war-reparations-ww-i-financially-ended) distinguishes a reparations-related bond payment. Additional primary institutional support from [German federal BADV](https://badv.bund.de/offene-vermoegensfragen/wertpapiere/auslandsschulden) identifies deferred1945–1952 interest, converted after reunification, with final maturity3October2010. The export uses corrected reparations-related wording. The older card remains linked for the date only, not its incorrect implication that the original bill was fully paid.

## Executable evidence and exact handoff

All11 focused tests pass:9 contract/acceptance/dependency/error tests with report writes redirected to a temporary copy, plus2 checkout tests using exact head blobs in an isolated temporary repository. The new `essay_corpus/** -text` attribute is scoped to Greg's corpus. It preserves future checkouts; it does not rewrite existing CRLF files. An initial isolation attempt had a path-fixture error and reproduced the stale-byte failure; the corrected canonical test passed.

Training Git-blob SHA256 is unchanged at PR130 `401e1bc`, PR131 head and merge:
`83153814da8251210f2b9d225dc713ad245c273bdc5d46dd1216b0e4b97178f5`.
Current Windows disk SHA is `c5bd1b58678eeec3745437d9ea866130e9276471af34aff8ff3e559fee20fb57`. **Use a binary extraction of the canonical Git blob and verify the approved hash before staging.** Do not identify the stale checkout bytes as the approved byte artifact. Full reviewed blob hashes are in the companion JSON.

## Rights and evaluation limits

Attribution covers every row and retains source licenses/revisions. MIT Aristotle, UJ archive and AGAD Lublin remain `reference_fact_check_only`, with `source_text_exported: false`; canonical attribution omits that explicit field, so retain this addendum alongside the manifest. No new source redistribution permission is granted. An independent scan of all90 rows against the three stored HTML snapshots found zero shared8-word or20-word windows across alternate Polish decodings. This supports the original-composition finding, without proving absence of every shorter phrase. No source-text or quotation fields enter the training messages.

Use eval16 as an external quality test:16 original inputs, no gold full essays and no need to invent targets for loss/early stopping. The latest factcards resolve the three cited quote-support defects and add economic effects for eval04; they remain fallible, non-exhaustive evidence aids. Preserve interpretive caveats and independent grading/adjudication. The current card hash is `260e07097dc3a144e57a9fa90388adf6662f3e51db101edece82e97ee02e2124`.

Casimir/Lublin/January overlap older#80DEV; do not claim those topics as clean posttraining tests. Do not mix legacy#4 records into this cleared export because several overlap eval groups. Group separation and title checks are not exhaustive contamination or pretraining-novelty proofs. Compare any pilot with matched nonthinking base and the strongest native-thinking base. No full90-essay regrade, GPU, inference, shared Git mutation or teammate-file edit occurred.
