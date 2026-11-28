"""Mark the tool-call markers as USER_DEFINED tokens in a converted GGUF, in place.

convert_hf_to_gguf.py types any token shaped like `<｜...｜>` as CONTROL, whatever the tokenizer says. llama-server
leaves CONTROL tokens out of the text its tool-call parser reads, so a call arrives as `functionbash` with
`<｜tool▁sep｜>` gone and the request fails. USER_DEFINED tokens (like `<think>`) are kept as text.

    uv run --with numpy --with pyyaml python r1d/gguf_markers.py MODEL.gguf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".cache/mellum-llamacpp-cd959bae9/gguf-py"))
sys.path.insert(0, str(Path(__file__).parent))


def plain_markers(path, markers):
    """Set each token in `markers` to USER_DEFINED; return {marker: id}. KeyError if one is not in the vocabulary."""
    import gguf
    r = gguf.GGUFReader(str(path), "r+")
    toks, types = r.fields["tokenizer.ggml.tokens"], r.fields["tokenizer.ggml.token_type"]
    ids = {bytes(toks.parts[i]).decode(): n for n, i in enumerate(toks.data)}
    changed = {m: ids[m] for m in markers}
    for tid in changed.values():
        types.parts[types.data[tid]][0] = gguf.TokenType.USER_DEFINED
    r.data.flush()
    return changed


if __name__ == "__main__":
    from add_tokens import TOOL_TOKENS
    print(plain_markers(sys.argv[1], TOOL_TOKENS))
