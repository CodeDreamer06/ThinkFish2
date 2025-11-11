from __future__ import annotations

from io import StringIO
from typing import List

import chess
import chess.pgn

from .types import (
    GenerateMovesResult,
    PGNLoadResult,
)


def generate_legal_moves(fen: str) -> GenerateMovesResult:
    board = chess.Board(fen)
    moves = [m.uci() for m in board.legal_moves]
    return {"legal_moves_uci": moves}


def uci_to_san(fen: str, uci_moves: List[str]) -> List[str]:
    board = chess.Board(fen)
    san_list: List[str] = []
    for u in uci_moves:
        move = chess.Move.from_uci(u)
        san = board.san(move)
        san_list.append(san)
        board.push(move)
    return san_list


def san_to_uci(fen: str, san_moves: List[str]) -> List[str]:
    board = chess.Board(fen)
    uci_list: List[str] = []
    for s in san_moves:
        move = board.parse_san(s)
        uci_list.append(move.uci())
        board.push(move)
    return uci_list


def load_pgn(pgn_text: str) -> PGNLoadResult:
    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        return {"moves_uci": [], "initial_fen": chess.STARTING_FEN}
    board = game.board()
    moves_uci: List[str] = []
    for move in game.mainline_moves():
        moves_uci.append(move.uci())
        board.push(move)
    initial_fen = game.headers.get("FEN", chess.STARTING_FEN)
    return {"moves_uci": moves_uci, "initial_fen": initial_fen}
