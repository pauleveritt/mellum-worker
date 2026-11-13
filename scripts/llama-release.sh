#!/usr/bin/env bash
# Pick and install a prebuilt llama.cpp release for Linux.
#
# Sourced by install.sh. A release binary carries its real build number (a
# shallow source clone reports "build 1", which backend.py rejects as too old)
# and ships GPU backends that need no compiler or CUDA toolkit.
#
#   LLAMA_TAG            release to install (default below; the one this was tested on)
#   MELLUM_LLAMA_FLAVOR  force a flavor: cuda-13.4, cuda-12.8, vulkan or cpu

LLAMA_TAG="${LLAMA_TAG:-b12066}"
LLAMA_HOME="${LLAMA_HOME:-$HOME/.local/share/mellum-llama}"

# The CUDA major the driver supports, from nvidia-smi's banner; empty without one.
# Older drivers print "CUDA Version: 12.4", newer ones "CUDA UMD Version: 13.4".
llama_cuda_major() {
    command -v nvidia-smi >/dev/null 2>&1 || return 0
    nvidia-smi 2>/dev/null | sed -n 's/.*CUDA[A-Z ]*Version: *\([0-9][0-9]*\).*/\1/p' | head -1
}

# True when a Vulkan loader is installed (it finds the GPU driver at run time).
llama_has_vulkan() {
    local d
    for d in /usr/lib64 /usr/lib /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu; do
        [[ -e "$d/libvulkan.so.1" ]] && return 0
    done
    command -v ldconfig >/dev/null 2>&1 && ldconfig -p 2>/dev/null | grep -q 'libvulkan\.so\.1'
}

# cuda-13.4 | cuda-12.8 | vulkan | cpu, for $1 = uname -m.
llama_flavor() {
    local arch="$1" cuda
    if [[ -n "${MELLUM_LLAMA_FLAVOR:-}" ]]; then
        echo "$MELLUM_LLAMA_FLAVOR"
        return
    fi
    cuda="$(llama_cuda_major)"
    if [[ -n "$cuda" ]] && (( cuda >= 13 )); then
        echo cuda-13.4
    elif [[ -n "$cuda" ]] && (( cuda >= 12 )) && [[ "$arch" == x86_64 ]]; then
        echo cuda-12.8
    elif llama_has_vulkan; then
        echo vulkan
    else
        echo cpu
    fi
}

# The release asset names for a flavor and arch: the main archive, then the
# CUDA runtime archive when the flavor needs one. Nothing for an unknown pair.
llama_assets() {
    local tag="$1" flavor="$2" arch="$3" a
    case "$arch" in
        x86_64) a=x64 ;;
        aarch64|arm64) a=arm64 ;;
        *) return 0 ;;
    esac
    case "$flavor" in
        cpu) echo "llama-$tag-bin-ubuntu-$a.tar.gz" ;;
        vulkan) echo "llama-$tag-bin-ubuntu-vulkan-$a.tar.gz" ;;
        cuda-12.8)
            [[ "$a" == x64 ]] || return 0
            echo "llama-$tag-bin-ubuntu-cuda-12.8-$a.tar.gz"
            echo "cudart-llama-$tag-bin-ubuntu-cuda-12.8-$a.tar.gz" ;;
        cuda-13.4)
            echo "llama-$tag-bin-ubuntu-cuda-13.4-$a.tar.gz"
            echo "cudart-llama-$tag-bin-ubuntu-cuda-13.4-$a.tar.gz" ;;
    esac
}

# Download, unpack into $LLAMA_HOME/<tag>-<flavor>, and link llama-server into
# ~/.local/bin. Returns non-zero (and leaves ~/.local/bin alone) on any failure,
# so the caller can fall back to a source build.
install_llama_release() {
    local arch flavor dest tmp asset first=""
    arch="$(uname -m)"
    flavor="$(llama_flavor "$arch")"
    mapfile -t assets < <(llama_assets "$LLAMA_TAG" "$flavor" "$arch")
    if (( ${#assets[@]} == 0 )); then
        echo "[INFO] no prebuilt llama.cpp for $arch/$flavor; building from source."
        return 1
    fi
    dest="$LLAMA_HOME/$LLAMA_TAG-$flavor"
    echo "Installing prebuilt llama.cpp $LLAMA_TAG ($flavor) into $dest..."
    tmp="$(mktemp -d)"
    for asset in "${assets[@]}"; do
        if ! curl -fL --progress-bar -o "$tmp/$asset" \
            "https://github.com/ggml-org/llama.cpp/releases/download/$LLAMA_TAG/$asset"; then
            echo "[WARN] could not download $asset."
            rm -rf -- "$tmp"
            return 1
        fi
    done
    rm -rf -- "$dest"
    mkdir -p "$dest"
    for asset in "${assets[@]}"; do
        # Every archive holds one top-level folder; its files all go side by side,
        # so llama-server finds the CUDA runtime libraries next to itself.
        tar xzf "$tmp/$asset" --strip-components=1 -C "$dest" || { rm -rf -- "$tmp"; return 1; }
    done
    rm -rf -- "$tmp"
    [[ -x "$dest/llama-server" ]] || { echo "[WARN] no llama-server in $LLAMA_TAG/$flavor."; return 1; }
    mkdir -p "$HOME/.local/bin"
    ln -sfn "$dest/llama-server" "$HOME/.local/bin/llama-server"
    hash -r
    echo "[OK] llama-server $LLAMA_TAG ($flavor) linked into ~/.local/bin."
}
