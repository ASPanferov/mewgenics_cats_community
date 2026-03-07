"""AI prompt writer: uses Gemini Flash to generate detailed visual prompts from raw cat data."""

import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PROMPT_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are an expert prompt writer for AI image generation. Your job is to transform structured game character data into a single, highly detailed visual description prompt.

TARGET ART STYLE: Edmund McMillen's Mewgenics / The Binding of Isaac
- Hand-drawn grotesque-cute cartoon style
- Thick black outlines, exaggerated proportions
- Bug-eyed with huge glossy tearful eyes
- Lumpy misshapen bodies, visible stitches and imperfections
- Simultaneously adorable and deeply unsettling
- Newgrounds Flash animation aesthetic
- Dark humor undertones
- Soft pale sickly color palette with pops of visceral red and sickly green
- Simple messy background with dark vignette edges
- Like a cursed children's book illustration

RULES:
1. Output ONLY the image prompt — no explanations, no markdown, no prefixes
2. Draw exactly ONE single cat character as the main subject
3. NEVER include text, words, letters, numbers, or labels in the image description
4. Express everything through visual elements, body language, colors, effects, accessories
5. Combine all character traits into ONE coherent visual — don't list them separately
6. The cat's CLASS determines its overall archetype and dominant color
7. STATS relative to each other determine body proportions (high STR = muscular, low INT = tiny head, etc.)
8. ABILITIES should manifest as visible magical/physical effects ON or AROUND the cat
9. PASSIVES should be subtle persistent visual traits (auras, body modifications, environmental effects)
10. ITEMS should be visible accessories, held objects, or worn equipment — grotesque and McMillen-style
11. MUTATIONS should be visible body deformations on the specific body part
12. Birth defects (frame >= 700) should look more severe and wrong than regular mutations
13. INJURED cats should show bandages, wounds, limping posture
14. Keep the prompt under 400 words — dense and visual, no filler
15. Prioritize the most visually distinctive features — don't try to cram everything in if it becomes incoherent

COLOR PALETTE BY CLASS:
- Fighter: red-orange | Tank: orange | Hunter: green | Mage: lavender/purple
- Medic: white/cream | Necromancer: black/dark grey + sickly green | Druid: earthy brown-green
- Thief: pale yellow | Tinkerer: lime green | Colorless: grey-beige
- Monk: golden-tan | Psychic: pale purple/pink | Jester: multicolored patchwork | Butcher: blood red"""


def _build_cat_data_text(cat_data: dict) -> str:
    """Format raw cat data into structured text for the prompt writer."""
    lines = []
    lines.append(f"NAME: {cat_data.get('name', 'Unknown')}")
    lines.append(f"GENDER: {cat_data.get('gender', 'unknown')}")
    lines.append(f"CLASS: {cat_data.get('class_en', 'Colorless')} ({cat_data.get('class_ru', '')})")
    lines.append(f"STATUS: {cat_data.get('status', 'OK')}")
    if cat_data.get('is_dead'):
        lines.append("THIS CAT IS DEAD — draw as a ghost or spirit")
    if cat_data.get('is_retired'):
        lines.append("RETIRED: this cat has adventured and retired")
    lines.append(f"STAT FOCUS: {cat_data.get('stat_focus', 'none')}")
    if cat_data.get('breed') and cat_data['breed'] != 'None':
        lines.append(f"BREED: {cat_data['breed']}")
    if cat_data.get('age_days'):
        lines.append(f"AGE: {cat_data['age_days']} days")
    if cat_data.get('birth_defect_passives'):
        lines.append(f"BIRTH DEFECTS: {', '.join(cat_data['birth_defect_passives'])}")

    # Stats
    stats = cat_data.get("stats", {})
    if stats:
        stat_parts = []
        for key in ['STR', 'DEX', 'CON', 'INT', 'SPD', 'CHA', 'LCK']:
            s = stats.get(key, {})
            if s:
                eff = s.get('effective', 0)
                base = s.get('base', 0)
                bonus = s.get('bonus', 0)
                extra = s.get('extra', 0)
                mod = ""
                if bonus: mod += f" +{bonus}bonus"
                if extra: mod += f" {'+' if extra > 0 else ''}{extra}injury"
                stat_parts.append(f"{key}={eff} (base {base}{mod})")
        lines.append(f"STATS: {', '.join(stat_parts)}")

    # Abilities with descriptions
    abilities = cat_data.get("abilities_rich", [])
    if abilities:
        ab_parts = []
        for a in abilities:
            if isinstance(a, dict):
                ab_parts.append(f"  - {a.get('key', '')} \"{a.get('name', '')}\" — {a.get('desc', 'no description')}")
            else:
                ab_parts.append(f"  - {a}")
        lines.append("ABILITIES:\n" + "\n".join(ab_parts))

    # Passives with descriptions
    passives = cat_data.get("passives_rich", [])
    if passives:
        pa_parts = []
        for p in passives:
            if isinstance(p, dict):
                pa_parts.append(f"  - {p.get('key', '')} \"{p.get('name', '')}\" — {p.get('desc', 'no description')}")
            else:
                pa_parts.append(f"  - {p}")
        lines.append("PASSIVES:\n" + "\n".join(pa_parts))

    # Items with descriptions
    items = cat_data.get("items_rich", [])
    if items:
        it_parts = []
        for i in items:
            if isinstance(i, dict):
                it_parts.append(f"  - {i.get('key', '')} \"{i.get('name', '')}\" — {i.get('desc', 'no description')}")
            else:
                it_parts.append(f"  - {i}")
        lines.append("ITEMS:\n" + "\n".join(it_parts))

    # Mutations
    mutations = cat_data.get("mutations", [])
    if mutations:
        mu_parts = []
        for m in mutations:
            if isinstance(m, dict):
                defect = " [BIRTH DEFECT]" if m.get("is_defect") else ""
                mu_parts.append(f"  - {m.get('part', '')} ({m.get('part_ru', '')}): {m.get('desc', 'unknown mutation')}{defect}")
            else:
                mu_parts.append(f"  - {m}")
        lines.append("MUTATIONS:\n" + "\n".join(mu_parts))

    return "\n".join(lines)


def generate_visual_prompt(cat_summary: dict) -> str:
    """Use Gemini Flash to generate a detailed visual prompt from cat data.

    Args:
        cat_summary: dict from build_cat_summary_ru() with rich ability/passive/item data

    Returns:
        A detailed visual prompt string for image generation
    """
    if not GEMINI_API_KEY:
        return None

    # Add class_en explicitly if not present
    cat_data = dict(cat_summary)
    if "class_en" not in cat_data:
        cat_data["class_en"] = cat_data.get("class_en", cat_data.get("class", "Colorless"))
    if "class_ru" not in cat_data:
        cat_data["class_ru"] = cat_data.get("class", "")

    data_text = _build_cat_data_text(cat_data)

    user_prompt = f"""Generate a detailed visual image prompt for this Mewgenics cat character.
Transform ALL the game data below into vivid visual descriptions. Think about what each ability, passive, item, and mutation would LOOK like on the cat.

{data_text}

Write the image generation prompt now:"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=PROMPT_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=600,
                temperature=0.8,
                top_p=0.9,
            ),
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Prompt writer error: {e}")

    return None
