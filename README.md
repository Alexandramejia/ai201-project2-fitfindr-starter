# FitFindr

FitFindr is a small AI agent that helps people find secondhand clothing and figure out how to wear it. You give it a natural language query like "vintage graphic tee under $30, size M" and it searches a listings dataset, suggests a full outfit using your existing wardrobe, and generates a shareable caption for the look. The goal is to make thrift shopping feel less overwhelming — instead of just finding a random item, you leave with an actual outfit idea.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── tools.py                   # The three agent tools
├── agent.py                   # The planning loop
├── planning.md                # Planning doc filled out before implementation
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

---

## Tool Inventory

### `search_listings(description, size, max_price)`

Searches the mock listings dataset and returns items that match what the user described.

**Inputs:**
- `description` (str) — keywords from the user's query, e.g. `"vintage graphic tee"`
- `size` (str | None) — size to filter by, e.g. `"M"`; skipped if `None`
- `max_price` (float | None) — price ceiling, e.g. `30.0`; skipped if `None`

**Output:** A list of listing dicts sorted by relevance (best match first). Returns an empty list if nothing matches — never raises an exception.

**If it fails:** Returns `[]`. The agent catches this immediately and sets an error message without calling any other tools.

---

### `suggest_outfit(new_item, wardrobe)`

Uses an LLM to suggest 1–2 outfit combinations using the thrifted item and the user's wardrobe.

**Inputs:**
- `new_item` (dict) — the listing dict for the item the user is considering
- `wardrobe` (dict) — a dict with an `items` key containing a list of wardrobe pieces

**Output:** A plain string with outfit suggestions written conversationally.

**If it fails:** If the wardrobe is empty, it gives general styling advice instead of crashing. Always returns a non-empty string.

---

### `create_fit_card(outfit, new_item)`

Turns the outfit suggestion into a short caption suitable for Instagram or TikTok.

**Inputs:**
- `outfit` (str) — the suggestion string from `suggest_outfit`
- `new_item` (dict) — the listing dict (used for item name, price, and platform)

**Output:** A 2–4 sentence caption that sounds like a real OOTD post, not a product description.

**If it fails:** If `outfit` is empty or blank, returns a plain error string instead of raising an exception.

---

## Interaction Walkthrough

**User query:** `"looking for a vintage graphic tee under $30"`

**Step 1 — Tool called: `search_listings`**
- Tool: `search_listings`
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- Why this tool: the user's query was parsed into keywords and a price ceiling; this tool filters and ranks the dataset to find the closest match
- Output: a list of listing dicts sorted by relevance, e.g. `[{"title": "Vintage Band Tee – Faded Black", "price": 18.0, "platform": "Depop", ...}, ...]`

**Step 2 — Tool called: `suggest_outfit`**
- Tool: `suggest_outfit`
- Input: `new_item=results[0]` (the top listing), `wardrobe=get_example_wardrobe()`
- Why this tool: now that we have a specific item, the agent asks the LLM to pull pieces from the user's existing wardrobe and build a real outfit around it
- Output: a paragraph suggesting combinations like "Pair this with your high-waisted straight-leg jeans and white canvas sneakers for a classic thrift-store look..."

**Step 3 — Tool called: `create_fit_card`**
- Tool: `create_fit_card`
- Input: `outfit=session["outfit_suggestion"]`, `new_item=session["selected_item"]`
- Why this tool: takes the outfit idea and condenses it into a post-ready caption with the item's name, price, and platform
- Output: `"Found this faded band tee on Depop for $18 and I can't stop wearing it. Styled it with high-waisted jeans and white sneakers for that effortless thrift-store vibe."`

**Final output to user:**
```
Found: Vintage Band Tee – Faded Black

Outfit: Pair this with your high-waisted straight-leg jeans and white canvas sneakers...

Fit card: Found this faded band tee on Depop for $18 and I can't stop wearing it...
```

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | Returns `[]` when query is too specific, e.g. `"designer ballgown size XXS under $5"` | Sets `session["error"]` to a helpful message and returns the session early — `suggest_outfit` and `create_fit_card` are never called |
| `suggest_outfit` | Receives an empty wardrobe (`get_empty_wardrobe()`) | Detects that `wardrobe["items"]` is empty and switches to a general styling prompt; always returns a usable string |
| `create_fit_card` | Receives an empty or whitespace-only `outfit` string | Returns `"Unable to generate a fit card: no outfit suggestion was provided."` — no exception raised |

---

## Planning Loop

Here's the full step-by-step of what `run_agent()` does:

1. **Initialize session** — `_new_session()` creates the dict with all keys set to their defaults.
2. **Parse query** — `_parse_query()` uses regex to extract `description`, `size`, and `max_price` from the raw query string. Result goes into `session["parsed"]`.
3. **Call `search_listings`** — passes the three parsed values. Results go into `session["search_results"]`.
4. **Check for empty results** — if the list is empty, sets `session["error"]` and returns early. Nothing else runs.
5. **Select top result** — `results[0]` becomes `session["selected_item"]`.
6. **Call `suggest_outfit`** — passes `selected_item` and `wardrobe`. Result goes into `session["outfit_suggestion"]`.
7. **Call `create_fit_card`** — passes `outfit_suggestion` and `selected_item`. Result goes into `session["fit_card"]`.
8. **Return session** — caller checks `session["error"]` first, then reads `session["fit_card"]`.

---

## State Management

The session dict is created once at the start of `run_agent()` and updated as each step completes. No tool modifies it directly — the agent reads results and writes them into the session itself.

| Key | What it stores |
|---|---|
| `query` | The original user input, unchanged |
| `parsed` | Dict with `description`, `size`, `max_price` pulled from the query |
| `search_results` | Full list of matching listings from `search_listings` |
| `selected_item` | The top result (`search_results[0]`), passed into the next two tools |
| `wardrobe` | The user's wardrobe dict, passed in at the start |
| `outfit_suggestion` | The string returned by `suggest_outfit` |
| `fit_card` | The caption string returned by `create_fit_card` |
| `error` | A string if something went wrong, otherwise `None` |

The key design decision is that tools don't call each other — they each receive arguments from the agent. `selected_item` is stored in the session after step 5 and passed directly into `suggest_outfit`. The result comes back as `outfit_suggestion`, which is then passed into `create_fit_card`. The user is never asked anything again after the initial query.

---

## Spec Reflection

Writing `planning.md` before touching any code made implementation faster than expected. Having the data flow mapped out meant I wasn't making decisions about variable names or return types mid-function — those choices were already written down. The one thing that changed during implementation was in `suggest_outfit`: the original plan assumed the wardrobe would always have items, so I had to go back and add the empty wardrobe branch after realizing `get_empty_wardrobe()` was a required test case. It was a small change but a good reminder to trace through edge cases before writing the first line.

---

## AI Usage Transparency

**Example 1: Implementing `suggest_outfit` and `create_fit_card`**

I gave Claude the tool specifications from `planning.md` — the input/output descriptions, the empty wardrobe edge case requirement, and the caption style guidelines for `create_fit_card`. Claude generated the core LLM prompt strings and the conditional logic for the empty wardrobe branch in `suggest_outfit`. Before accepting the code, I changed the wardrobe formatting loop because the generated version assumed every wardrobe item had a `name` key, but the actual data uses either `name` or `title` depending on the entry. I also added `temperature=0.9` to the `create_fit_card` LLM call myself, since the spec called for varied outputs and the generated code left it at the default.

**Example 2: Implementing `run_agent`**

I gave Claude the Planning Loop and State Management sections from `planning.md`, including the session dict structure and the step-by-step sequence. Claude generated most of `run_agent()` in one pass. The main thing I caught during review was that the generated no-results case raised an exception instead of setting `session["error"]` and returning early, which didn't match the spec. I rewrote that part to match the expected behavior and double-checked that all the session keys matched what was defined in `_new_session()`.
