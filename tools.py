"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    keywords = [kw.lower() for kw in description.split() if kw.strip()]

    results = []
    for listing in listings:
        # Filter by price
        if max_price is not None and listing.get("price", 0) > max_price:
            continue

        # Filter by size (case-insensitive substring match)
        if size and size.strip():
            listing_size = (listing.get("size") or "").lower()
            if size.lower() not in listing_size:
                continue

        # Score by keyword overlap across searchable fields
        searchable = " ".join([
            listing.get("title") or "",
            listing.get("description") or "",
            listing.get("category") or "",
            " ".join(listing.get("style_tags") or []),
            " ".join(listing.get("colors") or []),
            listing.get("brand") or "",
        ]).lower()

        score = sum(1 for kw in keywords if kw in searchable)

        if score > 0:
            results.append((score, listing))

    results.sort(key=lambda x: x[0], reverse=True)
    return [listing for _, listing in results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    title = new_item.get("title", "this item")
    category = new_item.get("category", "")
    style_tags = ", ".join(new_item.get("style_tags") or [])
    colors = ", ".join(new_item.get("colors") or [])
    brand = new_item.get("brand") or "unknown brand"
    condition = new_item.get("condition", "")

    item_summary = (
        f"Item: {title}\n"
        f"Category: {category}\n"
        f"Style tags: {style_tags}\n"
        f"Colors: {colors}\n"
        f"Brand: {brand}\n"
        f"Condition: {condition}"
    )

    wardrobe_items = (wardrobe or {}).get("items") or []

    if not wardrobe_items:
        prompt = (
            f"A user is considering buying this secondhand clothing item:\n\n"
            f"{item_summary}\n\n"
            "They don't have a wardrobe on file yet. Give them 1–2 general outfit ideas "
            "for this piece — what types of clothing, shoes, or accessories pair well with it, "
            "what vibe or occasion it suits, and any styling tips. Be specific and conversational."
        )
    else:
        wardrobe_lines = []
        for w in wardrobe_items:
            name = w.get("name") or w.get("title", "unknown piece")
            w_category = w.get("category", "")
            w_colors = ", ".join(w.get("colors") or []) if isinstance(w.get("colors"), list) else w.get("colors", "")
            wardrobe_lines.append(f"- {name} ({w_category}, {w_colors})")
        wardrobe_summary = "\n".join(wardrobe_lines)

        prompt = (
            f"A user is considering buying this secondhand clothing item:\n\n"
            f"{item_summary}\n\n"
            f"Their current wardrobe includes:\n{wardrobe_summary}\n\n"
            "Suggest 1–2 complete outfits that combine the new item with specific pieces "
            "from the wardrobe above. Name the wardrobe pieces you're pairing it with and "
            "briefly explain why the combination works. Be specific and conversational."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Unable to generate a fit card: no outfit suggestion was provided."

    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price")
    platform = new_item.get("platform", "a thrift platform")
    style_tags = ", ".join(new_item.get("style_tags") or [])

    price_str = f"${price:.2f}" if price is not None else "a great price"

    prompt = (
        f"Write a 2–4 sentence Instagram or TikTok caption for a thrift outfit post.\n\n"
        f"The thrifted item is: {title}, found on {platform} for {price_str}.\n"
        f"Style vibe: {style_tags}.\n"
        f"The outfit looks like this: {outfit}\n\n"
        "Guidelines:\n"
        "- Sound casual and authentic, like a real person posting their OOTD.\n"
        "- Mention the item name, price, and platform naturally — each only once.\n"
        "- Capture the specific vibe of the outfit in vivid but natural language.\n"
        "- Do not use hashtags or emojis.\n"
        "- Keep it to 2–4 sentences."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return response.choices[0].message.content or "Could not generate a fit card."
