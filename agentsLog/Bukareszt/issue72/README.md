# #72 optional explicit temperature — @Bukareszt

Issue https://github.com/kwiscion/machinekind-matura/issues/72, branch `issue-72-Bukareszt-explicit-temperature`, started 2026-09-26 17:40 Europe/Warsaw. CPU only, **zero model calls**, no GPU, no data, $0. Not merged: root reviews the exact head after the active run terminates. This is preparation for a hypothesis. **Lower temperature is not claimed to improve accuracy**, and nothing here authorizes inference or changes a default.

## Change

- `infer.py` (lead-authorized scope exception): optional config field `temperature`. `load_config` accepts only `int`/`float` (so `bool`, `null`, strings, lists and objects are rejected), finite (NaN, ±Infinity and `1e999` are rejected), and within `0 <= t <= 2`. The bounds are checked before `math.isfinite`, so huge integers such as `10**400` are rejected rather than raising OverflowError (lead review of 7760ab3). `run_case` adds `"temperature"` to the payload only when the key is present in the config. No seed, top_k, top_p or other options were added, and no default changed.
- Candidate config (EXPERIMENTAL, NOT PROMOTED): [`scripts/Bukareszt/configs/gemma4-12b-val40-1024-temp0.2.experimental.json`](../../../scripts/Bukareszt/configs/gemma4-12b-val40-1024-temp0.2.experimental.json). It equals the root baseline `agentsLog/kwiscion/gemma4-12b-val40-1024.config.json` except for `"temperature": 0.2` and the local label `name` (`…-temp0.2-experimental`, which is never sent to the model). Its checked-in form with CRLF line endings is the pinned `3d9c5018…ed8effa` used by the bounded runners; that file and every other original config, input, source and key are unchanged.
- Tests: `scripts/Bukareszt/test_infer_temperature.py` (4 tests, no network). The shared `test_infer.py` is unchanged and passes 10/10.

## Exact payload difference (baseline vs candidate, text case)

```
- {"model": "gemma4:12b-it-q4_K_M", "messages": [{"role": "user", "content": "Pytanie"}], "max_tokens": 1024, "reasoning_effort": "none"}
+ {"model": "gemma4:12b-it-q4_K_M", "messages": [{"role": "user", "content": "Pytanie"}], "max_tokens": 1024, "reasoning_effort": "none", "temperature": 0.2}
```

Omitted-field equivalence was checked against the unmodified runner (`git show origin/main:infer.py`, main `7eada40`): for the baseline config, the request bytes from the old and new `infer.py` are identical for a text case and a text+image case. The candidate body equals the old body with `, "temperature": 0.2` inserted before the final `}`.

## Primary source: Ollama v0.30.7 (tag commit `f0078ae4766d0d570e196158f20dde309bd96124`)

- [`openai/openai.go` `FromChatRequest`](https://github.com/ollama/ollama/blob/v0.30.7/openai/openai.go#L593-L615) decodes `temperature` as `*float64`. If it is present, the value goes unchanged into `options["temperature"]`, with **no scaling, clamping or range check**. **If it is omitted, it sets `options["temperature"] = 1.0`.** Also, **if `top_p` is omitted, it sets `options["top_p"] = 1.0`**. `seed` is forwarded only when present. `top_k` is not an OpenAI field, so it comes from the model's Modelfile parameters or `api.DefaultOptions()` (40).
- [`server/routes.go` `modelOptions`](https://github.com/ollama/ollama/blob/v0.30.7/server/routes.go#L133-L150) layers the options: `api.DefaultOptions()` (temperature 0.8, top_k 40, top_p 0.9, seed -1) first, then the model's Modelfile options, then the request options, so the request wins.
- [`llm/llama_server.go`](https://github.com/ollama/ollama/blob/v0.30.7/llm/llama_server.go#L1394-L1411) copies `Options.Temperature` (float32) unchanged into the llama-server completion request.
- [`docs/api/openai-compatibility.mdx`](https://github.com/ollama/ollama/blob/v0.30.7/docs/api/openai-compatibility.mdx) lists `temperature` and `top_p` as supported but documents **no range**. The 0–2 bound used by `infer.py` is the OpenAI chat-completions reference range, which is the API that this endpoint emulates. Ollama itself would accept values outside that range.
- Source-derived note (not a runtime measurement; measured runs keep their recorded labels): for `/v1/chat/completions` requests that omit these fields, the v0.30.7 compat code sets **temperature 1.0 and top_p 1.0**. Those values take precedence over the model metadata's top_p 0.95, so the effective omitted top_p is expected to be 1.0 rather than 0.95. top_k is left to the Modelfile/defaults (not verified locally with `ollama show`). The seed is random (`-1`) unless supplied.
- With temperature 0.2, only the temperature changes; top_p stays 1.0 and top_k stays the same. The source gives no reason that 0.2 is unsuitable. It is an ordinary positive value within both the OpenAI range and Ollama's unchecked float pass-through, and it is not the `<= 0` greedy special case. The sampler semantics inside the vendored llama.cpp revision were not reviewed beyond the Ollama hand-off. Without a seed, a run at 0.2 is still stochastic.

## Commands

```bash
python3 -m unittest scripts/Bukareszt/test_infer_temperature.py -v   # 4 OK
python3 -m unittest test_infer -q                                     # 10 OK
python3 infer.py --config scripts/Bukareszt/configs/gemma4-12b-val40-1024-temp0.2.experimental.json --input <frozen input> --output /dev/null --dry-run   # validation only, no requests
```

Limitations: the tests run offline against a mocked opener, and no live request was made. A future full-arm manifest, the GPU owner, runtime qualification and independent scoring are separate lead decisions. The bounded runners pin the original config hash, so using this candidate would need a new declared manifest.
