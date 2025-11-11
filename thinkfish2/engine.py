from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import chess
import chess.engine

from .types import EngineInfo, EvalResult, EvalScore


@dataclass
class EngineConfig:
    threads: int = int(os.getenv("THINKFISH2_THREADS", "1"))
    hash_mb: int = int(os.getenv("THINKFISH2_HASH_MB", "128"))
    min_depth: int = int(os.getenv("THINKFISH2_MIN_DEPTH", "12"))
    skill: int = int(os.getenv("THINKFISH2_SKILL", "20"))
    contempt: int = 0


class StockfishEngine:
    def __init__(self, engine_path: Optional[str] = None, config: Optional[EngineConfig] = None):
        self.engine_path = engine_path or os.getenv("STOCKFISH_PATH", "stockfish")
        self.config = config or EngineConfig()
        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._engine_info: EngineInfo = {}

    def start(self):
        if self._engine is not None:
            return
        self._engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        # Apply options
        try:
            self._engine.configure(
                {
                    "Threads": self.config.threads,
                    "Hash": self.config.hash_mb,
                    "Skill Level": self.config.skill,
                    # Some engines support "Contempt"; ignore if not supported
                }
            )
        except chess.engine.EngineError:
            pass
        # Version info (best-effort; ignore failures and avoid unused vars)
        try:
            if hasattr(self._engine.protocol, "version_info"):
                _ = self._engine.protocol.version_info()
        except Exception:
            pass
        self._engine_info = {
            "name": getattr(self._engine, "id", {}).get("name", "Stockfish"),
            "version": getattr(self._engine, "id", {}).get("version", ""),
            "options": {
                "Threads": self.config.threads,
                "Hash": self.config.hash_mb,
                "Skill": self.config.skill,
            },
        }

    def stop(self):
        if self._engine is not None:
            try:
                self._engine.quit()
            finally:
                self._engine = None

    def info(self) -> EngineInfo:
        return self._engine_info

    def evaluate(self, fen: str, depth: int, multipv: int = 1) -> EvalResult:
        if self._engine is None:
            self.start()
        assert self._engine is not None

        board = chess.Board(fen)
        limit = chess.engine.Limit(depth=max(depth, self.config.min_depth))
        with self._engine.analysis(board, limit, multipv=multipv) as analysis:
            best_pv = []
            best_score: Optional[chess.engine.PovScore] = None
            for info in analysis:
                if info.get("pv"):
                    pv_moves = [m.uci() for m in info["pv"]]
                    score = info.get("score")
                    if score is not None:
                        best_score = score
                        best_pv = pv_moves
            # Fallback using a single go if analysis loop yields nothing
            if not best_pv:
                result = self._engine.play(board, limit)
                best_pv = [result.move.uci()] if result.move else []
                best_score = None

        eval_score: EvalScore
        if best_score is None:
            # Unknown score; return neutral
            eval_score = {"type": "cp", "value": 0}
        else:
            pov = best_score.pov(board.turn)
            if pov.is_mate():
                eval_score = {"type": "mate", "value": pov.mate() or 0}
            else:
                eval_score = {"type": "cp", "value": pov.score() or 0}

        bestmove = best_pv[0] if best_pv else None
        return {
            "score": eval_score,
            "bestmove": bestmove,
            "pv": best_pv,
            "depth": depth,
            "engine": self.info(),
        }
