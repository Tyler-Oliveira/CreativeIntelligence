#!/usr/bin/env python3
"""Parse ChatGPT conversations.json and extract key content organized by domain."""

import json
import datetime
import re
import os

INPUT_FILE = "ChatGPT Download/conversations.json"
OUTPUT_DIR = "parsed_domains"

# Domain classification rules (checked in order, first match wins for primary)
DOMAIN_RULES = {
    "art_city": {
        "title_keywords": [
            "art city", "yourcompany", "Anytown", "yourcounty", "your-highway",
            "gathering", "catharsis", "forgefest", "boat ranch",
            "art attracts", "art enhancement", "art vision",
            "art-driven", "art driven", "revitalization",
            "small town revival", "small town", "cultural campus",
            "art city wind", "art city faq", "art city lesson",
            "art city foundation", "art city budget", "art city expansion",
            "art city pitch", "art city store", "art city project",
            "art city homes", "art city growth", "art city invest",
            "art city reflect", "art city announce", "art city strategy",
            "art city acquisition", "art city manifesto", "art city video",
            "art city website", "art city structure", "art city model",
            "art city rising", "art city building", "art city update",
            "art city ambitious", "acdc plan", "art city description",
            "art city gatherings", "art city insights", "art city cid",
            "Event Festival", "campground", "glamping", "campsite",
            "space activation", "skate park", "boulder broker",
            "nonprofit setup", "nonprofit wind", "501c3", "1023",
            "foundation overview", "wind down email",
            "exalted ruler", "minimum viable town",
            "nouns dao", "nouns sculpture", "nouns update",
        ],
    },
    "real_estate": {
        "title_keywords": [
            "real estate", "property", "land deal", "subdivision",
            "seller financ", "mortgage", "loan agreement", "construction loan",
            "1031 exchange", "strebeck", "strebek", "ute lake",
            "lot 108", "house sale", "building a house", "home build",
            "well drilling", "water rights", "easement",
            "deal memo", "deal structure", "land purchase",
            "campground valuation", "investment property",
            "sell travel trailer", "drywall", "square footage",
            "concrete", "panel calculation", "plywood",
            "permit requirements", "contractor", "journeyman",
            "nm land lease", "land with power",
            "construction", "home design", "house design",
            "house conversion", "kitchen design",
            "shelving", "bookshelf", "tile coverage",
            "penny floor",
        ],
    },
    "finance": {
        "title_keywords": [
            "investment", "market", "stock", "bitcoin", "btc", "crypto",
            "gold", "etf", "voo", "dividend", "portfolio",
            "recession", "inflation", "hyperinflation", "tariff",
            "yen carry", "vix", "nvidia", "apple invest",
            "safe vs", "safe terms", "canva invest",
            "net worth", "financially ready", "financial health",
            "financial position", "financial reset",
            "ira", "sep ira", "tax", "capital gains",
            "debt forgiveness", "loan payment", "valuation",
            "run rate", "revenue", "budget breakdown",
            "crisis playbook", "market extremes", "market analysis",
            "market outlook", "macro trend", "market stress",
            "interest rate", "bond yield", "oil vs gold",
            "asymmetric", "spac", "staking",
            "goldman sachs", "1mdb",
            "usa bankruptcy", "dollar devaluation",
            "currency collapse", "pe loan default",
            "robot impact", "excess compute",
            "options trading", "profiting from stock",
            "cap rate",
        ],
    },
    "memoir_creative": {
        "title_keywords": [
            "memoir", "jane d", "artist bio", "artist statement",
            "artistic journey", "hero's journey", "personal legend",
            "authenticity", "art philosophy",
            "manuscript", "book", "writing",
            "podcast", "documentary", "script",
            "brand brief", "brand", "merch",
            "logo", "design", "storefront sign",
            "social media", "content creation", "marketing",
            "ted talk", "manifesto",
            "year in review", "life summary",
            "interview", "transcript",
        ],
    },
    "life_personal": {
        "title_keywords": [
            "life vision", "vision 2030", "future vision",
            "self discovery", "self-discovery", "personal philosophy",
            "core beliefs", "5 year plan", "2025 plan", "2024 goals",
            "life optimization", "life forecast", "life path",
            "dating", "relationship", "partner", "elopement",
            "marriage", "betrayal", "gaslighting", "attachment",
            "parenting", "rebound",
            "astrology", "astrocartography", "vedic", "saturn return",
            "retrograde", "mercury retrograde",
            "meditation", "retreat", "panchakarma", "75 hard",
            "yoga", "primal movement", "fasting",
            "iridology", "liver cleanse", "inflammation",
            "health", "supar", "chest pain", "mri",
            "travel", "dolomites", "europe", "costa rica", "japan",
            "greece", "venice", "milan", "zurich", "spain",
            "baja", "tahiti", "dominican",
            "packing", "jet lag",
            "irish passport", "irish citizen", "visa",
            "south dakota residency",
            "homestead", "chickens", "garlic", "harvest",
            "birthday", "christmas", "nye",
            "gratitude", "manifestation", "law of one",
            "consciousness", "enlightenment",
        ],
    },
    "reference_legal": {
        "title_keywords": [
            "agreement", "contract", "lease", "consignment",
            "dissolution", "termination", "eviction",
            "trademark", "gdpr", "insurrection",
            "bylaws", "ordinance", "zoning",
            "rfp", "loi", "proposal",
            "at-will employment", "severance", "wrongful termination",
            "resignation",
        ],
    },
}

# Skip patterns - conversations that are just quick calculations or image generation
SKIP_PATTERNS = [
    r"^new chat$",
    r"days (between|until)",
    r"(sq|square) (meters?|feet|footage) to",
    r"^(acres?|gallons?) (in|to|conversion)",
    r"cubic feet",
    r"^(sum|total|percentage|calculate|calculation)",
    r"panel calculation",
    r"pixels per foot",
    r"^date calculation",
    r"fuel costs",
    r"hourly rate",
    r"annual salary",
    r"^turn (me|photo)",
    r"^animal to human",
    r"^friends in hot tub",
    r"^image (creation|transformation|aesthetic)",
    r"^(change|update) (color|image|time)",
    r"^(create|make|add) (fun|pattern|word)",
    r"^sparkly image",
    r"^clean up headshot",
    r"^(animate|remix) (a |)photo",
    r"^full body render",
    r"^painting mockup",
    r"^santa in",
    r"^(neon text|disco ball)",
    r"^font similarity",
    r"^porsche 912",
    r"^(explain|read|extract) (image|text|pdf|script)",
    r"^charger battery",
    r"^(unlock|plug) breaker",
    r"synonym for",
    r"^upside.down smiley",
    r"^android text",
    r"^papaya",
    r"^gen z term",
    r"^(what to plant|cooking)",
    r"^(colazione|valentín)",
    r"^(guess|guessing) personality",
    r"^lemon pig",
    r"^no senses",
]


def classify_conversation(title):
    """Classify a conversation into domains based on title."""
    title_lower = title.lower() if title else ""

    # Check skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, title_lower):
            return ["skip"]

    domains = []
    for domain, rules in DOMAIN_RULES.items():
        for kw in rules["title_keywords"]:
            if kw in title_lower:
                domains.append(domain)
                break

    return domains if domains else ["uncategorized"]


def extract_messages(conversation):
    """Extract the conversation thread in order."""
    mapping = conversation.get("mapping", {})

    # Build parent->children map
    children_map = {}
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent:
            children_map.setdefault(parent, []).append(node_id)

    # Find root
    root = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root = node_id
            break

    if not root:
        return []

    # Walk the main thread (follow current_node path)
    current_node = conversation.get("current_node")
    if not current_node:
        return []

    # Build path from current_node back to root
    path = []
    node_id = current_node
    while node_id:
        path.append(node_id)
        node = mapping.get(node_id, {})
        node_id = node.get("parent")
    path.reverse()

    messages = []
    for node_id in path:
        node = mapping.get(node_id, {})
        msg = node.get("message")
        if not msg:
            continue

        author = msg.get("author", {}).get("role", "unknown")
        content = msg.get("content", {})
        parts = content.get("parts", [])

        text_parts = []
        for part in parts:
            if isinstance(part, str) and part.strip():
                text_parts.append(part.strip())
            elif isinstance(part, dict):
                # Could be image or other content
                if part.get("content_type") == "text":
                    text_parts.append(part.get("text", ""))

        text = "\n".join(text_parts)
        if not text:
            continue

        create_time = msg.get("create_time")

        messages.append({
            "role": author,
            "text": text,
            "timestamp": create_time,
        })

    return messages


def summarize_conversation(title, messages, date):
    """Create a condensed summary focusing on user's ideas, decisions, and key info."""
    # Extract just user messages for the summary
    user_msgs = [m["text"] for m in messages if m["role"] == "user"]
    assistant_msgs = [m["text"] for m in messages if m["role"] == "assistant"]

    # Combine user messages (truncate very long ones)
    user_content = []
    for msg in user_msgs:
        if len(msg) > 2000:
            user_content.append(msg[:2000] + "...")
        else:
            user_content.append(msg)

    # Get key assistant responses (first and last, truncated)
    assistant_summary = []
    if assistant_msgs:
        first = assistant_msgs[0]
        if len(first) > 1500:
            first = first[:1500] + "..."
        assistant_summary.append(first)
        if len(assistant_msgs) > 1:
            last = assistant_msgs[-1]
            if len(last) > 1500:
                last = last[:1500] + "..."
            assistant_summary.append(last)

    return {
        "title": title,
        "date": date,
        "user_messages": user_content,
        "key_responses": assistant_summary,
        "message_count": len(messages),
    }


def main():
    print("Loading conversations...")
    with open(INPUT_FILE) as f:
        data = json.load(f)

    print(f"Total conversations: {len(data)}")

    # Classify and extract
    domains = {}
    skipped = 0
    uncategorized = []

    for conv in data:
        title = conv.get("title", "Untitled")
        ct = conv.get("create_time")
        date = datetime.datetime.fromtimestamp(ct).strftime("%Y-%m-%d") if ct else "Unknown"

        categories = classify_conversation(title)

        if "skip" in categories:
            skipped += 1
            continue

        messages = extract_messages(conv)
        if len(messages) < 3:
            skipped += 1
            continue

        summary = summarize_conversation(title, messages, date)

        if "uncategorized" in categories:
            uncategorized.append(summary)
            continue

        for cat in categories:
            domains.setdefault(cat, []).append(summary)

    # Sort each domain by date
    for domain in domains:
        domains[domain].sort(key=lambda x: x["date"])

    # Save to JSON for further processing
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for domain, convos in domains.items():
        output_file = os.path.join(OUTPUT_DIR, f"{domain}.json")
        with open(output_file, "w") as f:
            json.dump(convos, f, indent=2, ensure_ascii=False)
        print(f"  {domain}: {len(convos)} conversations")

    # Save uncategorized
    with open(os.path.join(OUTPUT_DIR, "uncategorized.json"), "w") as f:
        json.dump(uncategorized, f, indent=2, ensure_ascii=False)
    print(f"  uncategorized: {len(uncategorized)} conversations")
    print(f"  skipped: {skipped} conversations")

    # Print stats
    print("\n=== DOMAIN STATS ===")
    for domain, convos in sorted(domains.items(), key=lambda x: -len(x[1])):
        total_msgs = sum(c["message_count"] for c in convos)
        print(f"  {domain}: {len(convos)} convos, {total_msgs} total messages")


if __name__ == "__main__":
    main()
