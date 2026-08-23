"""Tree-sitter parser adapter for SecureOps analysis rules."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

DEFAULT_SECONDARY_LANGUAGE = "javascript"


class ParserError(RuntimeError):
    """Base error raised by parser adapter failures."""


class UnsupportedLanguageError(ParserError):
    """Raised when no Tree-sitter grammar is configured for a language."""


class ParserUnavailableError(ParserError):
    """Raised when Tree-sitter or a configured grammar cannot be loaded."""


@dataclass(frozen=True)
class LanguageSpec:
    """Runtime grammar metadata for one supported language."""

    key: str
    package: str
    extensions: tuple[str, ...]
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedSource:
    """Parsed source plus helpers needed by deterministic rules."""

    language: str
    source: bytes
    tree: Any
    file_path: str | None = None

    @property
    def root_node(self) -> Any:
        """Return the Tree-sitter root node."""
        return self.tree.root_node

    @property
    def has_errors(self) -> bool:
        """Return whether Tree-sitter reported syntax errors."""
        return bool(getattr(self.root_node, "has_error", False))

    def text_for_node(self, node: Any) -> str:
        """Return UTF-8 decoded source text covered by a Tree-sitter node."""
        return self.source[node.start_byte : node.end_byte].decode(
            "utf-8",
            errors="replace",
        )

    def line_for_node(self, node: Any) -> int:
        """Return the one-based starting line for a node."""
        return int(node.start_point[0]) + 1

    def line_range_for_node(self, node: Any) -> tuple[int, int]:
        """Return one-based inclusive start and end lines for a node."""
        return (int(node.start_point[0]) + 1, int(node.end_point[0]) + 1)


LANGUAGE_SPECS: tuple[LanguageSpec, ...] = (
    LanguageSpec(
        key="python",
        package="tree_sitter_python",
        extensions=(".py", ".pyw"),
        aliases=("py", "python3"),
    ),
    LanguageSpec(
        key=DEFAULT_SECONDARY_LANGUAGE,
        package="tree_sitter_javascript",
        extensions=(".js", ".jsx", ".mjs", ".cjs"),
        aliases=("js", "node"),
    ),
)

_SPECS_BY_LANGUAGE: dict[str, LanguageSpec] = {
    name: spec
    for spec in LANGUAGE_SPECS
    for name in (spec.key, *spec.aliases)
}

_LANGUAGE_BY_EXTENSION: dict[str, str] = {
    extension: spec.key
    for spec in LANGUAGE_SPECS
    for extension in spec.extensions
}


def normalize_language(language: str) -> str:
    """Return the canonical key for a supported language."""
    key = language.strip().lower()
    try:
        return _SPECS_BY_LANGUAGE[key].key
    except KeyError as exc:
        supported = ", ".join(sorted(spec.key for spec in LANGUAGE_SPECS))
        msg = f"Unsupported language '{language}'. Supported languages: {supported}."
        raise UnsupportedLanguageError(msg) from exc


def detect_language(file_path: str | Path) -> str | None:
    """Infer a supported language from a source file path."""
    return _LANGUAGE_BY_EXTENSION.get(Path(file_path).suffix.lower())


def supported_languages() -> tuple[str, ...]:
    """Return canonical language keys supported by this adapter."""
    return tuple(spec.key for spec in LANGUAGE_SPECS)


def is_supported_language(language: str) -> bool:
    """Return whether a language key or alias is supported."""
    return language.strip().lower() in _SPECS_BY_LANGUAGE


def iter_nodes(node: Any, *, types: Iterable[str] | None = None) -> Iterable[Any]:
    """Yield a node and its descendants, optionally filtered by node type."""
    wanted = set(types) if types is not None else None
    stack = [node]

    while stack:
        current = stack.pop()
        if wanted is None or current.type in wanted:
            yield current
        stack.extend(reversed(current.children))


class TreeSitterParserAdapter:
    """Small adapter around Tree-sitter grammars used by analysis rules."""

    def parse(
        self,
        source: str | bytes,
        language: str,
        *,
        file_path: str | Path | None = None,
    ) -> ParsedSource:
        """Parse source code for a supported language."""
        canonical_language = normalize_language(language)
        source_bytes = self._to_bytes(source)
        parser = _new_parser(canonical_language)
        tree = parser.parse(source_bytes)
        path_value = None if file_path is None else str(file_path)
        return ParsedSource(
            language=canonical_language,
            source=source_bytes,
            tree=tree,
            file_path=path_value,
        )

    def parse_file(
        self,
        file_path: str | Path,
        *,
        language: str | None = None,
    ) -> ParsedSource:
        """Read and parse a source file, inferring language when omitted."""
        path = Path(file_path)
        selected_language = language or detect_language(path)
        if selected_language is None:
            msg = f"Cannot infer a supported language from '{path}'."
            raise UnsupportedLanguageError(msg)
        return self.parse(
            path.read_bytes(),
            selected_language,
            file_path=path,
        )

    @staticmethod
    def _to_bytes(source: str | bytes) -> bytes:
        if isinstance(source, bytes):
            return source
        return source.encode("utf-8")


def _new_parser(language: str) -> Any:
    """Build a Tree-sitter parser for a canonical language key."""
    try:
        from tree_sitter import Parser
    except ModuleNotFoundError as exc:
        msg = "Python package 'tree_sitter' is not installed."
        raise ParserUnavailableError(msg) from exc

    tree_sitter_language = _get_tree_sitter_language(language)

    try:
        parser = Parser()
        if hasattr(parser, "set_language"):
            parser.set_language(tree_sitter_language)
        else:
            parser.language = tree_sitter_language
    except Exception as exc:
        msg = f"Could not initialize Tree-sitter parser for '{language}'."
        raise ParserUnavailableError(msg) from exc

    return parser


@lru_cache(maxsize=len(LANGUAGE_SPECS))
def _get_tree_sitter_language(language: str) -> Any:
    """Load and cache the immutable Tree-sitter language object."""
    spec = _SPECS_BY_LANGUAGE[language]

    try:
        grammar_module = import_module(spec.package)
    except ModuleNotFoundError as exc:
        msg = f"Tree-sitter grammar package '{spec.package}' is not installed."
        raise ParserUnavailableError(msg) from exc

    try:
        from tree_sitter import Language
    except ModuleNotFoundError as exc:
        msg = "Python package 'tree_sitter' is not installed."
        raise ParserUnavailableError(msg) from exc

    try:
        language_factory = getattr(grammar_module, "language")
        raw_language = language_factory()
        if isinstance(raw_language, Language):
            return raw_language
        return Language(raw_language)
    except Exception as exc:
        msg = f"Could not initialize Tree-sitter language for '{language}'."
        raise ParserUnavailableError(msg) from exc


default_parser = TreeSitterParserAdapter()


def parse_source(
    source: str | bytes,
    language: str,
    *,
    file_path: str | Path | None = None,
) -> ParsedSource:
    """Parse source code with the process-wide parser adapter."""
    return default_parser.parse(source, language, file_path=file_path)


def parse_file(
    file_path: str | Path,
    *,
    language: str | None = None,
) -> ParsedSource:
    """Parse a source file with the process-wide parser adapter."""
    return default_parser.parse_file(file_path, language=language)


__all__ = [
    "DEFAULT_SECONDARY_LANGUAGE",
    "LANGUAGE_SPECS",
    "LanguageSpec",
    "ParsedSource",
    "ParserError",
    "ParserUnavailableError",
    "TreeSitterParserAdapter",
    "UnsupportedLanguageError",
    "default_parser",
    "detect_language",
    "is_supported_language",
    "iter_nodes",
    "normalize_language",
    "parse_file",
    "parse_source",
    "supported_languages",
]
