from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import chess
import chess.pgn

from .engine import StockfishEngine
from .llm import chat_completion
from .types import ReviewResult


@dataclass
class ReviewConfig:
    depth: int = 12
    blunder_threshold_cp: int = 150  # centipawn loss threshold


def _iterate_game(fen: str, moves: List[chess.Move]) -> List[Tuple[str, str]]:
    """Return list of (fen_before, fen_after) for each move."""
    board = chess.Board(fen)
    pairs: List[Tuple[str, str]] = []
    for m in moves:
        before = board.fen()
        board.push(m)
        after = board.fen()
        pairs.append((before, after))
    return pairs


def _centipawn(score: chess.engine.PovScore, turn_white: bool) -> int:
    pov = score.pov(turn_white)
    if pov.is_mate():
        # Convert mate to large centipawn proxy retaining sign
        mate_val = pov.mate() or 0
        return 100000 if mate_val > 0 else -100000 if mate_val < 0 else 0
    return pov.score() or 0


def analyze_pgn(
    pgn_text: str, cfg: Optional[ReviewConfig] = None, engine: Optional[StockfishEngine] = None
) -> Dict[str, Any]:
    cfg = cfg or ReviewConfig()
    engine = engine or StockfishEngine()
    engine.start()

    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        return {
            "initial_fen": chess.STARTING_FEN,
            "moves": [],
            "moments": [],
        }

    initial_fen = game.headers.get("FEN", chess.STARTING_FEN)
    board = chess.Board(initial_fen)
    moves = list(game.mainline_moves())

    moments: List[Dict[str, Any]] = []

    for ply_index, move in enumerate(moves):
        side_white = board.turn  # side to move before applying 'move'

        # Evaluate current position
        eva_before = engine.evaluate(board.fen(), depth=cfg.depth)
        cp_before = eva_before["score"]["value"] if eva_before["score"]["type"] == "cp" else 0

        # If engine best move differs, estimate loss after applying played move
        board.push(move)
        eva_after = engine.evaluate(board.fen(), depth=cfg.depth)
        cp_after = eva_after["score"]["value"] if eva_after["score"]["type"] == "cp" else 0

        # Centipawn perspective: positive means advantage to side to move before
        # Loss for the moving side is (cp_before - cp_after) if same perspective
        loss_cp = cp_before - cp_after if side_white else -(cp_before - cp_after)

        if abs(loss_cp) >= cfg.blunder_threshold_cp:
            uci = move.uci()
            san = chess.Board(initial_fen).san(move) if False else None  # avoid recomputation
            moments.append(
                {
                    "ply": ply_index + 1,
                    "side": "white" if side_white else "black",
                    "uci": uci,
                    "loss_cp": int(loss_cp),
                    "before": eva_before,
                    "after": eva_after,
                }
            )

    return {
        "initial_fen": initial_fen,
        "moves": [m.uci() for m in moves],
        "moments": moments,
    }


def summarize_with_llm(analysis: Dict[str, Any], side: Optional[str] = None) -> str:
    side_str = side or "overall"
    system = (
        "You are a precise chess analyst. Use the provided engine-grounded data to write a concise,\n"
        "accurate review. Do not hallucinate board states. Focus on key mistakes (centipawn loss) and\n"
        "actionable lessons."
    )
    user = {
        "side": side_str,
        "initial_fen": analysis.get("initial_fen"),
        "moves": analysis.get("moves", []),
        "moments": analysis.get("moments", []),
    }
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                "Review the game from the following JSON. Focus on side={side}. Provide a narrative and bullet\n"
                "key takeaways.\nJSON:\n".replace("{side}", side_str) + str(user)
            ),
        },
    ]
    try:
        return chat_completion(messages, temperature=0.2)
    except Exception:
        # Fallback: basic handcrafted summary
        moments = analysis.get("moments", [])
        parts = [f"Review ({side_str}): {len(moments)} key moments detected."]
        for m in moments[:10]:
            parts.append(f"Ply {m['ply']} ({m['side']}): move {m['uci']} loss {m['loss_cp']} cp")
        return "\n".join(parts)


def review_game(pgn_text: str, side: Optional[str] = None, depth: int = 12) -> ReviewResult:
    analysis = analyze_pgn(pgn_text, ReviewConfig(depth=depth))
    summary = summarize_with_llm(analysis, side=side)
    # Convert moments to human-readable brief list
    kms = [
        f"Ply {m['ply']} ({m['side']}): {m['uci']} loss {m['loss_cp']} cp"
        for m in analysis.get("moments", [])
    ]
    return {
        "summary": summary,
        "key_moments": kms,
        "side": side or "overall",
    }
