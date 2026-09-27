# Retrieval health, not exam recall

All six pinned official20231101.pl shards were indexed:1,587,721articles,2,729,746passages, zero excluded/empty articles. Exact source offsets and article provenance remain in the index. SQLite index SHA256: `5bf93ceca9715170f7a3b6497746cd00dac4dd80f7fe0b53fd0a3f981d88bb36`.

Eight independently written short factual queries and two inflected variants were checked. The saved passage text supports the requested fact within top5for the eight short factual queries; the two variants retrieve the appropriate topic. Examples cover Meiji, Nantes, Kalmar, Westphalia, Carnation Revolution, Hastings, Bandung and Watt. This is a small easy health set. Some individual passages are bibliography or merely related material; title matches are not evidence.

Actual complete six-question lexical inputs performed weakly, with bibliography authors and generic task nouns competing with historical clues. No keys or manually supplied identities were used to repair these queries. The proposed study therefore generates compact fallible queries from complete original sources before independent DIRECT passage filtering. Its retrieval quality is unmeasured until that run and passage audit.

Current query module excludes generic bibliography lines, selects informative IDF terms across the input, uses bounded suffix-prefix recall, and permits complementary passages from the same article while removing substantially overlapping spans. This is lexical normalization, not a Polish morphological analyzer. The200candidate OR pool can miss conjunctions; relevance scores do not establish historical support.

Four query CPU tests cover late inflected entities, complementary sections, generic-noun competition and bibliography exclusion. Corpus construction is unchanged by query revisions. No model call was used for these health checks.
