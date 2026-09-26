# Attribution and rights for committed excerpts

Files under `agentsLog/Bukareszt/` (`audit/*.jsonl`, `examples/*`, `reports/*`) quote short chunks of text from the sources listed in `sources/sources.jsonl`. Each chunk carries a `source_id`; the manifest row gives the exact page revision (`url` is a permalink with `oldid`), retrieval time, SHA-256 of the fetched text, publisher and license.

- Polish Wikipedia articles (`plwiki-*`): text © Wikipedia contributors, licensed **CC BY-SA 4.0** (https://creativecommons.org/licenses/by-sa/4.0/). Quoted excerpts remain under CC BY-SA 4.0; attribution is by article title + permalink in the manifest.
- Polish Wikisource documents (`plws-*`): public-domain primary documents (historic state acts and manifestos; official documents are outside copyright under art. 4 of the Polish Copyright Act, and all authors died more than 70 years ago). The Wikisource transcription layer is CC BY-SA 4.0 and is attributed the same way.

No other third-party text is committed. Full source texts are not committed; they are rebuilt locally with `scripts/retrieval.py fetch` into the gitignored `raw/` folder. Nothing here derives from 2023, 2024 or 2025 matura exam sheets, answer keys, marking rubrics or exam source packs.
