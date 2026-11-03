#!/usr/bin/env bash
set -euo pipefail
until ! tmux has-session -t mellum-build 2>/dev/null; do sleep 2; done
test -f /workspace/mellum/qualification/build-ok
rm /workspace/mellum/qualification/build-ok
export PATH=/usr/local/cuda/bin:$PATH
cd /tmp/mellum-llama
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120 -DGGML_NATIVE=OFF '-DCMAKE_BUILD_RPATH=$ORIGIN' -DLLAMA_BUILD_NUMBER=11669 -DLLAMA_BUILD_COMMIT=620d2225c -DLLAMA_BUILD_IS_DEV=OFF
cmake --build build --target llama-server -j 8
cp -a build/bin/. /workspace/mellum/llama.cpp/build/bin/
cp build/CMakeCache.txt /workspace/mellum/qualification/CMakeCache.txt
/workspace/mellum/llama.cpp/build/bin/llama-server --version > /workspace/mellum/qualification/server-version.txt 2>&1
sha256sum /workspace/mellum/llama.cpp/build/bin/* > /workspace/mellum/qualification/binaries.sha256
ldd /workspace/mellum/llama.cpp/build/bin/llama-server > /workspace/mellum/qualification/ldd.txt
touch /workspace/mellum/qualification/build-ok
tmux new-session -d -s mellum-server 'bash /workspace/mellum/serve.sh > /workspace/mellum/server.log 2>&1'
