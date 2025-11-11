import chess
import pytest

from thinkfish2.engine import StockfishEngine


@pytest.mark.skip(reason="Requires local stockfish binary (PATH or STOCKFISH_PATH)")
def test_engine_evaluate_smoke():
    eng = StockfishEngine()
    eng.start()
    res = eng.evaluate(chess.STARTING_FEN, depth=12)
    assert "score" in res and "pv" in res
