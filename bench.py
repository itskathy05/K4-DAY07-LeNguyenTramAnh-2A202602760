from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
)
from src.models import Document
from src.store import EmbeddingStore


CORPUS_DIR = Path("data/scholarship")
OUTPUT_PATH = Path("ket_qua_benchmark.txt")
CACHE_PATH = Path(".benchmark_embedding_cache.json")
EXPECTED_DOCUMENT_COUNT = 8
TOP_K = 3

# Personal strategy: only this line should differ between team members.
CHUNKER = FixedSizeChunker(chunk_size=500, overlap=50)

# Shared team benchmark cases. The fifth case is the required filtered/A-B case.
BENCHMARK_CASES: list[dict] = [
    {
        "query": "Học bổng Green Tech 2026 có bao nhiêu suất, giá trị bao nhiêu và kéo dài bao lâu?",
        "gold_answer": ["18,000,000", "6 months"],
        "metadata_filter": None,
    },
    {
        "query": "Hạn cuối nộp hồ sơ học bổng Green Tech 2026 là ngày nào và thời gian dự kiến bắt đầu là khi nào?",
        "gold_answer": ["March 23, 2026", "April 2026"],
        "metadata_filter": None,
    },
    {
        "query": "Quy trình xét học bổng và hỗ trợ tài chính của USTH gồm những bước nào?",
        "gold_answer": ["Step 1", "Step 2", "Step 3"],
        "metadata_filter": None,
    },
    {
        "query": "Trong năm học 2026-2027, USTH dự kiến dành bao nhiêu tiền cho quỹ học bổng và áp dụng cho những nhóm người học nào?",
        "gold_answer": ["VND 16 billion", "undergraduate"],
        "metadata_filter": None,
    },
    {
        "query": "Đối tượng sinh viên nào được áp dụng các quy định học bổng năm 2026 của USTH?",
        "gold_answer": ["Vietnamese students", "international students"],
        "metadata_filter": {"audience": "student"},
    },
]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return simple YAML frontmatter fields and the Markdown body."""
    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text.strip()

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        match = re.match(r"^(\w+):\s*(.*)$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2).strip().strip('"').strip("'")
    return metadata, parts[2].strip()


def load_chunk_documents(corpus_dir: Path = CORPUS_DIR) -> list[Document]:
    """Load the eight source files and create traceable fixed-size chunks."""
    paths = sorted(corpus_dir.glob("*.md"))
    if len(paths) != EXPECTED_DOCUMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DOCUMENT_COUNT} Markdown documents in {corpus_dir}, "
            f"found {len(paths)}."
        )

    chunk_documents: list[Document] = []
    for path in paths:
        metadata, content = _parse_frontmatter(path.read_text(encoding="utf-8"))
        metadata = {
            **metadata,
            "doc_id": path.stem,
            "source_file": str(path),
        }

        for index, chunk in enumerate(CHUNKER.chunk(content)):
            chunk_documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    metadata={**metadata, "chunk_index": index},
                )
            )
    return chunk_documents


class CachedEmbedder:
    """Cache real embeddings by backend and content hash for repeatable reruns."""

    def __init__(self, embedder: Callable[[str], list[float]], cache_path: Path = CACHE_PATH) -> None:
        self.embedder = embedder
        self.cache_path = cache_path
        self._backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
        if cache_path.exists():
            self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            self.cache = {}

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        key = f"{self._backend_name}:{digest}"
        if key not in self.cache:
            self.cache[key] = self.embedder(text)
            self.cache_path.write_text(
                json.dumps(self.cache, ensure_ascii=False), encoding="utf-8"
            )
        return self.cache[key]


def create_real_embedder() -> CachedEmbedder:
    """Create a semantic embedder; MockEmbedder is intentionally unsupported."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "local").strip().lower()

    if provider == "local":
        embedder = LocalEmbedder(
            model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)
        )
    elif provider == "openai":
        embedder = OpenAIEmbedder(
            model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
        )
    elif provider == "gemini":
        embedder = GeminiEmbedder(
            model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)
        )
    else:
        raise ValueError(
            "Benchmark mode requires EMBEDDING_PROVIDER=local, openai, or gemini; "
            "MockEmbedder is not valid for semantic benchmark results."
        )
    return CachedEmbedder(embedder)


def build_store() -> tuple[EmbeddingStore, list[Document]]:
    """Chunk the corpus, embed every chunk, and return the populated store."""
    chunk_documents = load_chunk_documents()
    embedder = create_real_embedder()
    store = EmbeddingStore(
        collection_name="scholarship_fixed_500_overlap_50",
        embedding_fn=embedder,
    )
    store.add_documents(chunk_documents)
    return store, chunk_documents


def _answer_from_results(
    query: str,
    results: list[dict],
    llm_fn: Callable[[str], str] | None,
) -> str | None:
    if llm_fn is None:
        return None
    if not results:
        return "No relevant information was found in the knowledge base."

    context = "\n\n".join(
        f"[{index}] doc_id={result['metadata'].get('doc_id')} "
        f"source={result['metadata'].get('source_url')}\n{result['content']}"
        for index, result in enumerate(results, start=1)
    )
    prompt = (
        "Answer using only the retrieved context. Cite the supporting chunk number. "
        "If the answer is absent, say it was not found.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    )
    return llm_fn(prompt)


def run_benchmark_query(
    store: EmbeddingStore,
    query: str,
    metadata_filter: dict | None = None,
    top_k: int = TOP_K,
    llm_fn: Callable[[str], str] | None = None,
) -> dict:
    """Run one query, optionally pre-filtering candidates by metadata."""
    results = store.search_with_filter(
        query=query,
        top_k=top_k,
        metadata_filter=metadata_filter,
    )
    return {
        "query": query,
        "metadata_filter": metadata_filter,
        "results": results,
        "agent_answer": _answer_from_results(query, results, llm_fn),
    }


def format_benchmark_result(result: dict) -> str:
    """Format one query result for terminal output or the result text file."""
    lines = [
        f"Query: {result['query']}",
        f"Metadata filter: {result['metadata_filter']}",
    ]
    for rank, item in enumerate(result["results"], start=1):
        metadata = item["metadata"]
        lines.extend(
            [
                f"Top {rank}: score={item['score']:.6f}",
                f"  chunk_id={item['id']}",
                f"  doc_id={metadata.get('doc_id')}",
                f"  source_url={metadata.get('source_url')}",
                f"  content={item['content']}",
            ]
        )
    if result["agent_answer"] is not None:
        lines.append(f"Agent answer: {result['agent_answer']}")
    return "\n".join(lines)


def run_benchmark_suite(
    cases: list[dict],
    output_path: Path = OUTPUT_PATH,
    llm_fn: Callable[[str], str] | None = None,
) -> list[dict]:
    """Run the shared cases and save reproducible output for later evaluation."""
    if len(cases) != 5:
        raise ValueError("Insert exactly five team benchmark cases before running the suite.")

    store, chunk_documents = build_store()
    print(f"Loaded {EXPECTED_DOCUMENT_COUNT} source documents")
    print(f"Stored {len(chunk_documents)} chunks")

    outputs = []
    formatted = []
    for case in cases:
        result = run_benchmark_query(
            store=store,
            query=case["query"],
            metadata_filter=case.get("metadata_filter"),
            top_k=TOP_K,
            llm_fn=llm_fn,
        )
        result["gold_answer"] = case["gold_answer"]
        outputs.append(result)
        rendered = format_benchmark_result(result)
        formatted.append(rendered)
        print(f"\n{rendered}")

    output_path.write_text("\n\n".join(formatted) + "\n", encoding="utf-8")
    print(f"\nSaved benchmark output to {output_path}")
    return outputs


def main() -> int:
    if not BENCHMARK_CASES:
        print("Benchmark pipeline is ready.")
        print("Insert the team's five shared queries and gold answers into BENCHMARK_CASES.")
        print("No benchmark was executed.")
        return 0

    run_benchmark_suite(BENCHMARK_CASES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
