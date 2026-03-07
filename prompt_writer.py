"""AI prompt writer: uses Gemini Flash to generate detailed visual prompts from raw cat data."""

import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PROMPT_MODEL = "gemini-2.5-flash"

# Settings keys in DB
SETTING_SYSTEM_INSTRUCTION = "prompt_system_instruction"
SETTING_USER_PROMPT_TEMPLATE = "prompt_user_template"
SETTING_PROMPT_MODEL = "prompt_model"
SETTING_IMAGE_MODEL = "image_model"

DEFAULT_SYSTEM_INSTRUCTION = """\
You are a master visual prompt writer for AI image generation. You will receive structured game data about a cat character from the game Mewgenics by Edmund McMillen. Your job: transform ALL that data into a single, vivid, highly detailed image generation prompt in English.

═══════════════════════════════════════════════
ART STYLE: Edmund McMillen (Mewgenics / The Binding of Isaac / Super Meat Boy)
═══════════════════════════════════════════════
- Hand-drawn grotesque-cute cartoon style with thick black outlines
- Exaggerated proportions, bug-eyed with HUGE glossy tearful eyes
- Lumpy misshapen bodies, visible stitches, imperfections, asymmetry
- Simultaneously adorable and deeply unsettling — "cursed children's book illustration"
- Newgrounds Flash animation aesthetic, dark humor undertones
- Soft pale sickly color palette with pops of visceral red and sickly green
- Simple messy background with dark vignette edges, subtle environmental storytelling
- Characters look like handmade felt/clay/paper craft that came to life wrong

MANDATORY RULES:
1. Output ONLY the image prompt — no explanations, no markdown, no prefixes, no quotes
2. Draw exactly ONE single cat character as the main subject
3. NEVER include text, words, letters, numbers, or labels in the image
4. Express EVERYTHING through visual elements, body language, colors, effects, accessories
5. Combine ALL character traits into ONE coherent visual composition
6. Keep the prompt between 150-350 words — dense and visual, no filler
7. Write in English only
8. Start with the art style description, then the cat's body, then details
9. Prioritize the most visually distinctive features — coherence over completeness

═══════════════════════════════════════════════
CLASS → COLOR + ARCHETYPE
═══════════════════════════════════════════════
Each class has a dominant fur color and a visual archetype. Use these as the foundation:

FIGHTER (red-orange): muscular scrappy brawler, tiny angry eyes, oversized paws with chipped claws, band-aids and battle scars, missing ear chunk, tattered spiked collar
TANK (orange): absurdly fat round blob on tiny legs, dents and bruises like a punching bag, thick leathery skin, vacant determined stare, bucket helmet
HUNTER (green): scrawny feral gremlin, one eye bigger than other, matted fur with twigs, dead bird on collar, crouching low, crooked prehensile tail
MAGE (lavender/purple): frail emaciated, enormous swirling hypnotic eyes, floating off ground, arcane energy from ears and mouth, oversized wizard hat, fur on end from static
MEDIC (white/cream): chubby with creepy permanent smile and too-wide eyes, tiny nurse hat with blood-stained cross, comically large syringe, bandages everywhere
NECROMANCER (black/dark grey + sickly green): gaunt skeletal, hollow glowing green eye sockets, floating ghost kittens, bones poking through fur, tattered dark robe, maggots
DRUID (earthy brown-green): mossy overgrown, mushrooms and flowers sprouting from back, one eye is a blooming flower, bark-skin patches, roots from paws, bird nesting in head
THIEF (pale yellow): sneaky hunched, shifty beady eyes, tiny black mask, striped burglar outfit, unnaturally long nimble fingers, stolen items bulging from pockets, gold tooth
TINKERER (lime green): covered in mechanical parts and duct tape, monocle gear eye, welding goggles, robot companion on shoulder, wires and springs from fur, sparking wrench
COLORLESS (grey-beige): plain unassuming with big sad worried eyes, uncanny quality, clutching own tail nervously, slightly bent ear
MONK (golden-tan): bald with prayer beads, serene unsettling closed-eye smile, meditation pose floating, chi aura, muscular arms but tiny legs
PSYCHIC (pale purple/pink): hairless wrinkly, enormous throbbing brain visible through translucent skull, third eye glowing purple, objects floating, nosebleed, stares at viewer
JESTER (multicolored patchwork): wild manic grin, mismatched eyes (one huge one tiny), torn jester hat with bells, smeared makeup, tongue out sideways, bizarre dance pose
BUTCHER (blood red): massive hulking frame, blood-soaked apron, cleaver in one paw, dead-eyed stare, chunks of meat hanging from belt

═══════════════════════════════════════════════
STATS → BODY PROPORTIONS (relative to each other)
═══════════════════════════════════════════════
Compare stats to each other. High stat = exaggerated feature, low stat = atrophied:

STR (Strength): HIGH = extremely muscular bulging body, veins showing, oversized paws. LOW = scrawny noodle arms, frail thin body
DEX (Dexterity): HIGH = unnaturally flexible bendy, long spider-like fingers, acrobatic pose. LOW = stiff clumsy, stumbling stance
CON (Constitution): HIGH = absurdly thick dense body like a brick, scars and calluses. LOW = fragile paper-thin, visible ribs, sickly
INT (Intelligence): HIGH = comically enormous head, bulging brain, tiny glasses, formulas floating. LOW = tiny pinhead, vacant drool, mouth agape
SPD (Speed): HIGH = long spring-loaded legs, blur lines, streamlined, ears pinned back. LOW = sluggish blob, stubby legs, belly dragging
CHA (Charisma): HIGH = sparkling heart-pupil eyes, tiny crown/bowtie, cats swooning nearby. LOW = hideously ugly, other cats recoiling
LCK (Luck): HIGH = surrounded by clovers and horseshoes, green lucky shimmer. LOW = dark rain cloud above, broken mirror nearby, stepped in something

═══════════════════════════════════════════════
ABILITIES & PASSIVES → VISUAL EFFECTS
═══════════════════════════════════════════════
Transform each ability/passive into a VISIBLE effect on or around the cat. Some known mappings:

Fire abilities → paws engulfed in greasy flames, singed whiskers, charred fur
Lightning → electricity arcing between claws, fur standing up, electrocuted look
Ice/Freeze → icicles on whiskers, blue-tinged frostbitten skin, frost breath
Holy → disturbing angelic halo, golden glow, tiny creepy cherub companion
Necromancy → ghostly souls pulled from ground, ectoplasm dripping, zombie familiars
Blood abilities → soaked in blood rain, matted crimson fur, blood geysers
Poison/Pestilence → clouds of flies, pustules and boils, sickly green drool
Vampirism → elongated fangs dripping blood, pale corpse fur, bat-wing ears
Berserk/Rage → bloodshot bulging eyes, foaming mouth, feral rage veins
Summon/Familiar → small companion creature near the cat (describe what it looks like!)
Healing → glowing paws, floating pills and syringes, warm aura
Earth/Nature → cracked ground, debris floating, roots and vines

If an ability SUMMONS something (familiar, creature, undead, etc.) — add a small grotesque companion creature next to the cat. Describe it specifically.

═══════════════════════════════════════════════
ITEMS → GROTESQUE ACCESSORIES
═══════════════════════════════════════════════
Items should be visible on the cat's body as McMillen-style grotesque accessories:

Hats → crude, ill-fitting, made from wrong materials (bones, skin, brick, cactus)
Masks → disturbing, cracked, too-tight, covering wrong parts of face
Armor → cardboard with crayon labels, stitched leather barely holding, cat-hide (disturbing)
Jewelry → gaudy oversized gold chains, wilting flower necklaces, rubber bands cutting into flesh
Eyes/Optics → cracked taped glasses, heavy binoculars dragging neck, extra grafted eyes
Weapons → nail-studded boards, comically large syringes, sparking tools
Mysterious objects → pulsating eggs, vibrating skulls, glowing stones fused into flesh

═══════════════════════════════════════════════
MUTATIONS → BODY DEFORMATIONS
═══════════════════════════════════════════════
Each mutation is on a specific body part. Show it as a grotesque visible deformation:
- Describe WHERE on the body the mutation is (head, legs, tail, ears, eyes, body)
- Birth defects (marked [BIRTH DEFECT]) should look MORE severe, wrong, unsettling
- Multiple mutations stack — the cat becomes increasingly monstrous

═══════════════════════════════════════════════
GENDER & AGE
═══════════════════════════════════════════════
Male (кот): stocky lumpy build, broader jaw
Female (кошка): scraggly angular build, slightly more elegant but still grotesque
Spider-cat (кот-паук): HORRIFYING spider-cat hybrid, eight mismatched legs, multiple eyes, web
Young (< 5 days): tiny kitten proportions, even bigger eyes relative to body
Adult (5-19 days): standard proportions
Old (20+ days): grizzled, sagging skin, wise/tired eyes, gray whiskers

═══════════════════════════════════════════════
PROMPT STRUCTURE
═══════════════════════════════════════════════
Build the prompt in this order:
1. Art style foundation (McMillen grotesque-cute, thick outlines, etc.)
2. Gender/body type + class color + class archetype
3. Stat-based body proportions (what stands out?)
4. Ability visual effects (fire, ice, summons, etc.)
5. Passive visual traits (auras, modifications)
6. Items as accessories
7. Mutations as deformations
8. Overall mood and composition
10. "NO TEXT, NO WORDS, NO LETTERS" reminder at the end

IMPORTANT: Do NOT just list features. WEAVE them into a cohesive scene. The cat should feel like ONE character, not a checklist. Think about how all these elements interact visually."""


def _build_cat_data_text(cat_data: dict) -> str:
    """Format raw cat data into structured text for the prompt writer."""
    lines = []
    lines.append(f"NAME: {cat_data.get('name', 'Unknown')}")

    # Gender
    gender = cat_data.get('gender', 'неизвестно')
    voice = cat_data.get('voice', '')
    if gender == 'кот':
        lines.append("GENDER: Male (кот)")
    elif gender == 'кошка':
        lines.append("GENDER: Female (кошка)")
    elif gender == 'кот-паук':
        lines.append("GENDER: Spider-cat (кот-паук) — hybrid spider-cat horror")
    # Class
    class_en = cat_data.get('class_en', 'Colorless')
    lines.append(f"CLASS: {class_en}")

    # Age
    age = cat_data.get('age_days')
    if age:
        if age < 5:
            age_desc = " (young kitten)"
        elif age >= 20 and cat_data.get('is_retired'):
            age_desc = " (old grizzled cat)"
        else:
            age_desc = " (adult cat)"
        lines.append(f"AGE: {age} days{age_desc}")

    # Breed
    breed = cat_data.get('breed', '')
    if breed and breed != 'None':
        lines.append(f"BREED: {breed}")

    # Stat focus
    focus = cat_data.get('stat_focus', '')
    if focus and focus != 'нет' and focus != 'Нет':
        lines.append(f"STAT FOCUS: {focus}")

    # Birth defects
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
                stat_parts.append(f"{key}={eff}")
        lines.append(f"STATS: {', '.join(stat_parts)}")

        # Highlight extreme stats
        effs = {k: stats[k].get('effective', 0) for k in ['STR', 'DEX', 'CON', 'INT', 'SPD', 'CHA', 'LCK'] if stats.get(k)}
        if effs:
            avg = sum(effs.values()) / len(effs)
            highs = [k for k, v in effs.items() if avg > 0 and v / avg >= 1.3]
            lows = [k for k, v in effs.items() if avg > 0 and v / avg <= 0.7]
            if highs:
                lines.append(f"NOTABLY HIGH: {', '.join(highs)} — exaggerate these body features!")
            if lows:
                lines.append(f"NOTABLY LOW: {', '.join(lows)} — atrophy/shrink these features!")

    # Abilities with descriptions
    abilities = cat_data.get("abilities_rich", [])
    if abilities:
        ab_parts = []
        for a in abilities:
            if isinstance(a, dict):
                key = a.get('key', '')
                name = a.get('name', key)
                desc = a.get('desc', '')
                if desc and desc.strip():
                    ab_parts.append(f"  - {name}: {desc}")
                elif name:
                    ab_parts.append(f"  - {name}")
            else:
                ab_parts.append(f"  - {a}")
        if ab_parts:
            lines.append("ABILITIES (show as visible effects on/around the cat):\n" + "\n".join(ab_parts))

    # Passives with descriptions
    passives = cat_data.get("passives_rich", [])
    if passives:
        pa_parts = []
        for p in passives:
            if isinstance(p, dict):
                key = p.get('key', '')
                name = p.get('name', key)
                desc = p.get('desc', '')
                if desc and desc.strip():
                    pa_parts.append(f"  - {name}: {desc}")
                elif name:
                    pa_parts.append(f"  - {name}")
            else:
                pa_parts.append(f"  - {p}")
        if pa_parts:
            lines.append("PASSIVES (show as subtle persistent visual traits):\n" + "\n".join(pa_parts))

    # Items with descriptions
    items = cat_data.get("items_rich", [])
    if items:
        it_parts = []
        for i in items:
            if isinstance(i, dict):
                key = i.get('key', '')
                name = i.get('name', key)
                desc = i.get('desc', '')
                if desc and desc.strip():
                    it_parts.append(f"  - {name}: {desc}")
                elif name:
                    it_parts.append(f"  - {name}")
            else:
                it_parts.append(f"  - {i}")
        if it_parts:
            lines.append("ITEMS (show as grotesque accessories/equipment):\n" + "\n".join(it_parts))

    # Mutations
    mutations = cat_data.get("mutations", [])
    if mutations:
        mu_parts = []
        for m in mutations:
            if isinstance(m, dict):
                part = m.get('part', '')
                part_ru = m.get('part_ru', '')
                desc = m.get('desc', '')
                defect = " [BIRTH DEFECT — make it look severe and wrong!]" if m.get("is_defect") else ""
                location = f" on {part}" if part else ""
                if desc:
                    mu_parts.append(f"  - Mutation{location}: {desc}{defect}")
                else:
                    mu_parts.append(f"  - Mutation{location}: grotesque deformation{defect}")
            else:
                mu_parts.append(f"  - {m}")
        if mu_parts:
            lines.append("MUTATIONS (visible body deformations):\n" + "\n".join(mu_parts))

    return "\n".join(lines)


DEFAULT_USER_PROMPT_TEMPLATE = """Here is the game data for a Mewgenics cat character. Transform it into a vivid image generation prompt following all the rules in your instructions.

{cat_data}

Write the image generation prompt:"""


def get_system_instruction():
    """Get system instruction from DB or use default."""
    try:
        import db
        val = db.get_setting(SETTING_SYSTEM_INSTRUCTION)
        if val:
            return val
    except Exception:
        pass
    return DEFAULT_SYSTEM_INSTRUCTION


def get_user_prompt_template():
    """Get user prompt template from DB or use default."""
    try:
        import db
        val = db.get_setting(SETTING_USER_PROMPT_TEMPLATE)
        if val:
            return val
    except Exception:
        pass
    return DEFAULT_USER_PROMPT_TEMPLATE


def get_prompt_model():
    """Get prompt writer model from DB or use default."""
    try:
        import db
        val = db.get_setting(SETTING_PROMPT_MODEL)
        if val:
            return val
    except Exception:
        pass
    return PROMPT_MODEL


def get_image_model():
    """Get image generation model from DB or use default."""
    try:
        import db
        val = db.get_setting(SETTING_IMAGE_MODEL)
        if val:
            return val
    except Exception:
        pass
    return "gemini-3.1-flash-image-preview"


def generate_visual_prompt(cat_summary: dict) -> str:
    """Use Gemini Flash to generate a detailed visual prompt from cat data.

    Args:
        cat_summary: dict from build_cat_summary_ru() with rich ability/passive/item data

    Returns:
        A detailed visual prompt string for image generation
    """
    if not GEMINI_API_KEY:
        return None

    cat_data = dict(cat_summary)
    data_text = _build_cat_data_text(cat_data)

    system_instruction = get_system_instruction()
    user_template = get_user_prompt_template()
    model = get_prompt_model()

    user_prompt = user_template.replace("{cat_data}", data_text)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=8000,
                temperature=0.85,
                top_p=0.92,
            ),
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Prompt writer error: {e}")

    return None
