from __future__ import annotations

import argparse
import json
import sys
from typing import List

import chess

from .chessio import generate_legal_moves, load_pgn, san_to_uci, uci_to_san
from .engine import StockfishEngine


def cmd_legal(args: argparse.Namespace) -> None:
    res = generate_legal_moves(args.fen)
    print(json.dumps(res))


def cmd_convert(args: argparse.Namespace) -> None:
    fen = args.fen
    if args.uci:
        moves = args.uci
        san = uci_to_san(fen, moves)
        print(json.dumps({"san": san}))
    elif args.san:
        moves = args.san
        uci = san_to_uci(fen, moves)
        print(json.dumps({"uci": uci}))
    else:
        raise SystemExit("Provide either --uci or --san")


def cmd_pgn(args: argparse.Namespace) -> None:
    if args.file == "-":
        text = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    res = load_pgn(text)
    print(json.dumps(res))


def cmd_eval(args: argparse.Namespace) -> None:
    fen = args.fen
    depth = args.depth
    eng = StockfishEngine()
    try:
        eng.start()
        res = eng.evaluate(fen, depth=depth)
    finally:
        eng.stop()
    print(json.dumps(res))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("thinkfish2")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_legal = sub.add_parser("legal", help="Generate legal moves for a FEN")
    p_legal.add_argument("fen")
    p_legal.set_defaults(func=cmd_legal)

    p_conv = sub.add_parser("convert", help="Convert between UCI and SAN")
    p_conv.add_argument("fen")
    grp = p_conv.add_mutually_exclusive_group(required=True)
    grp.add_argument("--uci", nargs="*", help="UCI moves list")
    grp.add_argument("--san", nargs="*", help="SAN moves list")
    p_conv.set_defaults(func=cmd_convert)

    p_pgn = sub.add_parser("pgn", help="Load a PGN file and output moves + initial FEN")
    p_pgn.add_argument("file", help="Path to PGN file or '-' for stdin")
    p_pgn.set_defaults(func=cmd_pgn)

    p_eval = sub.add_parser("eval", help="Evaluate a position (requires Stockfish)")
    p_eval.add_argument("fen")
    p_eval.add_argument("--depth", type=int, default=12)
    p_eval.set_defaults(func=cmd_eval)

    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
