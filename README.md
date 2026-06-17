# FitFindr

FitFindr is an AI agent that helps people find secondhand clothing and figure out how to wear it. You give it a query like "vintage graphic tee under $30, size M" and it searches a listings dataset, suggests an outfit using your existing wardrobe, and generates a caption for the look.

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

`data/wardrobe_schema.json` defines the format the agent uses to represent a user's wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items for testing
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
- `description` (str): keywords from the user's query, like `"vintage graphic tee"`
- `size` (str | None): size to filter by, like `"M"`. Skipped if `None`
- `max_price` (float | None): price ceiling, like `30.0`. Skipped if `None`

**Output:** A list of listing dicts sorted by relevance, best match first. Returns an empty list if nothing matches and never raises an exception.

**If it fails:** The agent catches the empty list and sets an error message without calling any other tools.

---

### `suggest_outfit(new_item, wardrobe)`

Uses an LLM to suggest 1-2 outfit combinations using the thrifted item and the user's wardrobe.

**Inputs:**
- `new_item` (dict): the listing dict for the item the user is considering
- `wardrobe` (dict): a dict with an `items` key containing a list of wardrobe pieces

**Output:** A string with outfit suggestions written conversationally.

**If it fails:** If the wardrobe is empty, it gives general styling advice instead of crashing. It always returns something.

---

### `create_fit_card(outfit, new_item)`

Turns the outfit suggestion into a short caption for Instagram or TikTok.

**Inputs:**
- `outfit` (str): the suggestion string from `suggest_outfit`
- `new_item` (dict): the listing dict, used for the item name, price, and platform

**Output:** A 2-4 sentence caption that sounds like a real OOTD post.

**If it fails:** If `outfit` is empty or blank, it returns an error string instead of raising an exception.

---

## Interaction Walkthrough

**User query:** `"looking for a vintage graphic tee under $30"`

**Step 1: `search_listings`**
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- Why: the query was parsed into keywords and a price ceiling. This tool filters and scores the dataset to find the closest match.
- Output: a list of listing dicts sorted by relevance, e.g. `[{"title": "Vintage Band Tee Faded Black", "price": 18.0, "platform": "Depop", ...}, ...]`

**Step 2: `suggest_outfit`**
- Input: `new_item=results[0]` (the top listing), `wardrobe=get_example_wardrobe()`
- Why: now that we have a specific item, the agent asks the LLM to build an outfit using pieces from the user's wardrobe.
- Output: something like "Pair this with your high-waisted straight-leg jeans and white canvas sneakers for a classic thrift-store look..."

**Step 3: `create_fit_card`**
- Input: `outfit=session["outfit_suggestion"]`, `new_item=session["selected_item"]`
- Why: takes the outfit description and turns it into a caption with the item name, price, and platform.
- Output: `"Found this faded band tee on Depop for $18 and I can't stop wearing it. Styled it with high-waisted jeans and white sneakers for that effortless thrift-store vibe."`

**Final output:**
```
Found: Vintage Band Tee Faded Black

Outfit: Pair this with your high-waisted straight-leg jeans and white canvas sneakers...

Fit card: Found this faded band tee on Depop for $18 and I can't stop wearing it...
```

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | Returns `[]` when nothing matches, e.g. `"designer ballgown size XXS under $5"` | Sets `session["error"]` and exits early. `suggest_outfit` and `create_fit_card` never run. |
| `suggest_outfit` | Gets an empty wardrobe from `get_empty_wardrobe()` | Detects that `wardrobe["items"]` is empty and uses a different prompt that gives general styling advice instead |
| `create_fit_card` | Gets an empty `outfit` string | Returns `"Unable to generate a fit card: no outfit suggestion was provided."` without raising an exception |

---

## Planning Loop

Here's what `run_agent()` does step by step:

1. **Initialize session** - `_new_session()` creates the dict with all keys set to their defaults.
2. **Parse query** - `_parse_query()` uses regex to pull out `description`, `size`, and `max_price` from the raw query. Result goes into `session["parsed"]`.
3. **Call `search_listings`** - passes the three parsed values. Results go into `session["search_results"]`.
4. **Check for empty results** - if the list is empty, sets `session["error"]` and returns early.
5. **Select top result** - `results[0]` becomes `session["selected_item"]`.
6. **Call `suggest_outfit`** - passes `selected_item` and `wardrobe`. Result goes into `session["outfit_suggestion"]`.
7. **Call `create_fit_card`** - passes `outfit_suggestion` and `selected_item`. Result goes into `session["fit_card"]`.
8. **Return session** - the caller checks `session["error"]` first, then reads `session["fit_card"]`.

---

## State Management

The session dict is created at the start of `run_agent()` and updated as each step runs. Tools don't talk to each other directly, they just receive arguments from the agent.

| Key | What it stores |
|---|---|
| `query` | The original user input, unchanged |
| `parsed` | Dict with `description`, `size`, `max_price` pulled from the query |
| `search_results` | Full list of matching listings from `search_listings` |
| `selected_item` | The top result, `search_results[0]`, passed into the next two tools |
| `wardrobe` | The user's wardrobe dict, passed in at the start |
| `outfit_suggestion` | The string returned by `suggest_outfit` |
| `fit_card` | The caption string returned by `create_fit_card` |
| `error` | A string if something went wrong, otherwise `None` |

`selected_item` gets stored after step 5 and passed directly into `suggest_outfit`. The result comes back as `outfit_suggestion` and is then passed into `create_fit_card`. The user is never prompted again after the initial query.

---

## Spec Reflection

Writing `planning.md` before writing any code actually helped a lot. Having the data flow written out meant I wasn't stopping mid-function to figure out what to name things or what to return. The one thing that changed during implementation was in `suggest_outfit`. The original plan didn't account for an empty wardrobe, so I had to go back and add that branch after realizing `get_empty_wardrobe()` was a required test case. It was an easy fix once I caught it, but it showed me why tracing through edge cases in planning is worth the time.

---

## AI Usage Transparency

**Example 1: Implementing `suggest_outfit` and `create_fit_card`**

I gave Claude the tool specs from `planning.md`, including the input/output descriptions, the empty wardrobe edge case, and the caption style guidelines for `create_fit_card`. It generated the LLM prompt strings and the conditional logic for the empty wardrobe branch. Before accepting the code I changed the wardrobe formatting loop because the generated version assumed every item had a `name` key, but the actual data uses either `name` or `title`. I also added `temperature=0.9` to `create_fit_card` myself since the spec said outputs should vary and Claude left it at the default.

**Example 2: Implementing `run_agent`**

I gave Claude the Planning Loop and State Management sections from `planning.md`, including the session dict structure and the step-by-step sequence. It generated most of `run_agent()` in one pass. The main issue I caught was that the no-results case raised an exception instead of setting `session["error"]` and returning early, which didn't match the spec. I rewrote that part and checked that all the session keys lined up with what `_new_session()` defined.
