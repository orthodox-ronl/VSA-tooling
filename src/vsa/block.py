from dataclasses import dataclass, field
from typing import Dict, List

from .parser import Parser


DEFAULT_METADATA = {
    "do": "F4",
    "mode": "major",
    "tempo": "120",
    "validate-ending": "true",
    "duration-model": "default",
}


@dataclass
class VSABlock:
    metadata: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    start_line: int = 1
    end_line: int = 1

    def effective_metadata(self) -> Dict[str, str]:
        result = dict(DEFAULT_METADATA)
        result.update(self.metadata)
        return result

    def parse_body(self):
        return Parser(self.body).parse()
