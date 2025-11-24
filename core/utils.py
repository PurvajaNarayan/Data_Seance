
import matplotlib.pyplot as plt

def load_and_show_png_bytes(img_bytes: bytes, title: str | None = None):
    """
    Loader function: read PNG bytes and plot them with matplotlib.
    """
    from io import BytesIO
    import matplotlib.image as mpimg

    arr = mpimg.imread(BytesIO(img_bytes), format="png")
    plt.figure()
    plt.imshow(arr)
    plt.axis("off")
    if title:
        plt.title(title)
    plt.show()

from typing import Sequence, Any
from pprint import pformat
from langchain_core.messages import BaseMessage


# ---------- helpers ----------

def _is_probably_binary_string(s: str) -> bool:
    """Heuristic to avoid dumping base64/data URLs and other non-human strings."""
    if not isinstance(s, str):
        return False

    if s.startswith("data:image") or "base64," in s[:80]:
        return True

    if len(s) > 256:
        base64_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r "
        )
        if set(s[:1024]) <= base64_chars:
            return True

    non_printable = sum((ord(c) < 32 or ord(c) > 126) for c in s)
    if len(s) == 0:
        return False
    return (non_printable / len(s)) > 0.30


def _indent_preserve(text: str, indent: int) -> str:
    """Indent every line of `text` by `indent` spaces, preserving internal formatting."""
    prefix = " " * indent
    return "".join(prefix + line for line in text.splitlines(keepends=True))


def _sanitize_for_print(obj: Any, max_list_items: int = 8) -> Any:
    """
    Prepare an object for pretty-printing inside dicts:

    - binary-ish strings / bytes -> "[binary data omitted]"
    - long lists -> truncated list + note element
    """
    if isinstance(obj, (bytes, bytearray)):
        return "[binary data omitted]"

    if isinstance(obj, str):
        if _is_probably_binary_string(obj):
            return "[binary data omitted]"
        return obj

    if isinstance(obj, dict):
        return {k: _sanitize_for_print(v, max_list_items) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        total = len(obj)
        show_n = min(total, max_list_items)
        items = [_sanitize_for_print(x, max_list_items) for x in obj[:show_n]]
        if total > show_n:
            items.append(
                f"... (list truncated, has {total} elements; showing first {show_n})"
            )
        return items if isinstance(obj, list) else tuple(items)

    return obj


# ---------- object → human string ----------

def _humanize_obj(
    obj: Any,
    indent: int = 0,
    max_list_items: int = 8,
) -> str:
    """
    Convert arbitrary object to a human-readable multi-line string.

    IMPORTANT: strings are *never* re-wrapped or reformatted;
    their internal newlines/spacing are preserved.
    """
    lines: list[str] = []
    prefix = " " * indent

    # None
    if obj is None:
        lines.append(prefix + "null")

    # Strings (preserve formatting)
    elif isinstance(obj, str):
        if _is_probably_binary_string(obj):
            lines.append(prefix + "[binary data omitted]")
        else:
            lines.append(_indent_preserve(obj, indent))

    # Simple scalars
    elif isinstance(obj, (int, float, bool)):
        lines.append(prefix + repr(obj))

    # Dicts: recursively pretty-print as a dict literal
    elif isinstance(obj, dict):
        sanitized = _sanitize_for_print(obj, max_list_items=max_list_items)
        pretty = pformat(sanitized, width=80, compact=False)
        lines.append(_indent_preserve(pretty, indent))

    # Lists / tuples: each element as its own block, with truncation
    elif isinstance(obj, (list, tuple)):
        total = len(obj)
        if total == 0:
            lines.append(prefix + "[]")
        else:
            show_n = min(total, max_list_items)
            for i, item in enumerate(obj[:show_n], 1):
                lines.append(
                    _humanize_obj(
                        item,
                        indent=indent,
                        max_list_items=max_list_items,
                    )
                )
                if i != show_n:
                    lines.append("")  # blank line between elements

            if total > show_n:
                lines.append(
                    f"{prefix}(list truncated, has {total} elements; "
                    f"showing first {show_n})"
                )

    # Fallback: pretty repr
    else:
        pretty = pformat(obj, width=80, compact=True)
        lines.append(_indent_preserve(pretty, indent))

    return "\n".join(lines)


def _render_content(content: Any) -> str:
    """
    Render the .content attribute of a message.
    - Plain string: returned exactly as-is.
    - List: each element pretty-printed as its own block.
    - Dict / other: pretty-printed generically.
    """
    if content is None:
        return "content: null"

    # Plain text: show exactly as stored
    if isinstance(content, str):
        return _indent_preserve(content, 2)

    # List-of-blocks content
    if isinstance(content, list):
        blocks: list[str] = []
        for idx, block in enumerate(content, 1):
            blocks.append(f"- item {idx}:")
            blocks.append(_humanize_obj(block, indent=4))
            blocks.append("")
        return "\n".join("  " + line if line else "" for line in blocks)

    # Anything else
    return  _humanize_obj(content, indent=2)


# ---------- public API ----------

def pretty_messages_pretty(
    messages: Sequence[BaseMessage],
    max_list_items: int = 8,
) -> str:
    """
    Pretty-print LangChain Messages.

    - **Preserves** the original first line from `pretty_repr()` (the
      `==================== Human Message ====================` header).
    - Replaces the rest with a more readable view of `.content`:
        * strings unchanged,
        * dicts recursively pretty-printed,
        * lists printed element-by-element with truncation note,
        * binary-ish data omitted.
    """
    out: list[str] = []

    for msg in messages:
        # Grab original pretty_repr and keep the header line AS-IS
        if hasattr(msg, "pretty_repr") and callable(getattr(msg, "pretty_repr")):
            try:
                base = msg.pretty_repr()
            except TypeError:
                base = msg.pretty_repr(html=False)
        else:
            base = repr(msg)

        lines = base.splitlines() or [repr(msg)]
        header_line = lines[0]  # e.g. "====================  Human Message  ===================="

        out.append(header_line)      # keep exactly
        out.append("")               # blank line after header
        out.append(_render_content(getattr(msg, "content", None)))
        out.append("")               # blank line between messages

    return "\n".join(out)
