---
title: Troubleshooting
track: getting-started
prerequisites: []
authors: [Andre van Zuydam]
backends: []
---

# Troubleshooting uv and llama-server

For Windows, macOS, and Linux. These instructions use the native `llama-server` from llama.cpp and do not require Homebrew.

![A small robot with a wrench untangling a cable between a laptop and a server box](../assets/illustrations/troubleshoot.webp){ .illustration }

## 1. Identify what is failing

Open a terminal and run each command separately:

```text
uv --version
llama-server --version
```

| Result | Next step |
| --- | --- |
| Command not found or not recognized | Check installation and PATH in your operating system section. |
| A version appears | That program starts. Continue to the server checks below. |
| Missing library, DLL, or incompatible executable | See executable and library errors. |
| Server starts but the model fails | See model and memory errors. |
| Server starts but your app cannot connect | See connection checks. |

`uv` manages Python tools and environments. Native `llama-server` runs models and does not need uv to serve a model. Our shell installer uses uv to supply CMake during compilation.

Installing `llama-cpp-python[server]` provides a separate Python server. It does not install the native `llama-server` command discussed here.

## 2. Windows

### Run the batch installer

Open a terminal in the folder containing `install.bat`.

In PowerShell:

```powershell
.\install.bat
```

In Command Prompt:

```bat
install.bat
```

If Windows cannot find the script, check that its actual name is `install.bat`, rather than `install.bat.txt`. Enable file extensions in File Explorer to check.

Run from a terminal so the window stays open when an error occurs. After installation, close and reopen your terminal. If necessary, restart the application that hosts the terminal so it receives the updated PATH.

### Check where the commands are installed

In PowerShell:

```powershell
Get-Command uv -All
Get-Command llama-server -All
where.exe uv
where.exe llama-server
```

If a command works when you use its full path, its folder is missing from PATH. Add the folder containing the executable to your user's Path under **Edit environment variables for your account**, then open a new terminal. Add the folder, not the executable filename.

To run an executable in the current folder from PowerShell:

```powershell
.\llama-server.exe --version
```

For a full path containing spaces, use the call operator:

```powershell
& "C:\Tools\llama.cpp\llama-server.exe" --version
```

### WinGet is missing or installation fails

Install or update Microsoft's **App Installer** through the Microsoft Store, then open a new terminal and check:

```powershell
winget --version
```

Install missing packages:

```powershell
winget install --id astral-sh.uv --exact --source winget
winget install llama.cpp --source winget
```

If WinGet reports that a package is already installed, check PATH before reinstalling. If it lists multiple matches, use the exact package ID shown by `winget search llama.cpp`.

If WinGet is unavailable on a managed computer, use the official uv installer or release downloads and the official llama.cpp release archive. Your organisation may need to approve installation.

### Missing DLL or “This app can't run on your PC”

- Extract the whole llama.cpp release archive into one folder. Keep its supplied DLLs beside the executable.
- Match the download to your Windows architecture: x64 and ARM64 are different builds.
- For a missing Microsoft runtime, install the corresponding Microsoft Visual C++ Redistributable from Microsoft.
- For CUDA DLL errors, check the release's driver and CUDA requirements, or try a CPU build first.

Do not download individual DLL files from third-party DLL websites.

## 3. macOS and Linux: run the shell installer

From the folder containing `install.sh`, run:

```bash
bash install.sh
```

Alternatively:

```bash
chmod +x install.sh
./install.sh
```

Run it as your normal user. The script requests sudo for Linux system packages when needed.

### “set: Illegal option -o pipefail”

The script requires Bash. Running `sh install.sh` overrides its Bash shebang and can cause this error. Use `bash install.sh`.

### “Permission denied”

Use `bash install.sh`, or add executable permission with `chmod +x install.sh`. If the folder is mounted with execution disabled, move the script into a local folder where execution is allowed.

### “bad interpreter”, “bash\r”, or errors containing `$'\r'`

The file may have Windows CRLF line endings. Open it in a text editor, change its line endings to **LF**, and save it as UTF-8. Ensure `#!/usr/bin/env bash` is its first line, with no blank line or byte order mark before it.

### Check PATH

```bash
command -v uv
command -v llama-server
type -a uv
type -a llama-server
```

The supplied shell installer places both commands in `$HOME/.local/bin`. Check them directly:

```bash
"$HOME/.local/bin/uv" --version
"$HOME/.local/bin/llama-server" --version
```

If those commands work, enable that directory in the current terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

For future terminals, add that same line once to your shell configuration. Common locations are `~/.zshrc` for interactive Zsh and `~/.bashrc` for interactive Bash on Linux. Bash login shells, often used on macOS, read `~/.bash_profile`. Open a new terminal after saving.

### uv is missing

Install uv using its official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Follow the PATH instructions it prints. Here, `sh` runs uv's installer; your own `install.sh` still requires Bash.

If curl is unavailable but wget exists:

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

## 4. macOS build problems

### Missing compiler or developer tools

```bash
xcode-select --install
```

Finish Apple's installer, then rerun `bash install.sh`. Check the active developer tools with:

```bash
xcode-select -p
clang --version
```

If macOS requests acceptance of an Xcode licence or additional components, finish that setup before rebuilding.

### Apple Silicon, Intel, and Metal errors

```bash
uname -m
```

`arm64` indicates an ARM environment; `x86_64` indicates an Intel environment, which can also be a terminal running under Rosetta. Use a download and terminal environment appropriate for your Mac.

If a Metal error prevents startup, test CPU inference by adding `--n-gpu-layers 0` to the server command below. If the error persists before model loading, a CPU-only rebuild may be needed. The build option is `-DGGML_METAL=OFF`.

## 5. Linux build problems

### Missing curl, Git, make, or C/C++ compiler

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y curl ca-certificates git build-essential
```

On Fedora:

```bash
sudo dnf install -y curl ca-certificates git gcc gcc-c++ make
```

On Arch Linux, perform a normal full system update before installing prerequisites:

```bash
sudo pacman -Syu
sudo pacman -S --needed curl ca-certificates git base-devel
```

Other distributions need equivalent packages. An immutable distribution or managed system may require its own supported development environment.

### CMake is missing or too old

The supplied script obtains CMake through uv. Test that step:

```bash
uv tool run --from cmake cmake --version
```

This command needs internet access the first time. Errors mentioning Python downloads, package indexes, or certificates indicate that this step failed before llama.cpp compilation began.

### Build is killed or runs out of memory

Reduce compilation to one job:

```bash
BUILD_JOBS=1 bash install.sh
```

Check free disk space with `df -h`. The build uses your temporary directory, and source files and build files need space there.

### “GLIBC_x.y not found” or “Illegal instruction”

A downloaded executable may require a newer Linux runtime or CPU features your computer lacks. Use a compatible release or build from source on that computer. For a conservative source build, consult llama.cpp's options for disabling native CPU optimisation, starting with `-DGGML_NATIVE=OFF`.

### Missing shared libraries

Keep the libraries supplied with a prebuilt release together with its executable. Copying only the executable from a shared-library build can break it. The supplied installer requests static project libraries, but the resulting executable still depends on operating system libraries.

## 6. Test model loading and server startup

A successful installation does not include a model. Download a GGUF model supported by your llama.cpp version, and replace the example path below with its actual location.

Windows PowerShell:

```powershell
llama-server -m "C:\models\your-model.gguf" --host 127.0.0.1 --port 8000 -c 2048 --n-gpu-layers 0
```

macOS and Linux:

```bash
llama-server -m "$HOME/models/your-model.gguf" --host 127.0.0.1 --port 8000 -c 2048 --n-gpu-layers 0
```

This starts a local CPU test with a limited context size. Leave the terminal open while the server runs. Press **Ctrl+C** to stop it. Once the CPU test works, remove `--n-gpu-layers 0` to test the acceleration available in your build.

### Model file errors

- **File not found:** Check the path, spelling, and file permissions. Quote paths containing spaces.
- **Invalid GGUF or unexpected end of file:** Check that the download completed and contains model data rather than an HTML error page. Verify the publisher's checksum if available.
- **Unsupported architecture or tensor type:** Update llama.cpp or choose a model supported by your installed version.
- **Split model:** Download every required shard and follow the model publisher's loading instructions.
- **Out of memory:** Choose a smaller model or quantisation, reduce context size, and close other memory-intensive applications. CPU mode still needs enough system RAM.

## 7. Test the connection

After the server finishes loading, use a second terminal.

Windows PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/v1/models
```

macOS and Linux:

```bash
curl -i http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/models
```

| Symptom | What to check |
| --- | --- |
| Connection refused | Confirm the server is still running and listening on port 8000. Read its startup error. |
| Health endpoint returns 503 | The model may still be loading. Check progress in the server terminal. |
| Address already in use | Choose another port, such as `--port 8001`, and update your client URL. |
| 401 response | If API-key authentication is enabled, configure the client with the same key. |
| 404 response | Check the endpoint. An OpenAI-compatible client usually needs a base URL ending in `/v1`. |
| Browser works but your app fails | Check the app's base URL, model ID, authentication, and any tool-calling requirements. |

For a client running on this same computer, the base URL in this example is `http://127.0.0.1:8000/v1`. Use a model ID returned by `/v1/models` if the client requires one.

Inside WSL, Docker, or another machine, `127.0.0.1` can refer to a different environment. Check the appropriate host address, port forwarding, server binding, and firewall rules. Binding to `127.0.0.1` keeps this test local; do not change firewall settings to fix a server that has failed to start.

## 8. Download, proxy, and permission errors

- Confirm the computer can reach `astral.sh`, GitHub, and any Python package index or model host used by the failing step.
- On a managed network, use the approved proxy and certificate configuration. Do not disable certificate verification to bypass TLS errors.
- If GitHub reports a rate limit or a download fails partway through, wait and retry the failed download.
- If installation reports permission denied, confirm that your user owns the destination folder. Avoid running the whole macOS/Linux installer with sudo, which can install tools under the wrong account.
- If security software quarantines a release file, review its report and verify the official download source before taking action.

## 9. Collect useful information for support

Include your operating system and version, CPU architecture, RAM, GPU and driver version if relevant, installation method, and the exact command that failed. Copy the first meaningful error and the lines around it.

Windows PowerShell:

```powershell
uv --version
llama-server --version
Get-Command uv -All
Get-Command llama-server -All
```

macOS and Linux:

```bash
uname -srm
uv --version
llama-server --version
command -v uv
command -v llama-server
```

To capture installer output on macOS or Linux:

```bash
bash install.sh > install.log 2>&1
```

To capture it from Windows Command Prompt:

```bat
install.bat > install.log 2>&1
```

Remove API keys, tokens, and private information before sharing logs. If you need to confirm that a failing script produces a nonzero exit code, run it without a logging pipeline; a pipeline can otherwise report the logging tool's status.

## Official references

- [uv installation and installer options](https://docs.astral.sh/uv/getting-started/installation/)
- [llama.cpp installation methods](https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md)
- [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases)
- [llama.cpp source build instructions](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [llama-server options and HTTP endpoints](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- [Microsoft App Installer and WinGet](https://learn.microsoft.com/windows/package-manager/winget/)
- [Microsoft Visual C++ Redistributable downloads](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist)
