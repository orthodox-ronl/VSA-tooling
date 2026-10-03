from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any


@dataclass
class TextNode:
    text: str
    start: Optional[int] = None
    end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "TextNode",
            "text": self.text,
        }


@dataclass
class ScopeNode:
    height_modifier: List[str]
    text: str
    length_modifier: List[str]
    start: Optional[int] = None
    end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ScopeNode",
            "height_modifier": self.height_modifier,
            "text": self.text,
            "length_modifier": self.length_modifier,
        }


@dataclass
class PitchMarkerNode:
    height_modifier: Optional[List[str]] = None
    start: Optional[int] = None
    end: Optional[int] = None

    @property
    def ehm(self) -> List[str]:
        return self.height_modifier or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PitchMarkerNode",
            "height_modifier": self.height_modifier or [],
        }


HeightMarkerNode = PitchMarkerNode


@dataclass
class PitchTransitionNode:
    """Stille toonhoogte-overgang ``[<oude-EHM>:<nieuwe-EHM>]`` (niet renderen)."""

    from_height_modifier: Optional[List[str]] = None
    to_height_modifier: Optional[List[str]] = None
    start: Optional[int] = None
    end: Optional[int] = None

    @property
    def from_ehm(self) -> List[str]:
        return self.from_height_modifier or []

    @property
    def to_ehm(self) -> List[str]:
        return self.to_height_modifier or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PitchTransitionNode",
            "from_height_modifier": self.from_height_modifier or [],
            "to_height_modifier": self.to_height_modifier or [],
        }


@dataclass
class ControlTokenNode:
    token: str
    meaning: str
    start: Optional[int] = None
    end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ControlTokenNode",
            "token": self.token,
            "meaning": self.meaning,
        }


Node = Union[
    TextNode,
    ScopeNode,
    PitchMarkerNode,
    PitchTransitionNode,
    ControlTokenNode,
]


@dataclass
class Document:
    nodes: List[Node] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Document",
            "nodes": [node.to_dict() for node in self.nodes],
        }
