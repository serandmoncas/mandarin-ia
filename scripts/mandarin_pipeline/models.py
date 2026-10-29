"""Pydantic models for generated content. Serialized as camelCase by alias."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

MissionId = Literal[
    "introductions", "restaurant", "transport", "hotel", "shopping", "directions", "emergencies"
]

MISSIONS: dict[str, str] = {
    "introductions": "Presentarse",
    "restaurant": "Restaurante",
    "transport": "Transporte",
    "hotel": "Hotel",
    "shopping": "Compras",
    "directions": "Direcciones",
    "emergencies": "Emergencias",
}


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class GeneratedExample(CamelModel):
    zh: str
    es: str


class WordContent(CamelModel):
    word: str
    cedict_reading_index: int = Field(ge=0)
    meanings_es: list[str] = Field(min_length=1, max_length=4)
    examples: list[GeneratedExample] = Field(min_length=4, max_length=4)


class Component(CamelModel):
    char: str
    meaning_es: str


class CharContent(CamelModel):
    char: str
    components: list[Component]
    mnemonic_es: str


class PhraseContent(CamelModel):
    mission: MissionId
    zh: str
    es: str


Status = Literal["generated", "auto_checked", "human_reviewed"]


class Syllable(CamelModel):
    hanzi: str
    pinyin: str  # tone-marked, e.g. "nǐ"
    tone: int = Field(ge=1, le=5)


class AudioRef(CamelModel):
    voice: str
    path: str


class Example(CamelModel):
    zh: str
    pinyin: str
    syllables: list[Syllable]
    es: str
    known_before_ratio: float
    audio: AudioRef | None = None


class ReviewResult(CamelModel):
    id: str
    ok: bool
    issues: list[str] = Field(default_factory=list)
