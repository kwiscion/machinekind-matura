"""CPU-only regression: llama.cpp @fcb3074f jinja lexer source normalization vs pinned Gemma HF template.

Faithful Python port of common/jinja/lexer.cpp lines 37-58 (lexer::tokenize), whose `src` is returned
as lexer_result.source (line 338) -> common_chat_template::src (common/chat.h:63) -> source() (chat.h:71)
-> common_chat_templates_source (common/chat.cpp:754) -> /props "chat_template" (server-context.cpp:4609,4629).
Also reproduces common_chat_templates_init's string_replace_all trigger checks (common/chat.cpp:790-808).
Usage: python template_normalization_regression.py RAW_JINJA CONTROL_GGUF GGUF_PY_DIR
No model calls; reads files only; prints JSON to stdout.
"""
import hashlib, json, sys

EXPECT_RAW = 'ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4'
EXPECT_SERVED = '6a1015c47ccfcfa67c3b772385bccee357a4d37c3cda37bd202e9047f391ab82'


# Outputs of the ACTUAL pinned C++ lexer (t.cpp linked to build-cuda/bin/libllama-common.so.0.5.0, sha 655f1829...)
CPP_DISCRIMINATORS = {
    'two_nl': (b'x{{ a }}\n\n', '787b7b2061207d7d0a'),
    'trail_space_nl': (b'x{{ a }} \n', '787b7b2061207d7d20'),
    'crlf_end': (b'x\r\n{{ a }}\r\n', '780a7b7b2061207d7d'),
    'lone_cr_end': (b'x\r{{ a }}\r', '780a7b7b2061207d7d0a'),
    'lead_ws': (b' \n{{ a }}\n', '200a7b7b2061207d7d'),
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def lexer_normalize(source: bytes) -> bytes:
    src = bytearray(source)                    # L37  std::string src = source;
    if not source:                             # L39-41
        return bytes(src)
    pos = 0                                    # L44-47 erase '\r' of each "\r\n", then ++pos
    while True:
        pos = src.find(b'\r\n', pos)
        if pos == -1:
            break
        del src[pos]
        pos += 1
    pos = 0                                    # L48-51 replace remaining lone '\r' with '\n'
    while True:
        pos = src.find(b'\r', pos)
        if pos == -1:
            break
        src[pos] = 0x0A
        pos += 1
    if source[-1:] == b'\n':                   # L56-58 test ORIGINAL source.back(), pop one char
        src.pop()
    return bytes(src)


def cpp_hacks(src: bytes) -> dict:
    s = src.decode('utf-8')
    return {
        'channel_hack_applies': '<|channel|>' in s and 'in message.content or' in s,
        'tool_calls_hack_applies': '[TOOL_CALLS]' in s and "if (message['content'] is none or" in s,
        'contains_<|channel|>': '<|channel|>' in s,
        'contains_[TOOL_CALLS]': '[TOOL_CALLS]' in s,
        'is_empty_or_chatml': s == '' or s == 'chatml',
    }


def main():
    raw_path, gguf_path, gguf_py = sys.argv[1:4]
    sys.path.insert(0, gguf_py)
    import gguf
    raw = open(raw_path, 'rb').read()
    r = gguf.GGUFReader(gguf_path)
    kv = {}
    for name in ('tokenizer.chat_template', 'tokenizer.chat_template.tool_use'):
        f = r.fields.get(name)
        kv[name] = bytes(f.parts[f.data[0]]) if f is not None else None
    other_tmpl_keys = sorted(k for k in r.fields if 'chat_template' in k)
    g = kv['tokenizer.chat_template']
    trailing_nl = len(raw) - len(raw.rstrip(b'\n'))
    norm = lexer_normalize(g)
    alts = {
        'no_strip': g,
        'strip_all_trailing_whitespace(rstrip)': g.rstrip(),
        'strip_all_trailing_newlines': g.rstrip(b'\n'),
        'python_strip()': g.strip(),
        'crlf_only_no_pop': g.replace(b'\r\n', b'\n').replace(b'\r', b'\n'),
        'pop_two_newlines': g[:-2] if g.endswith(b'\n\n') else g,
    }
    alt_hashes = {k: sha(v) for k, v in alts.items()}
    out = {
        'raw_path': raw_path, 'raw_sha256': sha(raw), 'raw_len': len(raw),
        'raw_cr_count': raw.count(b'\r'), 'raw_crlf_count': raw.count(b'\r\n'),
        'raw_trailing_newline_count': trailing_nl, 'raw_last_bytes_hex': raw[-8:].hex(),
        'gguf_path': gguf_path, 'gguf_template_keys': other_tmpl_keys,
        'gguf_template_sha256': sha(g), 'gguf_template_len': len(g),
        'gguf_template_equals_raw': g == raw,
        'gguf_tool_use_template_present': kv['tokenizer.chat_template.tool_use'] is not None,
        'cpp_init_hacks': cpp_hacks(g),
        'lexer_normalized_sha256': sha(norm), 'lexer_normalized_len': len(norm),
        'lexer_normalized_equals_raw_minus_one_trailing_nl': norm == raw[:-1],
        'alternative_hashes': alt_hashes,
        'alternatives_matching_served': [k for k, v in alt_hashes.items() if v == EXPECT_SERVED],
    }
    out['checks'] = {
        'raw_sha_is_pinned': out['raw_sha256'] == EXPECT_RAW,
        'gguf_equals_raw': out['gguf_template_equals_raw'],
        'normalized_is_served': out['lexer_normalized_sha256'] == EXPECT_SERVED,
        'no_cpp_hack_applies': not out['cpp_init_hacks']['channel_hack_applies'] and not out['cpp_init_hacks']['tool_calls_hack_applies'] and not out['cpp_init_hacks']['is_empty_or_chatml'],
        'no_strip_differs_from_served': alt_hashes['no_strip'] != EXPECT_SERVED,
        'python_port_matches_cpp_on_discriminators': all(lexer_normalize(i).hex() == h for i, h in CPP_DISCRIMINATORS.values()),
    }
    # NOTE: on THIS template (0 CR, exactly one trailing '\n', no leading whitespace, last byte before '\n' is '}'),
    # rstrip()/strip()/rstrip('\n') are byte-identical to the lexer rule, so they cannot be told apart by hash here.
    out['alternatives_distinguishable_on_this_template'] = sorted(k for k, v in alt_hashes.items() if v != EXPECT_SERVED)
    out['alternatives_indistinguishable_on_this_template'] = out['alternatives_matching_served']
    out['discriminators'] = {k: {'python_port_hex': lexer_normalize(i).hex(), 'cpp_hex': h,
                                 'rstrip_hex': i.rstrip().hex(), 'strip_hex': i.strip().hex()} for k, (i, h) in CPP_DISCRIMINATORS.items()}
    out['pass'] = all(out['checks'].values())
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
