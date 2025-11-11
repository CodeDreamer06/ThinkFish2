from typing import List, Literal, Optional, TypedDict

ScoreType = Literal["cp", "mate"]


class EngineInfo(TypedDict, total=False):
    name: str
    version: str
    options: dict


class EvalScore(TypedDict):
    type: ScoreType  # "cp" or "mate"
    value: int  # centipawns or ply to mate


class EvalResult(TypedDict):
    score: EvalScore
    bestmove: Optional[str]
    pv: List[str]
    depth: int
    engine: EngineInfo


class EvaluateInput(TypedDict, total=False):
    fen: str
    depth: int
    multipv: int


class GenerateMovesInput(TypedDict):
    fen: str


class GenerateMovesResult(TypedDict):
    legal_moves_uci: List[str]


class ConvertUciToSanInput(TypedDict):
    fen: str
    uci_moves: List[str]


class ConvertSanToUciInput(TypedDict):
    fen: str
    san_moves: List[str]


class PGNLoadInput(TypedDict):
    pgn: str


class PGNLoadResult(TypedDict):
    moves_uci: List[str]
    initial_fen: str


class ReviewResult(TypedDict):
    summary: str
    key_moments: List[str]
    side: Optional[Literal["white", "black", "overall"]]
