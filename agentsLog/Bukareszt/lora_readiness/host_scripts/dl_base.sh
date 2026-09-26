#!/bin/bash
set -u
R=/ephemeral/mm-lora; REV=707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7
B=$R/base/gemma-4-12B-it@707f0a3b; mkdir -p $B $R/logs
cd $B
for f in .gitattributes README.md chat_template.jinja config.json generation_config.json processor_config.json tokenizer.json tokenizer_config.json model.safetensors; do
  echo "$(date -u +%FT%TZ) start $f"
  curl -sfL --retry 5 -C - -o "$f" "https://huggingface.co/google/gemma-4-12B-it/resolve/$REV/$f" || echo "FAIL $f"
  echo "$(date -u +%FT%TZ) done $f $(stat -c %s "$f")"
done
sha256sum * .gitattributes > $R/logs/base_sha256.txt
echo "$(date -u +%FT%TZ) ALLDONE"
