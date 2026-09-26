#!/bin/bash
set -u
R=/ephemeral/mm-lora; cd $R/src
curl -sfL -o transformers-96331a9f.zip https://codeload.github.com/huggingface/transformers/zip/96331a9f93b72697f160a958d2883d4b49a56739 || echo FAIL_T
curl -sfL -o peft-b8674c86.zip https://codeload.github.com/huggingface/peft/zip/b8674c86183a5dee38d0c3ede392e189593025e5 || echo FAIL_P
sha256sum transformers-96331a9f.zip peft-b8674c86.zip llama.cpp-fcb3074f.tar.gz | tee $R/logs/src_sha256.txt
