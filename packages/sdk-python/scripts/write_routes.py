"""Writes ``src/tracetus/routes.py`` from the OpenAPI document.

The method of a request decides what a failed answer means: a read that failed
changed nothing, while a write answered `500` may have written. The generated
package knows the method of every operation, but it keeps it inside a private
function, so this writes the one table the hand-written half needs — the same
shape the JavaScript client generates for the same reason.

Run by ``scripts/generate.sh``; the CI job regenerates and diffs it.
"""

from __future__ import annotations

import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DOCUMENT = HERE.parent.parent.parent / "apps" / "api" / "openapi.json"
TARGET = HERE.parent / "src" / "tracetus" / "routes.py"

HEADER = '''"""The method of every operation, generated from the OpenAPI document.

Do not edit: ``scripts/generate.sh`` writes this file, and CI diffs it against
a fresh generation. The key is the module the generated package puts the
operation in, which is its ``operationId`` with the dot replaced.
"""

from __future__ import annotations

from collections.abc import Mapping

OPERATION_METHODS: Mapping[str, str] = {
'''

FOOTER = """}


def method_of(module_name: str) -> str:
    \"\"\"The method of an operation module, or an empty string when unknown.

    Unknown counts as unsafe wherever this is read: it is the answer that keeps
    a caller from issuing twice.
    \"\"\"
    return OPERATION_METHODS.get(module_name.rsplit(".", 1)[-1], "")
"""


def module_name_of(operation_id: str) -> str:
    """``records.createBatch`` becomes ``records_create_batch``.

    The same name the generator derives for the operation's module: the dot
    becomes an underscore and each camel hump becomes one too.
    """
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", operation_id.replace(".", "_"))

    return snake.lower()


def main() -> None:
    document = json.loads(DOCUMENT.read_text(encoding="utf-8"))
    rows = []

    for path, operations in sorted(document["paths"].items()):
        for method, operation in sorted(operations.items()):
            operation_id = operation.get("operationId")

            if isinstance(operation_id, str):
                rows.append((module_name_of(operation_id), method.upper(), path))

    lines = [f'    "{name}": "{method}",  # {path}\n' for name, method, path in sorted(rows)]

    TARGET.write_text(HEADER + "".join(lines) + FOOTER, encoding="utf-8")
    print(f"wrote {TARGET.relative_to(HERE.parent)} with {len(rows)} operations")


if __name__ == "__main__":
    main()
