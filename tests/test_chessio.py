import chess

from thinkfish2.chessio import generate_legal_moves, load_pgn, san_to_uci, uci_to_san


def test_generate_moves_startpos():
    res = generate_legal_moves(chess.STARTING_FEN)
    assert "e2e4" in res["legal_moves_uci"]
    assert "e7e5" not in res["legal_moves_uci"]


def test_uci_san_roundtrip():
    fen = chess.STARTING_FEN
    uci = ["e2e4", "e7e5", "g1f3"]
    san = uci_to_san(fen, uci)
    uci2 = san_to_uci(fen, san)
    assert uci2 == uci


def test_load_pgn_simple():
    pgn = """
[Event "?"]
[Site "?"]
[Date "2024.01.01"]
[Round "?"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 *
"""
    res = load_pgn(pgn)
    assert res["initial_fen"] == chess.STARTING_FEN
    assert res["moves_uci"][0] == "e2e4"
