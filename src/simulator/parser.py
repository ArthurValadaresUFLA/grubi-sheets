from __future__ import annotations

import re
from pathlib import Path


class DataEngine:
    @classmethod
    def load_patterns(cls, path: Path) -> dict[str, re.Pattern]:
        patterns = {}
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    name, pat = line.split("=", 1)
                    pat = pat.strip().strip('"').strip("'")
                    patterns[name.strip()] = re.compile(pat)
        return patterns

    @classmethod
    def parse_log(cls, text_blob: str, sim_id: int, patterns: dict[str, re.Pattern]) -> list[dict]:
        events = []
        # Mantém um estado para cruzar dados de múltiplas linhas do log (ex: propagar um send_id)
        state = {"simulation": sim_id}

        for line in text_blob.splitlines():
            matched = False
            current_match = {}

            for pat in patterns.values():
                match = pat.search(line)
                if match:
                    matched = True
                    for k, v in match.groupdict().items():
                        if v is not None:
                            try:
                                if "." in v:
                                    current_match[k] = float(v)
                                else:
                                    current_match[k] = int(v)
                            except ValueError:
                                current_match[k] = v

            if matched:
                state.update(current_match)
                # Salva o estado atual como uma nova linha
                events.append(state.copy())

        return events