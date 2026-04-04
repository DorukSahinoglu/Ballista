from __future__ import annotations

import json
from pathlib import Path

from ballista import build_editor_contract, load_algorithm_definition_file
from ballista.examples import build_builtin_registry


def main() -> None:
    definition_path = Path(__file__).with_name("labeled_matrix_definition.json")
    registry = build_builtin_registry()
    loaded = load_algorithm_definition_file(definition_path, registry)
    contract = build_editor_contract(registry, loaded.slot_schema)

    print(json.dumps(contract, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
