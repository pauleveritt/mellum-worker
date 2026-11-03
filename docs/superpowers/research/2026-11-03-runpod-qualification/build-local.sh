#!/usr/bin/env bash
set -euo pipefail
export PATH=/usr/local/cuda/bin:$PATH
git clone --no-hardlinks /workspace/mellum/llama.cpp /tmp/mellum-llama
cd /tmp/mellum-llama
test "$(git rev-parse HEAD)" = 620d2225cc436ab0b001e3200e590e3b286ef9ab
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120 -DGGML_NATIVE=OFF '-DCMAKE_BUILD_RPATH=$ORIGIN'
cmake --build build --target llama-server -j 8
mkdir -p /workspace/mellum/llama.cpp/build/bin
cp -a build/bin/. /workspace/mellum/llama.cpp/build/bin/
cp build/CMakeCache.txt /workspace/mellum/qualification/CMakeCache.txt
/workspace/mellum/llama.cpp/build/bin/llama-server --version
ldd /workspace/mellum/llama.cpp/build/bin/llama-server > /workspace/mellum/qualification/ldd.txt
sha256sum /workspace/mellum/llama.cpp/build/bin/* > /workspace/mellum/qualification/binaries.sha256
touch /workspace/mellum/qualification/build-ok
