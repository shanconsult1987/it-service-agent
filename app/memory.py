from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

MEMORY_FILE = ROOT / "data" / "agent_memory.md"


def load_memory():

    return MEMORY_FILE.read_text(
        encoding="utf-8"
    )


def append_memory(
    section,
    content
):

    current = load_memory()

    marker = f"## {section}"

    if marker not in current:

        current += (
            f"\n\n{marker}\n"
            f"{content}\n"
        )

    else:

        before, after = current.split(
            marker,
            1
        )

        current = (
            before
            + marker
            + "\n"
            + content
            + "\n"
            + after
        )

    MEMORY_FILE.write_text(
        current,
        encoding="utf-8"
    )

    return load_memory()