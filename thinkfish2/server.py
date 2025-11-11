from __future__ import annotations

"""
Minimal MCP-like server placeholder.

This module wires up tool handlers as simple JSON-RPC over stdin/stdout so that
it can run without additional dependencies. It mimics MCP semantics at a high
level (method names, structured inputs/outputs). You can replace the transport
with a true MCP server later without changing tool logic.
"""

import json
import sys
from typing import Any, Dict

from .chessio import (
    generate_legal_moves,
    load_pgn,
    san_to_uci,
    uci_to_san,
)
from .engine import StockfishEngine
from .review import review_game

_engine = StockfishEngine()


def handle_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if method == "engine.info":
        _engine.start()
        return {"ok": True, "engine": _engine.info()}
    if method == "engine.configure":
        # Basic runtime overrides for common options
        threads = params.get("threads")
        hash_mb = params.get("hash_mb")
        skill = params.get("skill")
        if threads:
            _engine.config.threads = int(threads)
        if hash_mb:
            _engine.config.hash_mb = int(hash_mb)
        if skill is not None:
            _engine.config.skill = int(skill)
        _engine.stop()
        _engine.start()
        return {"ok": True, "engine": _engine.info()}
    if method == "position.evaluate":
        fen = params["fen"]
        depth = int(params.get("depth", 16))
        multipv = int(params.get("multipv", 1))
        result = _engine.evaluate(fen=fen, depth=depth, multipv=multipv)
        return {"ok": True, "result": result}
    if method == "moves.generate_legal":
        fen = params["fen"]
        return {"ok": True, "result": generate_legal_moves(fen)}
    if method == "moves.uci_to_san":
        fen = params["fen"]
        uci_moves = params["uci_moves"]
        return {"ok": True, "result": uci_to_san(fen, uci_moves)}
    if method == "moves.san_to_uci":
        fen = params["fen"]
        san_moves = params["san_moves"]
        return {"ok": True, "result": san_to_uci(fen, san_moves)}
    if method == "pgn.load":
        return {"ok": True, "result": load_pgn(params["pgn"])}
    if method == "pgn.review_overall":
        depth = int(params.get("depth", 12))
        return {"ok": True, "result": review_game(params["pgn"], side="overall", depth=depth)}
    if method == "pgn.review_white":
        depth = int(params.get("depth", 12))
        return {"ok": True, "result": review_game(params["pgn"], side="white", depth=depth)}
    if method == "pgn.review_black":
        depth = int(params.get("depth", 12))
        return {"ok": True, "result": review_game(params["pgn"], side="black", depth=depth)}

    return {"ok": False, "error": f"Unknown method: {method}"}


def main() -> None:
    # Simple newline-delimited JSON-RPC: {"id": <id>, "method": str, "params": {}}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            rid = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            resp = handle_request(method, params)
            out = {"id": rid, **resp}
        except Exception as e:
            out = {"ok": False, "error": str(e)}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
