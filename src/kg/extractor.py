"""Triplet extraction — uses an LLM to extract (head, relation, tail) triplets from chunks.

Each triplet links two entities via a relation and is traced back to its source chunk.
"""

import hashlib
import re
from dataclasses import dataclass

import structlog
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from src.config import get_settings

logger = structlog.get_logger(__name__)

_EXTRACTION_PROMPT = """\
Extract informative triplets directly from the text following the examples.
Each triplet should capture a factual relationship between two entities.
Do not add any extra words, line breaks, or spaces beyond the triplet format.

Example 1:
Text: Scott Derrickson (born July 16, 1966) is an American director, screenwriter and producer.
Triplets:
<Scott Derrickson, born in, 1966>
<Scott Derrickson, nationality, American>
<Scott Derrickson, occupation, director>
<Scott Derrickson, occupation, screenwriter>
<Scott Derrickson, occupation, producer>

Example 2:
Text: A process is an instance of a running program. The operating system manages processes \
using a process control block (PCB) which stores the process state.
Triplets:
<process, is instance of, running program>
<operating system, manages, processes>
<process control block, stores, process state>
<process control block, abbreviation, PCB>

Text: {text}
Triplets:
"""

_TRIPLET_PATTERN = re.compile(r"<\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^>]+?)\s*>")


@dataclass
class Triplet:
    head: str
    relation: str
    tail: str
    chunk_id: str


def make_chunk_id(doc: Document) -> str:
    """Generate a stable, deterministic ID for a chunk based on its source and position."""
    source = doc.metadata.get("source_file", "unknown")
    start = doc.metadata.get("start_index", 0)
    raw = f"{source}:{start}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _parse_triplets(text: str, chunk_id: str) -> list[Triplet]:
    """Parse LLM output into Triplet objects."""
    triplets = []
    for match in _TRIPLET_PATTERN.finditer(text):
        head = match.group(1).strip().lower()
        relation = match.group(2).strip().lower()
        tail = match.group(3).strip().lower()
        if head and relation and tail:
            triplets.append(Triplet(head=head, relation=relation, tail=tail, chunk_id=chunk_id))
    return triplets


def extract_triplets(chunks: list[Document], batch_size: int = 20) -> list[Triplet]:
    """Extract triplets from all chunks using the configured LLM.

    Processes chunks in batches. Each chunk gets a stable chunk_id added to its metadata.
    """
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.openai_api_key,
        temperature=0.0,
    )

    all_triplets: list[Triplet] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        logger.info("extracting_triplets", batch=f"{i+1}-{i+len(batch)}/{len(chunks)}")

        for doc in batch:
            chunk_id = make_chunk_id(doc)
            doc.metadata["chunk_id"] = chunk_id

            prompt = _EXTRACTION_PROMPT.format(text=doc.page_content)
            response = llm.invoke(prompt)
            triplets = _parse_triplets(response.content, chunk_id)
            all_triplets.extend(triplets)

    logger.info("triplet_extraction_complete", total_triplets=len(all_triplets))
    return all_triplets
