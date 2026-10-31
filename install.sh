#!/usr/bin/env bash
set -euo pipefail

trap 'echo "[ERROR] Installation failed at line $LINENO." >&2' ERR

OS="$(uname -s)"
case "$OS" in
    Darwin|Linux) ;;
    *)
        echo "[ERROR] Only macOS and Linux are supported." >&2
        exit 1
        ;;
esac

# Also find tools installed during a previous run.
export PATH="$HOME/.local/bin:$PATH"

# This script lives at the repo root; the start prompts below run from the repo.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

has() {
    command -v "$1" >/dev/null 2>&1
}

# llama.cpp learned Mellum's architecture in build 9482.
MIN_BUILD=9482

# Newer builds print "version: 0.7.0-dev (build 11829, ...)",
# older ones "version: 7360 (...)". Prints nothing if neither matches.
build_of() {
    local out
    out="$("$1" --version 2>&1 || true)"
    if [[ "$out" =~ \(build\ ([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    elif [[ "$out" =~ version:\ ([0-9]+)\ \( ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

# Every llama-server on PATH must be new enough, or an old one that comes
# first wins and cannot load Mellum. Homebrew's copy is upgraded, ours in
# ~/.local/bin is rebuilt, and any other old copy is renamed to .old once a
# current build is installed.
build_llama=false
retire=()
if ! has llama-server; then
    build_llama=true
else
    echo "llama-server on PATH, in the order the shell tries them:"
    have_good=false
    brew_old=false
    while IFS= read -r path; do
        build="$(build_of "$path")"
        if [[ -z "$build" ]]; then
            echo "  $path  [build unknown]"
        elif (( build >= MIN_BUILD )); then
            echo "  $path  [build $build, OK]"
            have_good=true
        else
            echo "  $path  [build $build, too old]"
            if has brew && [[ "$path" == "$(brew --prefix)"/* ]]; then
                brew_old=true
            elif [[ "$path" == "$HOME/.local/bin/llama-server" ]]; then
                build_llama=true
            else
                retire+=("$path")
            fi
        fi
    done < <(type -ap llama-server | awk '!seen[$0]++')

    if [[ "$brew_old" == true ]]; then
        echo "Upgrading llama.cpp with Homebrew..."
        brew upgrade llama.cpp
        hash -r
        have_good=true
    fi
    # Old copies to rename need a current build to take their place.
    if (( ${#retire[@]} > 0 )) && [[ "$have_good" == false ]]; then
        build_llama=true
    fi
fi

# Rename each old llama-server so it stops shadowing the current one.
retire_old() {
    local path ok=true
    for path in ${retire[@]+"${retire[@]}"}; do
        if mv "$path" "$path.old" 2>/dev/null; then
            echo "[FIXED] Renamed $path to $(basename "$path").old (too old for Mellum)."
            echo "        Undo: mv \"$path.old\" \"$path\""
        else
            echo "[ERROR] Could not rename $path; it may need: sudo mv \"$path\" \"$path.old\""
            ok=false
        fi
    done
    hash -r
    [[ "$ok" == true ]]
}

# This repo and Pi need Node.js 24 or newer; npm comes with it.
MIN_NODE=24
NODE_DIR="$HOME/.local/share/mellum-node"
PI_PACKAGE="@earendil-works/pi-coding-agent"
PI_VERSION="1.4.0"   # the Pi version the course ships and develops against

node_major() {
    local version
    version="$(node --version 2>/dev/null || true)"
    version="${version#v}"
    echo "${version%%.*}"
}

# A missing or old Node.js gets a private LTS in ~/.local, fetched by uv's
# nodeenv: no sudo, no Homebrew, no shell configuration to edit.
ensure_node() {
    if has node && [[ "$(node_major)" -ge "$MIN_NODE" ]]; then
        echo "[OK] Node.js $(node_major) is new enough."
        return 0
    fi
    if has node; then
        echo "[OLD] Node.js $(node_major) at $(command -v node) is too old;"
        echo "this repo and Pi need $MIN_NODE or newer."
    fi
    echo "Installing a private Node.js LTS into $NODE_DIR..."
    rm -rf -- "$NODE_DIR"
    uv tool run nodeenv --prebuilt --node=lts "$NODE_DIR"
    mkdir -p "$HOME/.local/bin"
    for tool in node npm npx; do
        ln -sf "$NODE_DIR/bin/$tool" "$HOME/.local/bin/$tool"
    done
    hash -r
    if [[ "$(node_major)" -lt "$MIN_NODE" ]]; then
        echo "[ERROR] Node.js is still older than $MIN_NODE: $(command -v node)."
        return 1
    fi
    echo "[OK] Node.js $(node_major) installed."
}

# Pi is an npm package. --prefix puts it in ~/.local/bin, so it never needs sudo.
pi_version() { pi --version 2>/dev/null | tr -d '[:space:]'; }

# Pi must be the pinned version this repo is measured against, not just any pi.
ensure_pi() {
    if has pi && [[ "$(pi_version)" == "$PI_VERSION" ]]; then
        echo "[OK] pi $PI_VERSION already installed."
        return 0
    fi
    if has pi; then
        echo "[CHANGE] pi $(pi_version) is not the pinned $PI_VERSION; installing $PI_VERSION."
    fi
    echo "Installing $PI_PACKAGE@$PI_VERSION..."
    npm install -g --prefix "$HOME/.local" "$PI_PACKAGE@$PI_VERSION"
    hash -r
    has pi || { echo "[ERROR] pi installation failed."; return 1; }
    [[ "$(pi_version)" == "$PI_VERSION" ]] || echo "[WARN] pi reports $(pi_version), expected $PI_VERSION."
}

# Give base Pi the mellum-worker harness (/mellum, worker prompt, guards) from
# this clone, so the Pi the learner runs is the worker, not bare Pi.
ensure_harness() {
    if pi list 2>/dev/null | grep -q "mellum-worker"; then
        echo "[OK] mellum-worker harness already installed in Pi."
        return 0
    fi
    echo "Installing the mellum-worker harness into Pi (from this clone)..."
    pi install "$REPO_DIR" \
        || echo "[WARN] harness install failed; run it yourself: pi install \"$REPO_DIR\""
}

# Once the tools are in, hand off to run.sh — the recurring entry point that
# starts the server (first run downloads the model) and Pi.
offer_start() {
    echo
    echo "Next: start the model and Pi with  bash ./run.sh"
    [[ -t 0 ]] || return 0
    local ans
    read -r -p "Start now? [Y/n] " ans || ans=""
    [[ "$ans" =~ ^[Nn] ]] || exec "$REPO_DIR/run.sh"
}

if has uv && [[ "$build_llama" == false ]]; then
    retire_old
    echo "[OK] uv and llama-server already exist."
    ensure_node
    ensure_pi
    ensure_harness
    echo
    llama-server --version
    node --version
    pi --version
    offer_start
    exit 0
fi

# Install prerequisites only if needed.
need_deps=false
has curl || need_deps=true

if [[ "$build_llama" == true ]]; then
    for tool in git make cc c++; do
        has "$tool" || need_deps=true
    done
fi

if [[ "$need_deps" == true ]]; then
    if [[ "$OS" == Darwin ]]; then
        if ! xcode-select -p >/dev/null 2>&1; then
            xcode-select --install
            echo "Finish installing Apple's Command Line Tools, then rerun."
            exit 1
        fi
    else
        SUDO=()
        if [[ "$(id -u)" -ne 0 ]]; then
            if ! has sudo; then
                echo "[ERROR] sudo is required to install build prerequisites."
                exit 1
            fi
            SUDO=(sudo)
        fi

        if has apt-get; then
            "${SUDO[@]}" apt-get update
            "${SUDO[@]}" apt-get install -y \
                curl ca-certificates git build-essential
        elif has dnf; then
            "${SUDO[@]}" dnf install -y \
                curl ca-certificates git gcc gcc-c++ make
        elif has pacman; then
            "${SUDO[@]}" pacman -S --needed --noconfirm \
                curl ca-certificates git base-devel
        else
            echo "[ERROR] Install curl, git, make, and a C/C++ compiler,"
            echo "then rerun this script."
            exit 1
        fi
    fi
fi

# Create a private workspace for downloads and compilation.
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT

if has uv; then
    echo "[OK] uv already exists."
else
    echo "Installing uv..."
    curl -fsSL https://astral.sh/uv/install.sh \
        -o "$work_dir/install-uv.sh"

    UV_INSTALL_DIR="$HOME/.local/bin" sh "$work_dir/install-uv.sh"
    hash -r
    has uv || { echo "[ERROR] uv installation failed."; exit 1; }
fi

if [[ "$build_llama" == false ]]; then
    echo "[OK] llama-server already exists."
else
    for tool in git make cc c++; do
        has "$tool" || {
            echo "[ERROR] Missing build prerequisite: $tool"
            exit 1
        }
    done

    echo "Downloading llama.cpp..."
    git clone --depth 1 https://github.com/ggml-org/llama.cpp.git \
        "$work_dir/llama.cpp"

    # uv supplies CMake without a system-wide installation.
    # Static project libraries let us install the server as one executable.
    echo "Configuring llama-server..."
    uv tool run --from cmake cmake \
        -S "$work_dir/llama.cpp" \
        -B "$work_dir/build" \
        -G "Unix Makefiles" \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=OFF \
        -DLLAMA_BUILD_TESTS=OFF \
        -DLLAMA_BUILD_SERVER=ON

    echo "Building llama-server..."
    uv tool run --from cmake cmake \
        --build "$work_dir/build" \
        --target llama-server \
        --parallel "${BUILD_JOBS:-2}"

    mkdir -p "$HOME/.local/bin"
    install -m 755 "$work_dir/build/bin/llama-server" \
        "$HOME/.local/bin/llama-server"
    hash -r
fi

retire_old
ensure_node
ensure_pi
ensure_harness

echo
uv --version
llama-server --version
node --version
pi --version
echo
echo "Installation complete."
echo 'For future terminals, ensure this is in your shell configuration:'
echo 'export PATH="$HOME/.local/bin:$PATH"'
offer_start