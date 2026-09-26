# Key-free May 2024 validation input

Rebuild the frozen 40-item model input and its 21 page PNGs directly from the official question PDF. No private file transfer is required. The script neither downloads nor opens the answer PDF, answer card, or evaluator keys. Scoring remains with the separate evaluator owner.

## Run on the GPU machine

Prerequisites: Python 3 and existing Poppler `pdftotext` / `pdftoppm` on PATH. Verification below used Poppler 22.02.0. Run from this repository's root:

```sh
python3 -B agentsLog/kwiscion/validation-2024-keyfree/bootstrap.py
```

The one network request downloads only the pinned official May 2024 question PDF. An upstream hash change causes refusal. To reuse an already acquired question PDF:

```sh
python3 -B agentsLog/kwiscion/validation-2024-keyfree/bootstrap.py \
  --question-pdf /absolute/path/MHIP-R0-100-A-2405-arkusz.pdf
```

Use `--poppler-bin /path/to/bin` if Poppler is not on PATH. A fresh `--output-dir agentsLog/<owner>/private/<run>` may be selected; the script refuses to overwrite a nonempty directory. After a failed or interrupted attempt, preserve the attempt and select a new output directory.

The default model-facing input is:

```text
agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.jsonl
```

Keep it beside its generated `pages/` directory: image paths are relative to the JSONL. All generated files are ignored by Git. Do not commit or redistribute the question PDF, question text, or images. Once bootstrap succeeds, the inference input and images are entirely local.

## Acceptance

- Exactly 40 rows: 29 image-labelled and 11 text-labelled, with 21 referenced pages rendered at 110 DPI.
- Runner input SHA-256 must be `f4df6bcb9c1152d42e3650e820dfee1b4d182a5ad065eea41c9c0be85a0003c7`. The script refuses to write the runner entry point unless this matches and every image has rendered.
- Question PDF SHA-256 must be `ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21`.
- The shared builder is checked against its LF-normalized hash before importing its question parser, image heuristic and prompt header. Its `main`, answer parser and rubric builder are never called. Item order and essay classification derive from the question sheet itself.
- `bootstrap_verification.json` records hashes and counts only. `verification.json` alongside this README contains the tested local image hashes; PNG bytes can vary with Poppler versions, so preserve the generated manifest for comparison. Input hash drift is always a hard failure.

Local verification on 26 September: both the existing-question-PDF route and a fresh official download completed and matched the frozen input exactly. All 21 rendered PNGs were byte-identical to the existing canonical private pages. The download run used a Python audit hook that raised on any attempted file access whose path contained `zasady` or `eval_keys`; no such access occurred. No model inference or scoring was performed by this bootstrap. The shared builder and input schema were unchanged.

## Existing lead-machine Poppler setup

The lead machine already has a project-local Ubuntu Poppler extraction. Inside WSL, from the repository root:

```sh
export LD_LIBRARY_PATH="$PWD/outputs/local-smoke/poppler-root/usr/lib/x86_64-linux-gnu"
python3 -B agentsLog/kwiscion/validation-2024-keyfree/bootstrap.py \
  --poppler-bin outputs/local-smoke/poppler-root/usr/bin \
  --question-pdf agentsLog/Pewciu6/private/validation_2024/MHIP-R0-100-A-2405-arkusz.pdf
```

The GPU teammate should use their existing Poppler installation; the ignored lead-machine binaries are not part of this handoff.
