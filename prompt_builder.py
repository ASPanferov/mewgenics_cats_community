"""Build image generation prompts from cat data in Edmund McMillen's Mewgenics style."""

from cat_parser import (CatData, CLASS_RU, STAT_LABELS, STAT_LABELS_RU, PART_NAME_RU, PART_NAME_EN,
                        STAT_FOCUS_RU, STAT_FOCUS_EN,
                        _BIRTH_DEFECT_FRAME_THRESHOLD, BIRTH_DEFECT_PASSIVES)
from game_descriptions import game_desc

# === CORE STYLE ===
MCMILLEN_STYLE = (
    "In the style of Edmund McMillen's Mewgenics game art: "
    "hand-drawn grotesque-cute cartoon cat, thick black outlines, "
    "exaggerated proportions, bug-eyed with huge glossy tearful eyes, "
    "lumpy misshapen body, visible stitches and imperfections, "
    "simultaneously adorable and deeply unsettling, "
    "Newgrounds Flash animation aesthetic, dark humor undertones, "
    "like a cursed children's book illustration. "
    "Soft pale sickly color palette with pops of visceral red and sickly green. "
    "Simple messy background with dark vignette edges. "
    "IMPORTANT: Draw exactly ONE single cat character as the main subject. "
    "Do NOT draw two identical cats or duplicate the cat. "
    "Additional small companion creatures (familiars, ghosts, insects) are allowed "
    "only if the cat's abilities explicitly summon them. "
    "NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS, NO LABELS on the image. "
    "Pure illustration only. Express everything through visual elements, "
    "body language, colors, effects, and accessories — never through text or symbols."
)

# Class -> McMillen-style visual description
CLASS_VISUAL = {
    "Fighter": (
        "muscular scrappy brawler cat with tiny angry eyes, oversized paws with chipped claws, "
        "covered in band-aids and battle scars, missing a chunk of ear, flexing comically, "
        "wearing a tattered collar with spikes, veins popping on forehead"
    ),
    "Tank": (
        "absurdly fat round blob-shaped cat barely standing on tiny legs, "
        "covered in dents and bruises like a punching bag, thick leathery skin showing through patchy fur, "
        "drooling slightly, has a vacant but determined stare, wears a bucket on head as helmet"
    ),
    "Hunter": (
        "scrawny feral-looking cat with one eye bigger than the other, "
        "holding a crudely made bow with an arrow, crouching low like a gremlin, "
        "matted fur with twigs and leaves stuck in it, has a dead bird hanging from collar, "
        "long crooked tail used as a third arm"
    ),
    "Mage": (
        "frail emaciated cat with enormous swirling hypnotic eyes, "
        "floating slightly off the ground with paws curled, "
        "crackles of unstable magical energy leak from ears and mouth, "
        "wears an oversized wizard hat that covers half its face, "
        "fur stands on end from static, visibly vibrating with arcane power"
    ),
    "Medic": (
        "chubby wholesome-looking cat with a creepy permanent smile and too-wide eyes, "
        "wears a tiny nurse hat with a blood-stained cross, "
        "carries a comically large syringe dripping mysterious fluid, "
        "has bandages wrapped around its own body, one paw is a rubber glove, "
        "surrounded by floating pills and medicine bottles"
    ),
    "Necromancer": (
        "gaunt skeletal cat with sunken hollow eye sockets glowing sickly green, "
        "patches of fur missing revealing grey skin underneath, "
        "surrounded by tiny floating ghost kittens, bones poking through fur, "
        "wears a tattered dark robe, maggots crawling in ear, "
        "sits atop a pile of tiny skulls, dripping ectoplasm"
    ),
    "Druid": (
        "mossy overgrown cat with mushrooms and flowers sprouting from its back, "
        "one eye is a blooming flower, bark-like skin patches, "
        "roots growing out of paws into the ground, a tiny bird nests in its head, "
        "surrounded by buzzing insects and crawling worms, "
        "looks peaceful but deeply unsettling like a rotting log come alive"
    ),
    "Thief": (
        "sneaky hunched cat with shifty beady eyes darting sideways, "
        "wearing a tiny black mask and striped burglar outfit, "
        "unnaturally long nimble fingers on each paw, "
        "carrying stolen items bulging from pockets, one gold tooth, "
        "has a long shadow that doesn't match its body shape"
    ),
    "Tinkerer": (
        "cat covered in mechanical parts and duct tape, one eye replaced with a monocle gear, "
        "welding goggles on forehead, tiny robot companion perched on shoulder, "
        "wires and springs poking out of fur, oil-stained paws, "
        "holds a sparking wrench, tail is a mechanical appendage with a claw"
    ),
    "Colorless": (
        "plain unassuming cat with big sad worried eyes, "
        "slightly disheveled ordinary appearance but with an uncanny quality, "
        "like it knows something terrible you don't, "
        "clutching its own tail nervously, one ear slightly bent"
    ),
    "Monk": (
        "bald cat with prayer beads around neck, serene but unsettling closed-eye smile, "
        "sits in meditation pose floating slightly, visible chi aura, "
        "extremely muscular arms but tiny delicate legs"
    ),
    "Jester": (
        "wild manic grinning cat with mismatched eyes (one huge one tiny), "
        "wearing a torn jester hat with bells, face painted in smeared makeup, "
        "tongue permanently sticking out sideways, doing a bizarre dance pose"
    ),
    "Psychic": (
        "hairless wrinkly cat with an enormous throbbing brain visible through translucent skull, "
        "third eye on forehead glowing purple, objects floating around it, "
        "nosebleed from psychic strain, thin trembling body, "
        "stares directly at you with unsettling intelligence"
    ),
}

# Class -> dominant color
CLASS_COLOR = {
    "Fighter": "dominant red-orange fur coloring",
    "Tank": "dominant orange fur coloring",
    "Hunter": "dominant green fur coloring",
    "Mage": "dominant soft light purple/lavender fur coloring",
    "Medic": "dominant white/pale cream fur coloring",
    "Necromancer": "dominant black/dark grey fur coloring with sickly green accents",
    "Druid": "dominant earthy brown-green fur coloring",
    "Thief": "dominant pale yellow/cream fur coloring",
    "Tinkerer": "dominant lime green fur coloring",
    "Colorless": "muted grey-beige fur coloring",
    "Monk": "dominant golden-tan fur coloring",
    "Jester": "multicolored patchwork fur",
    "Psychic": "dominant pale purple/pink hairless skin",
    "Butcher": "dominant blood red fur coloring",
}

# Ability/passive -> grotesque McMillen visual effects
ABILITY_VISUALS = {
    "Fireball": "paws engulfed in greasy flames, singed whiskers, charred fur patches",
    "LightningPaws": "crackling electricity arcing between claws, fur standing straight up, electrocuted look",
    "ChainLightning": "body acting as a lightning rod, sparks shooting from eyes and ears",
    "FreezeRay": "half-frozen with icicles hanging from whiskers and chin, blue-tinged frostbitten skin",
    "IceSurge": "encrusted in ice crystals, breath visible as frost cloud",
    "Blizzard": "covered in snow like a sad snowman, shivering violently",
    "BurningPaws": "paw-prints leave scorched marks, tips of fur smoldering",
    "WindSlash": "fur being violently blown in impossible directions, razor wind cuts visible",
    "HolyMantel": "disturbing angelic halo hovering crookedly, blinding golden glow from within",
    "HolyWeapon": "claws replaced with golden blades of light, too bright to look at directly",
    "GuardianAngel": "tiny creepy cherub kitten floating above protectively with dead eyes",
    "HallowedGround": "standing in a pool of eerie golden light on cracked holy ground",
    "WrathOfGod": "lightning bolt from above striking nearby, righteous fury in bloodshot eyes",
    "DivineProtection": "surrounded by a bubble of holy light, trapped or protected unclear",
    "SoulReap": "ghostly cat souls being pulled from the ground toward its mouth",
    "Pestilence": "surrounded by clouds of flies, pustules and boils on skin, sickly green drool",
    "BloodRain": "soaked in blood rain from above, matted crimson fur, unbothered expression",
    "MaggotArmy": "maggots crawling out of fur and orifices, disturbing symbiotic relationship",
    "BloodGeyser": "standing over a geyser of dark blood erupting from the ground",
    "Vampirism": "elongated fangs dripping blood, pale corpse-like fur, bat-wing ear shape",
    "Earthquake": "cracked ground radiating from stomping paw, debris floating",
    "BellyFlop": "grotesquely distended belly dragging on ground, stretch marks visible",
    "WetHairball": "sopping wet matted disgusting fur clumps, puddle of gross fluid around it",
    "Berserk": "bloodshot bulging eyes, foaming mouth, veins visible through skin, feral rage",
    "Sunburn": "painfully red peeling skin showing through thin fur, miserable expression",
    "HotBlooded": "literally steaming, red-hot skin visible through fur, angry sweat drops",
    "BloodLust": "dilated pupils fixed on prey, blood-smeared mouth, twitching with hunger",
    "BloodFrenzy": "covered in blood splatter, wild unhinged grin, claws dripping",
    "ToadStyle": "grotesquely puffed up like a bullfrog, sitting in a squat, croaking pose",
    "Dwarfism": "comically tiny but proportionally wrong, huge head on tiny body",
    "Scatological": "surrounded by filth, brown-stained paws, flies circling, proud expression",
    "Tourettes": "involuntary twitching, symbols coming from mouth, chaotic energy lines",
    "Infested": "scratching furiously, fleas visible as tiny dots, raw red patches in fur",
    "Parasitic": "visible worms under translucent skin, sunken sickly eyes, gaunt frame",
    "SpiderEgg": "spider egg sac bulging from back, tiny spiders hatching from fur",
    "DeathIncarnate": "half-skeletal, flesh peeling away revealing bones, one eye is just a socket",
    "Overpowered": "absurdly jacked muscles bulging through skin, veins like garden hoses",
    "ThickSkull": "comically oversized rock-hard head, tiny brain visible through skull cracks",
    "DumbMuscle": "huge muscles everywhere but vacant drooling expression, flexing stupidly",
    "Micronaps": "falling asleep mid-action, drool puddle, Z's floating from head",
    "SavantSyndrome": "enormous brain pushing skull open, one eye magnified, scattered genius scribblings floating",
    "PinsAndNeedles": "quills and needles growing out of fur like a porcupine mutation",
    "GravityFalls": "floating upward with panicked expression, fur and objects drifting up",
    "PTSD": "thousand-yard stare, trembling, flashback images in dilated pupils",
    "Wrestlemaniac": "wearing a tiny luchador mask, flexing pose, body oil sheen",
    "EatingDisorder": "impossibly thin or grotesquely bloated, complicated relationship with food visible",
}

VOICE_VISUALS = {
    "male": "male cat with stocky lumpy build",
    "female": "female cat with scraggly angular build",
    "spidercat": "horrifying spider-cat hybrid with eight mismatched legs, multiple eyes on face, web-spinning from behind",
}

ITEM_VISUALS = {
    "DryBoneHat": "wearing a hat crudely assembled from yellowed bones and sinew",
    "DeadMask": "wearing a disturbing death mask with hollowed eyes",
    "SnakeskinHat": "wearing a hat made from real snake with its dead eyes still open",
    "BrickHat": "a literal brick balanced on head with a dent in skull beneath",
    "MedicHat": "tiny blood-splattered nurse cap",
    "FeatheredCap": "wearing a ratty cap with one sad bent feather",
    "MuertosMask": "face painted as Dia de los Muertos sugar skull, cracking at edges",
    "NinjaBandana": "wearing a torn dirty ninja headband over one eye",
    "CactusHat": "a living cactus growing from head, needles poking into scalp",
    "Glasses": "wearing cracked taped-together oversized glasses",
    "Binoculars": "heavy binoculars dragging neck down",
    "SurvivalistMask": "wearing a grimy dented gas mask, breathing tubes dangling",
    "HumanFleshHat": "wearing a horrifying hat made of stitched human skin, most disturbing item",
    "FecalMask": "face covered in a mask of literal dried feces, somehow proud of it",
    "HorseBlinders": "wearing horse blinders made from cardboard, peripheral vision gone",
    "AmoebaHat": "translucent pulsating blob creature sitting on head like a parasite",
    "CatHideArmor": "wearing armor made from another cat's hide, deeply disturbing",
    "LeatherArmor": "crude stitched leather vest, barely holding together",
    "CardboardArmor": "wearing a cardboard box as armor with 'ARMOR' written in crayon",
    "BarbedHat": "barbed wire wrapped around head, small blood drops seeping",
    "VibratingSkull": "a tiny skull chattering and vibrating on a string",
    "StoneHelmet": "a heavy stone bowl jammed on head, neck compressed",
    "MinerMask": "dirty miner's helmet with a flickering dying headlamp",
    "FlowerNecklace": "wilting flower necklace, some flowers already dead and brown",
    "Bling": "gaudy oversized gold chains with a dollar sign pendant",
    "ExtraSetOfEyes": "a second pair of eyes grafted onto forehead, blinking independently",
    "NailBoard": "dragging a nail-studded board like a weapon or teddy bear",
    "FuryDice": "flaming dice orbiting head chaotically",
    "LuckyToe": "a severed toe on a string around neck, questionably lucky",
    "Neverstone": "pulsating mysterious stone fused into forehead flesh",
    "WaterBottle": "clutching a half-empty dirty water bottle desperately",
    "KidneyStones": "wincing in visible pain, sweat drops, legs crossed",
    "CarBattery": "a car battery crudely strapped to back with jumper cables",
    "Scrubs": "wearing stained surgical scrubs several sizes too big",
    "RubberBand": "rubber bands wrapped tightly around body cutting into flesh",
    "MysteriousEye": "a third eye on forehead that looks in a different direction",
    "WeirdEgg": "cradling a pulsating alien-like egg that might hatch something terrible",
    "IceCube": "partially frozen in an ice cube, only head and one paw free",
    "SpiderEgg": "a pulsating spider egg sac glued to back, about to burst",
}


# ===================== STAT ANALYSIS =====================

def _analyze_stats(cat: CatData) -> str:
    """Analyze stats relative to each other and generate visual body description.

    Stats are compared relative to each other to determine the cat's
    physical appearance. High stat = exaggerated feature, low stat = atrophied.
    """
    eff = cat.stats.effective
    if not any(eff):
        return ""

    # stat indices: 0=STR, 1=DEX, 2=CON, 3=INT, 4=SPD, 5=CHA, 6=LCK
    avg = sum(eff) / 7
    if avg == 0:
        avg = 1

    # Calculate relative strength of each stat (ratio to average)
    rel = [e / avg for e in eff]

    descriptions = []

    # STR (Strength) -> body musculature
    if rel[0] >= 1.4:
        descriptions.append("extremely muscular bulging body with veins showing, oversized powerful paws")
    elif rel[0] >= 1.15:
        descriptions.append("noticeably strong muscular build, thick sturdy legs")
    elif rel[0] <= 0.6:
        descriptions.append("scrawny weak-looking noodle arms, frail thin body")
    elif rel[0] <= 0.8:
        descriptions.append("somewhat thin and weak-looking limbs")

    # DEX (Dexterity) -> agility, grace
    if rel[1] >= 1.4:
        descriptions.append("unnaturally flexible bendy body, long nimble spider-like fingers, acrobatic pose")
    elif rel[1] >= 1.15:
        descriptions.append("lithe and agile body, alert crouching posture")
    elif rel[1] <= 0.6:
        descriptions.append("stiff clumsy body, stumbling awkward stance")

    # CON (Constitution) -> bulk, toughness
    if rel[2] >= 1.4:
        descriptions.append("absurdly thick dense body like a brick, covered in scars and calluses, battle-hardened hide")
    elif rel[2] >= 1.15:
        descriptions.append("sturdy thick-skinned body, resilient and tough-looking")
    elif rel[2] <= 0.6:
        descriptions.append("fragile paper-thin body, visible ribs, sickly pale, looks like it might break")
    elif rel[2] <= 0.8:
        descriptions.append("somewhat frail and delicate frame")

    # INT (Intelligence) -> head/brain size
    if rel[3] >= 1.4:
        descriptions.append("comically enormous oversized head with bulging brain, tiny reading glasses, "
                          "scribbles and formulas floating around")
    elif rel[3] >= 1.15:
        descriptions.append("slightly larger head than normal, knowing intelligent eyes")
    elif rel[3] <= 0.6:
        descriptions.append("tiny pinhead with vacant empty stare, drooling, mouth agape")
    elif rel[3] <= 0.8:
        descriptions.append("slightly dull confused expression")

    # SPD (Speed) -> body shape, legs
    if rel[4] >= 1.4:
        descriptions.append("long powerful spring-loaded legs, blur lines behind body, streamlined shape, "
                          "ears pinned back from speed")
    elif rel[4] >= 1.15:
        descriptions.append("quick-looking lean body, long legs, alert ears perked forward")
    elif rel[4] <= 0.6:
        descriptions.append("sluggish blob barely able to move, stubby tiny legs, dragging belly on ground")
    elif rel[4] <= 0.8:
        descriptions.append("somewhat slow-looking, short stumpy legs")

    # CHA (Charisma) -> appearance appeal
    if rel[5] >= 1.4:
        descriptions.append("inexplicably charming despite being grotesque, sparkling eyes with heart pupils, "
                          "tiny crown or bowtie, other cats swooning nearby")
    elif rel[5] >= 1.15:
        descriptions.append("oddly endearing face, slightly less disgusting than usual")
    elif rel[5] <= 0.6:
        descriptions.append("hideously ugly even by cat standards, other cats recoiling in background, "
                          "face only a mother could love")
    elif rel[5] <= 0.8:
        descriptions.append("unremarkable bland face, forgettable")

    # LCK (Luck) -> lucky charms, environment
    if rel[6] >= 1.4:
        descriptions.append("surrounded by lucky clovers, horseshoes, and shimmering green lucky aura, "
                          "four-leaf clover growing from ear")
    elif rel[6] >= 1.15:
        descriptions.append("faint green shimmer of luck, a four-leaf clover nearby")
    elif rel[6] <= 0.6:
        descriptions.append("dark rain cloud above head, stepped in something gross, broken mirror pieces nearby, "
                          "unlucky black cat vibes")
    elif rel[6] <= 0.8:
        descriptions.append("slightly unlucky aura, a crack in the ground near paw")

    # Injured status
    if cat.status == "Injured":
        descriptions.append("visibly injured and in pain, bandages and fresh wounds, "
                          "limping or wincing, bruises visible through fur")
    elif cat.status == "Dead":
        descriptions.append("ghost-like translucent form, X-shaped eyes, floating above a tiny grave, "
                          "crooked angel halo or tiny devil horns")

    return ". ".join(descriptions)


def _build_ability_context(cat: CatData) -> str:
    """Build visual context from abilities with game descriptions.

    Includes both hardcoded visual effects AND game descriptions so the model
    understands what to draw. Text descriptions help the model — the no-text
    rule in MCMILLEN_STYLE prevents it from rendering words on the image.
    """
    parts = []

    for ability in cat.abilities[:4]:
        visual = ABILITY_VISUALS.get(ability)
        desc_info = game_desc.get_ability(ability)
        if visual and desc_info:
            parts.append(f"{desc_info[0]}: {visual}")
        elif visual:
            parts.append(visual)
        elif desc_info:
            parts.append(f"ability '{desc_info[0]}' ({desc_info[1][:120]}) — "
                       "show this visually on the cat's body or surroundings")

    for passive in cat.passives[:3]:
        visual = ABILITY_VISUALS.get(passive)
        desc_info = game_desc.get_passive(passive)
        if visual and desc_info:
            parts.append(f"{desc_info[0]}: {visual}")
        elif visual:
            parts.append(visual)
        elif desc_info:
            parts.append(f"passive trait '{desc_info[0]}' ({desc_info[1][:120]}) — "
                       "show as a subtle visual detail on the cat")

    return ". ".join(parts)


def _build_item_context(cat: CatData) -> str:
    """Build item visual descriptions with game context."""
    parts = []
    for item in cat.items[:3]:
        visual = None
        for item_key, item_visual in ITEM_VISUALS.items():
            if item.lower().startswith(item_key[:6].lower()) or item_key.lower().startswith(item[:6].lower()):
                visual = item_visual
                break

        desc_info = game_desc.get_item(item)
        if visual and desc_info:
            parts.append(f"{desc_info[0]}: {visual}")
        elif visual:
            parts.append(visual)
        elif desc_info:
            parts.append(f"equipped '{desc_info[0]}' ({desc_info[1][:100]}) — "
                       "show as a grotesque accessory or held object")
        else:
            parts.append("a strange grotesque accessory strapped to body")
    return ". ".join(parts)


def _build_mutation_context(cat: CatData) -> str:
    """Build visual context from mutations (body part frame mutations)."""
    if not cat.mutations:
        return ""

    parts = []
    for part_name, frame in cat.mutations.items():
        desc = game_desc.get_mutation(part_name, frame)
        is_defect = frame >= _BIRTH_DEFECT_FRAME_THRESHOLD
        part_ru = PART_NAME_RU.get(part_name, part_name)

        if desc:
            prefix = "birth defect" if is_defect else "mutation"
            parts.append(f"{prefix} on {part_name} ({part_ru}): {desc} — "
                        "show as a visible grotesque bodily deformation")
        else:
            if is_defect:
                parts.append(f"birth defect on {part_name}: visibly deformed, "
                           "wrong-looking, unsettling abnormality")
            else:
                parts.append(f"mutation on {part_name}: mutated, unusual, "
                           "grotesquely altered body part")

    return ". ".join(parts)


def build_prompt(cat: CatData) -> str:
    """Build a detailed image generation prompt in McMillen's Mewgenics style.

    The prompt analyzes:
    1. Core art style (McMillen grotesque-cute)
    2. Gender/body type from voice
    3. Class color and visual archetype
    4. Stats relative to each other -> body proportions & features
    5. Abilities with game descriptions -> visual power effects
    6. Passives with game descriptions -> subtle trait indicators
    7. Items with descriptions -> grotesque accessories
    8. Injury/death status
    """
    parts = []

    # 1. Core style
    parts.append(MCMILLEN_STYLE)

    # 2. Gender/body
    for prefix, desc in VOICE_VISUALS.items():
        if cat.voice.startswith(prefix):
            parts.append(desc)
            break

    # 3. Class color + archetype
    color = CLASS_COLOR.get(cat.cat_class, CLASS_COLOR["Colorless"])
    parts.append(color)

    cls_visual = CLASS_VISUAL.get(cat.cat_class, CLASS_VISUAL["Colorless"])
    parts.append(cls_visual)

    # 4. Stat-based body description
    stat_desc = _analyze_stats(cat)
    if stat_desc:
        parts.append(stat_desc)

    # 5-6. Abilities and passives as visual effects
    ability_ctx = _build_ability_context(cat)
    if ability_ctx:
        parts.append(ability_ctx)

    # 7. Items as visual accessories
    item_ctx = _build_item_context(cat)
    if item_ctx:
        parts.append(item_ctx)

    # 8. Mutations as body deformations
    mutation_ctx = _build_mutation_context(cat)
    if mutation_ctx:
        parts.append(mutation_ctx)

    # 9. Name
    if cat.name and not cat.name.startswith("Кот #"):
        parts.append(f'This cat is named "{cat.name}"')

    return ". ".join(parts)


def _translate_focus(raw_focus: str, lang: str) -> str:
    """Translate stat_focus raw key (e.g. 'str', 'poisoned') to display string."""
    if not raw_focus:
        return "none" if lang == 'en' else "нет"
    focus_map = STAT_FOCUS_EN if lang == 'en' else STAT_FOCUS_RU
    # raw_focus is either a raw key ('str', 'poisoned') or legacy Russian value
    if raw_focus in focus_map:
        return focus_map[raw_focus]
    # Legacy: raw_focus might already be a Russian string from old DB data
    # Reverse-lookup from Russian to get the key, then translate
    reverse_ru = {v: k for k, v in STAT_FOCUS_RU.items()}
    key = reverse_ru.get(raw_focus)
    if key:
        return focus_map.get(key, raw_focus)
    return raw_focus


def build_cat_summary(cat: CatData, lang: str = 'ru') -> dict:
    """Build a localized summary of cat data for the UI."""
    class_ru = CLASS_RU.get(cat.cat_class, cat.cat_class)

    stats_dict = {}
    for i, (label, label_ru) in enumerate(zip(STAT_LABELS, STAT_LABELS_RU)):
        stats_dict[label] = {
            "label_en": label,
            "label_ru": label_ru,
            "base": cat.stats.base[i],
            "bonus": cat.stats.bonus[i],
            "extra": cat.stats.extra[i],
            "effective": cat.stats.effective[i],
        }

    # Build mutations list for UI
    mutations_list = []
    for part_name, frame in cat.mutations.items():
        part_ru = PART_NAME_RU.get(part_name, part_name)
        part_en = PART_NAME_EN.get(part_name, part_name)
        desc = game_desc.get_mutation(part_name, frame, lang=lang)
        is_defect = frame >= _BIRTH_DEFECT_FRAME_THRESHOLD
        mutations_list.append({
            "part": part_name,
            "part_ru": part_ru,
            "part_en": part_en,
            "frame": frame,
            "desc": desc or "",
            "is_defect": is_defect,
        })

    # Build rich ability/passive/item info with names + descriptions
    abilities_rich = []
    for a in cat.abilities:
        info = game_desc.get_ability(a, lang=lang)
        name = (info[0] if info and info[0] else '') or a
        abilities_rich.append({
            "key": a,
            "name": name,
            "desc": info[1] if info else "",
        })

    passives_rich = []
    for p in cat.passives:
        info = game_desc.get_passive(p, lang=lang)
        name = (info[0] if info and info[0] else '') or p
        passives_rich.append({
            "key": p,
            "name": name,
            "desc": info[1] if info else "",
        })

    items_rich = []
    for it in cat.items:
        info = game_desc.get_item(it, lang=lang)
        name = (info[0] if info and info[0] else '') or it
        items_rich.append({
            "key": it,
            "name": name,
            "desc": info[1] if info else "",
        })

    # Detect birth defect passives
    birth_defect_passives = [a for a in cat.abilities if a in BIRTH_DEFECT_PASSIVES]
    for p in cat.passives:
        if p in BIRTH_DEFECT_PASSIVES and p not in birth_defect_passives:
            birth_defect_passives.append(p)

    # Gender localized
    gender_map = {
        'en': {'кот': 'male', 'кошка': 'female', 'кот-паук': 'spider-cat'},
        'ru': {'кот': 'кот', 'кошка': 'кошка', 'кот-паук': 'кот-паук'},
    }
    gender_display = gender_map.get(lang, gender_map['en']).get(cat.gender, cat.gender or ('unknown' if lang == 'en' else 'неизвестно'))

    return {
        "id": cat.id,
        "name": cat.name,
        "class": class_ru if lang == 'ru' else cat.cat_class,
        "class_en": cat.cat_class,
        "class_ru": class_ru,
        "gender": gender_display,
        "gender_code": cat.gender_code,
        "voice": cat.voice or "",
        "stat_focus": _translate_focus(cat.stat_focus, lang),
        "status": cat.status,
        "is_dead": cat.is_dead,
        "is_retired": cat.is_retired,
        "is_donated": cat.is_donated,
        "breed": getattr(cat, 'breed', ''),
        "birth_day": cat.birth_day,
        "age_days": cat.age_days,
        "parent_keys": getattr(cat, 'parent_keys', []),
        "inbreeding_level": getattr(cat, 'inbreeding_level', 0),
        "birth_defect_passives": birth_defect_passives,
        "abilities": [a["name"] for a in abilities_rich],
        "passives": [p["name"] for p in passives_rich],
        "items": [i["name"] for i in items_rich],
        "abilities_rich": abilities_rich,
        "passives_rich": passives_rich,
        "items_rich": items_rich,
        "mutations": mutations_list,
        "stats": stats_dict,
    }


# Backward compatibility alias
def build_cat_summary_ru(cat: CatData) -> dict:
    return build_cat_summary(cat, lang='ru')
