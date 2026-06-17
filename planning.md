# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
This tool searches the secondhand clothing listings based on what the user is looking for. It filters items using the description, size, and max price.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The type of item the user wants, such as "vintage graphic tee" or "denim jacket."
- `size` (str): The clothing size the user wants, such as "S", "M", or "L." This can be empty if the user does not give a size.
- `max_price` (float): The highest price the user is willing to pay.

**What it returns:**
It returns a list of matching clothing items. Each item can include fields like id, title, description, category, style_tags, size, condition, price, colors, brand, and platform.

**What happens if it fails or returns nothing:**
If no listings match, the agent tells the user that nothing was found and suggests changing the search, size, or price. The agent stops and does not call the outfit tool.

---

### Tool 2: suggest_outfit

**What it does:**
This tool takes the item found from the search and suggests how the user can style it with their wardrobe. It creates a simple outfit idea using the new item and clothes the user already owns.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The clothing item selected from search_listings.
- `wardrobe` (dict): The user's wardrobe information, including items they already own.

**What it returns:**
It returns a written outfit suggestion. The suggestion explains what to wear with the new item and gives styling advice.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, the tool still gives general styling advice instead of crashing. If no outfit can be suggested, the agent tells the user that it could not make a full outfit and gives a basic styling idea.

---

### Tool 3: create_fit_card

**What it does:**
This tool turns the outfit suggestion into a short, shareable caption. The fit card should sound like something someone might post on social media.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion created by suggest_outfit.
- `new_item` (dict): The clothing item selected from the listings.

**What it returns:**
It returns a short caption or fit card describing the outfit in a fun way.

**What happens if it fails or returns nothing:**
If the outfit information is missing or incomplete, the tool returns an error message instead of crashing. The agent tells the user that it needs a valid outfit before making a fit card.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
No additional tools for this version. I am only completing the required three tools.

---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent starts with the user's request. First, it calls `search_listings(description, size, max_price)` to find matching thrift items. After search_listings runs, the agent checks if the results list is empty. If it is empty, the agent saves an error message and stops. If results are found, the agent chooses the first item and saves it as `selected_item`.

Next, the agent calls `suggest_outfit(selected_item, wardrobe)` using the item from the search and the user's wardrobe. The outfit suggestion is saved as `outfit_suggestion`. If the outfit suggestion is missing, the agent saves an error message and stops.

Finally, the agent calls `create_fit_card(outfit_suggestion, selected_item)` to make a short caption. The fit card is saved and returned to the user. The loop is done once the search result, outfit suggestion, and fit card are all created or when an error stops the process early.

---

## State Management

**How does information from one tool get passed to the next?**
The agent uses a session dictionary to remember information during one user interaction. After `search_listings` finds results, the first result is stored as `selected_item`. That same `selected_item` is passed into `suggest_outfit`. Then the outfit suggestion is stored as `outfit_suggestion` and passed into `create_fit_card`.

The session tracks the user query, listings found, selected item, wardrobe, outfit suggestion, fit card, and any error message. This lets the agent move step by step without asking the user to re-enter the same information.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The agent tells the user no matching listings were found and suggests trying a different description, size, or price. It stops before calling the next tools. |
| suggest_outfit | Wardrobe is empty | The agent gives general styling advice using the new item instead of crashing. |
| create_fit_card | Outfit input is missing or incomplete | The agent returns a message saying it needs a valid outfit suggestion before it can create a fit card. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```text
User query
    |
    v
Planning Loop
    |
    v
search_listings(description, size, max_price)
    |
    |-- results empty --> Save error message --> Return to user
    |
    |-- results found
    v
Session stores selected_item = first result
    |
    v
suggest_outfit(selected_item, wardrobe)
    |
    |-- outfit missing --> Save error message --> Return to user
    |
    v
Session stores outfit_suggestion
    |
    v
create_fit_card(outfit_suggestion, selected_item)
    |
    |-- fit card missing --> Save error message --> Return to user
    |
    v
Session stores fit_card
    |
    v
Return listing, outfit suggestion, and fit card to user
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I'll give Claude the Tool 1 spec (inputs: description, size, max_price; return value: list of matching item dicts; failure: return empty list) and ask it to implement `search_listings()` using `load_listings()` from the data loader. I'll test it against at least 3 queries — one that returns results, one with no matches, and one that filters by size — before moving on. For Tool 2, I'll give Claude the Tool 2 spec and ask it to implement `suggest_outfit()`, then verify it handles an empty wardrobe by running it with `wardrobe={}`. For Tool 3, I'll give Claude the Tool 3 spec and ask it to implement `create_fit_card()`, then confirm it returns a string caption and handles a missing outfit input with a clear error message rather than a crash.

**Milestone 4 — Planning loop and state management:**
I'll give Claude the Architecture diagram and State Management section from this planning.md and ask it to implement the planning loop. I'll verify that the session dictionary correctly stores `selected_item`, `outfit_suggestion`, and `fit_card` by printing the session after each step. I'll also test the early-stop behavior by running a query with no matching listings and confirming the agent stops without calling `suggest_outfit` or `create_fit_card`.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent parses the query and calls `search_listings(description="vintage graphic tee", size="", max_price=30.0)`. The tool scans the listings data and returns a list of matching items. For example, it returns a vintage band tee in size M, priced at $22, listed on Depop in good condition.

**Step 2:**
The agent takes the first result from the list and stores it as `selected_item`. It then calls `suggest_outfit(new_item=selected_item, wardrobe={"bottoms": ["baggy jeans"], "shoes": ["chunky sneakers"]})`. The tool returns an outfit suggestion such as: "Pair the vintage band tee with your baggy jeans — tuck the front in slightly for shape — and finish with your chunky sneakers for a 90s-inspired streetwear look."

**Step 3:**
The agent stores the outfit suggestion as `outfit_suggestion` and calls `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`. The tool returns a short, social-media-style caption such as: "thrifted this vintage band tee for $22 and it already goes with everything I own. baggy jeans + chunky sneakers = the fit. 🤌 #thriftfinds #outfitinspo"

**Final output to user:**
The user sees three things: the listing details for the found item (title, price, condition, platform), the full outfit suggestion explaining how to style it with their existing wardrobe, and the shareable fit card caption they can copy and post.
