"""
Research engine for narrative discovery and topic investigation.

Two modes:
  - Web search (requires TAVILY_API_KEY): real-time results
  - Claude knowledge fallback: uses training data, flags that clearly

Flow:
  1. Convert user's research request into targeted search queries
  2. Search (Tavily or fallback)
  3. Extract narrative angles from results
  4. Each angle has headline, facts, relevance, and raw_text for content gen
"""

import os
import re
import json
import httpx
import anthropic
from dataclasses import dataclass, field


# ─── Data Model ───────────────────────────────────────────────────────────────

@dataclass
class ResearchAngle:
    headline: str          # One-sentence narrative hook
    source_url: str
    source_title: str
    key_facts: list[str]   # 3-5 concrete facts with numbers
    relevance: str         # Why this matters given project context
    raw_text: str          # Full extracted text for content generation
    from_live_search: bool = True


# ─── Search ───────────────────────────────────────────────────────────────────

def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """
    Call Tavily Search API. Returns list of result dicts.
    Returns empty list if no API key or request fails.
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []

    try:
        with httpx.Client(timeout=20) as http:
            resp = http.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False,
                }
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception:
        return []


# ─── Query Builder ────────────────────────────────────────────────────────────

def build_search_queries(
    research_input: str,
    project_context: str,
    client: anthropic.Anthropic
) -> list[str]:
    """
    Convert user's research request into 1-3 targeted search queries.
    Handles both:
      - Broad: "find narratives relevant to my DeFi protocol"
      - Specific: "Kelp DAO exploit details"
    """
    context_line = f"\nUser's project: {project_context}" if project_context.strip() else ""

    prompt = f"""Convert this research request into 1-3 targeted web search queries for finding recent relevant information.

Research request: {research_input}{context_line}

Rules:
- Return ONLY a JSON array of strings, no markdown
- Include year "2025" or "2026" in at least one query for recency
- If a specific protocol/event is mentioned, make the first query very precise
- Keep each query under 12 words
- For broad requests, make queries that would surface recent narratives in that space

Example output: ["Kelp DAO exploit 2025", "EigenLayer restaking security vulnerabilities"]"""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r'```json|```', '', resp.content[0].text.strip()).strip()
        queries = json.loads(raw)
        return [q for q in queries if isinstance(q, str)][:3]
    except Exception:
        return [research_input]


# ─── Angle Extraction ─────────────────────────────────────────────────────────

def extract_angles_from_results(
    search_results: list[dict],
    research_input: str,
    project_context: str,
    client: anthropic.Anthropic
) -> list[ResearchAngle]:
    """
    Use Claude to extract 1-3 narrative angles from raw search results.
    Each angle is a distinct hook worth building content around.
    """
    if not search_results:
        return []

    results_text = "\n\n---\n\n".join([
        f"URL: {r.get('url', '')}\n"
        f"Title: {r.get('title', '')}\n"
        f"Content: {r.get('content', '')[:700]}"
        for r in search_results[:6]
    ])

    context_line = f"\nUser's project/context: {project_context}" if project_context.strip() else ""

    system = """You extract narrative angles from research results for social media content creation.
A narrative angle is: something specific that happened + why it matters + what a clear position on it would be.

Return ONLY a valid JSON array. No markdown fences, no preamble.

Each object:
{
  "headline": "One sharp sentence — what happened or what the key insight is. Specific enough to argue with.",
  "source_url": "the source URL",
  "source_title": "article or source name",
  "key_facts": ["specific fact with number or date", "specific fact 2", "specific fact 3"],
  "relevance": "1-2 sentences on why this matters for the user's context",
  "raw_text": "200-300 words of the most important context from this source — preserve specific numbers, dates, protocol names"
}"""

    prompt = f"""Research query: {research_input}{context_line}

Search results:
{results_text}

Extract 1-3 distinct narrative angles worth building a post around.
Skip generic observations — every angle must have specific facts, names, or numbers that prove firsthand knowledge."""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r'```json|```', '', resp.content[0].text.strip()).strip()
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]

        return [
            ResearchAngle(
                headline=a.get("headline", ""),
                source_url=a.get("source_url", ""),
                source_title=a.get("source_title", ""),
                key_facts=a.get("key_facts", []),
                relevance=a.get("relevance", ""),
                raw_text=a.get("raw_text", ""),
                from_live_search=True,
            )
            for a in data
            if a.get("headline")
        ]
    except Exception:
        return []


# ─── Claude Knowledge Fallback ────────────────────────────────────────────────

def fallback_angles_from_knowledge(
    research_input: str,
    project_context: str,
    client: anthropic.Anthropic
) -> list[ResearchAngle]:
    """
    No Tavily key or search failed. Use Claude's training data.
    Clearly flags these as knowledge-based, not live search.
    """
    context_line = f"\nUser's project/context: {project_context}" if project_context.strip() else ""

    system = """You are a Web3/DeFi/crypto research assistant identifying narrative angles for content creation.

You are working from your training data — not live search. Be specific and factual within what you know, but do not invent events that haven't happened.

Return ONLY a valid JSON array. No markdown, no preamble.

Each object:
{
  "headline": "Sharp, specific narrative hook",
  "source_url": "",
  "source_title": "Claude knowledge base",
  "key_facts": ["specific fact 1", "specific fact 2", "specific fact 3"],
  "relevance": "Why this matters given the user's context",
  "raw_text": "200-300 words of concrete context, facts, numbers, and background on this topic"
}"""

    prompt = f"""Research request: {research_input}{context_line}

Identify 2-3 concrete narrative angles in this space. Base these on known events, patterns, or structural dynamics — not speculation. Each must have specific facts, numbers, or protocol names that someone could build an opinion post around.

Note: These will be flagged as based on your training data, not live search."""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = re.sub(r'```json|```', '', resp.content[0].text.strip()).strip()
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]

        return [
            ResearchAngle(
                headline=a.get("headline", ""),
                source_url=a.get("source_url", ""),
                source_title=a.get("source_title", "Claude knowledge base"),
                key_facts=a.get("key_facts", []),
                relevance=a.get("relevance", ""),
                raw_text=a.get("raw_text", ""),
                from_live_search=False,
            )
            for a in data
            if a.get("headline")
        ]
    except Exception:
        return []


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def research_topic(
    research_input: str,
    project_context: str,
    client: anthropic.Anthropic,
) -> tuple[list[ResearchAngle], bool]:
    """
    Full research pipeline.

    Returns:
        (angles, search_powered) where search_powered=True means live web results were used.

    Handles both modes transparently:
      - TAVILY_API_KEY set: real-time search → extract angles
      - No key: Claude knowledge fallback
    """
    has_tavily = bool(os.getenv("TAVILY_API_KEY", "").strip())

    if has_tavily:
        queries = build_search_queries(research_input, project_context, client)

        all_results: list[dict] = []
        seen_urls: set[str] = set()

        for query in queries:
            for r in search_tavily(query, max_results=5):
                url = r.get("url", "")
                if url and url not in seen_urls:
                    all_results.append(r)
                    seen_urls.add(url)

        if all_results:
            angles = extract_angles_from_results(
                all_results, research_input, project_context, client
            )
            if angles:
                return angles, True

    # Fallback: Claude knowledge
    angles = fallback_angles_from_knowledge(research_input, project_context, client)
    return angles, False
