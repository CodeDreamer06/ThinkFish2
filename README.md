# ThinkFish2: MCP Server for Chess Analysis with Stockfish + LLM

ThinkFish2 is an MCP (Model Context Protocol) server written in Python that connects the Stockfish chess engine to an LLM through tool-use. It enables reproducible, accurate chess analysis by letting LLMs call high-fidelity tools for evaluation, search, and game review—reducing hallucinations and improving explanatory quality.

Inspired by the original ThinkFish project (https://github.com/ronaldsuwandi/thinkfish), ThinkFish2 reimagines the architecture for server-side tool-use via the MCP protocol, focuses on correctness and reliability, and adds an extensible feature set suitable for production-grade integrations.


## Why ThinkFish2?

- Purpose-built for LLM tool-use: exposes chess analysis capabilities via MCP tools so that any MCP-compatible client/agent can leverage Stockfish safely and reproducibly.
- Accuracy-first: moves computation to a deterministic engine and feeds results to the LLM—dramatically reducing hallucinations.
- Extensible, Python-native: easy to add new tools and evaluators, swap engines, or integrate with different model providers.
- Practical game reviews: provides high-level and side-specific (White/Black) summaries grounded in engine analysis.


## Key Capabilities

- Stockfish-backed move and position evaluations (depth-configurable)
- UCI ↔ SAN/PGN conversions for human-readable outputs
- Multi-perspective game review tools (overall, White, Black)
- Before/After FEN prompting strategy (optional) to contextualize explanations
- Deterministic tool outputs consumable by LLMs for explanations and guidance
- Configurable engine parameters (skill level, contempt, threads, hash, min depth, etc.)
- Pluggable LLM layer (your MCP client/agent handles the model; ThinkFish2 focuses on tools)


## How It Works

ThinkFish2 runs as an MCP server process that registers a set of chess tools. MCP-compatible clients (e.g., agent frameworks, IDE assistants, or orchestrators) connect to the server and invoke tools during conversations. Typical flow:

1. Client sends a position or game (FEN/PGN) to a tool
2. ThinkFish2 calls Stockfish locally to evaluate/search
3. The tool returns structured, deterministic results (e.g., centipawn scores, principal variations, best move, move annotations)
4. Your LLM uses these results to produce reliable explanations and reviews

This separation of concerns lets the LLM focus on language and teaching while ThinkFish2 guarantees chess-grounded accuracy.


## Tools Exposed (MCP)

Planned initial tool surface (subject to change as we implement):

- engine.info: return current engine configuration and version
- engine.configure: set engine options (threads, hash, skill, contempt, etc.)
- position.evaluate: evaluate a FEN or board state (return score, depth, bestmove, PV)
- position.search_line: run a focused search for a given move sequence from a FEN
- moves.generate_legal: list legal moves from a FEN
- moves.uci_to_san: convert UCI moves to SAN (and optionally to annotated algebraic)
- moves.san_to_uci: convert SAN to UCI given a FEN context
- pgn.load: parse PGN and return a normalized representation
- pgn.review_overall: produce structured, engine-grounded game insights (uses LLM if VOIDAI_API_KEY set)
- pgn.review_white: White-centric summary grounded in engine deltas (uses LLM if available)
- pgn.review_black: Black-centric summary grounded in engine deltas (uses LLM if available)

Each tool will:
- Accept well-specified inputs (FEN/PGN/moves, numeric limits)
- Return typed, deterministic outputs suitable for direct LLM consumption
- Avoids free-form text unless explicitly requested


## Improvements Over the Original ThinkFish

- MCP-first architecture: native tool-use via the Model Context Protocol
- Stronger type discipline for tool inputs/outputs to reduce LLM ambiguity
- Deeper engine configurability and reproducibility controls
- Structured review outputs for downstream narrative generation
- Modular Python design for maintainability and testing


## Design Principles

- Safety by default: let the engine compute; let the LLM explain
- Deterministic interfaces: tools return structured data the same way every time
- Explicit context: optionally include before/after FENs to reduce hallucinations
- Testability: engine and chess logic are unit-testable without the LLM
- Extensibility: add tools without breaking clients


## Requirements

- Python 3.10+
- A Stockfish binary available on your PATH or configured via environment variable
- Optional: a supported MCP client/agent to consume the server’s tools

Recommended OS: Linux, macOS, or WSL on Windows.


## Installation

## Quick CLI Usage

- Ensure you have Python 3.10+ and Stockfish installed and on PATH.
- Run commands via the module runner:

Examples:

- Generate legal moves for a FEN:
  - python -m thinkfish2.cli legal "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

- Convert UCI moves to SAN from a given FEN:
  - python -m thinkfish2.cli convert "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" --uci e2e4 e7e5

- Convert SAN moves to UCI from a given FEN:
  - python -m thinkfish2.cli convert "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" --san e4 e5

- Load a PGN file and output normalized data as JSON:
  - python -m thinkfish2.cli pgn path/to/game.pgn

- Evaluate a position with Stockfish:
  - python -m thinkfish2.cli eval "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" --depth 14

- Start the minimal JSON-RPC style server:
  - python -m thinkfish2.server


1) Clone the repo
- git clone https://github.com/CodeDreamer06/ThinkFish2.git
- cd ThinkFish2

2) Create and activate a virtual environment
- python -m venv .venv
- source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

3) Install dependencies (to be finalized as we implement)
- pip install -U pip
- pip install -r requirements.txt  # when available

4) Ensure Stockfish is installed
- macOS: brew install stockfish
- Ubuntu/Debian: sudo apt-get install stockfish
- Windows: download from https://stockfishchess.org/download/

Set STOCKFISH_PATH if the binary is not on PATH.


## Configuration

Environment variables:
- STOCKFISH_PATH: path to Stockfish binary if not on PATH
- THINKFISH2_THREADS: number of engine threads
- THINKFISH2_HASH_MB: transposition table size (MB)
- THINKFISH2_MIN_DEPTH: minimum depth for evaluations
- THINKFISH2_SKILL: engine skill level (0-20)
- VOIDAI_API_KEY: API key for VoidAI chat completions (required for LLM summaries)
- VOIDAI_MODEL: Model name for VoidAI (default: kimi-k2-instruct)

Additional MCP or engine options may be added as the toolset grows.


## Running the Server

Run the JSON-RPC style server (MCP-like shim):
- python -m thinkfish2.server

Send newline-delimited JSON requests on stdin, receive JSON responses on stdout. Example:

Input:
{"id": 1, "method": "engine.info", "params": {}}
{"id": 2, "method": "position.evaluate", "params": {"fen": "startpos FEN here", "depth": 12}}

Refer to your MCP client’s docs for how to integrate with a custom server; this shim can be adapted to a true MCP transport.


## Examples

### Evaluate a Position

- Tool: position.evaluate
- Input: { fen: "<FEN>", depth: 18 }
- Output: {
    score: { type: "cp" | "mate", value: number },
    bestmove: "e2e4",
    pv: ["e2e4", "e7e5", ...],
    depth: 18,
    engine: { name, version }
  }

Your LLM can then transform this into a natural-language explanation or compare alternatives.


### Review a PGN (uses LLM if configured)

- Tool: pgn.review_overall
- Input: { pgn: "<PGN>", depth: 12 }
- Output: { summary: string, key_moments: string[], side: "overall" }

## Before/After FEN Prompting

We adopt the original project’s key insight: include both pre- and post-move FEN states to help the LLM understand board changes. ThinkFish2 will provide optional utilities to generate this pair for each half-move, enabling downstream prompts to be more grounded and less prone to hallucination.


## Roadmap

- v0.1
  - Minimal server with engine.info, position.evaluate, moves.generate_legal (DONE)
  - PGN parsing and basic conversions (UCI/SAN) (DONE)
- v0.2
  - Review tools (overall/white/black) with LLM summaries via VoidAI (DONE)
  - Search line and blunder detection helpers (BASIC BLUNDER HEURISTIC DONE)
- v0.3
  - True MCP transport and typed tool schemas
  - Caching, parallel analysis, and batch PGN review
  - Optional opening book integration

Community input welcome—open issues with proposals or requests.


## Differences vs. the Original ThinkFish

- Original: JS/Node web app using Stockfish.js; LLM produces narratives directly
- ThinkFish2: Python MCP server exposing tools; LLM consumes structured outputs to generate narratives in your client


## Repository Structure (proposed)

- thinkfish2/
  - engine.py          # Stockfish process management and options
  - chessio.py         # FEN/PGN parsing, UCI/SAN conversions
  - tools/             # MCP tool definitions and handlers
  - server.py          # MCP server entrypoint and wiring
  - types.py           # Typed schemas for inputs/outputs
  - utils.py           # Shared helpers
- tests/
  - unit/              # Unit tests for engine/chessio
  - integration/       # End-to-end tool tests

This structure will firm up as the implementation lands.


## Contributing

Contributions are welcome! Suggested ways to help:
- Discuss tool shapes and schemas in issues
- Add new MCP tools or engine features
- Improve evaluations or introduce review heuristics
- Enhance test coverage and CI

Please open an issue before substantial changes.


## License

MIT License. See LICENSE when added.


## Acknowledgements

- ThinkFish by Ronald Suwandi (inspiration): https://github.com/ronaldsuwandi/thinkfish
- Stockfish engine and contributors: https://stockfishchess.org/
- MCP community and tooling efforts
