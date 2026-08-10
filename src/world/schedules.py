"""
schedules.py — the individual weekly routines of the Chrysos Heirs.

The world is big and the Heirs are spread across it. Each Heir keeps a weekly
routine — for every day of the Light-Calendar week and every period of the day,
they have a place and an occupation. These routines are *defaults*: the Heir may
deviate of their own free will, but the world between the cities is wide, and
any deviation is paid for in commuting time (see map_data.travel_days).

The result is a livelier, more honest Amphoreus: the Heirs who live and work
together (the Okhema council circle, the scholars of the Grove, the two souls
of Aedes Elysiae) meet often; the rest cross paths only when someone is willing
to spend days on the road.
"""

from typing import Dict, List, Tuple

PERIOD_NAMES: List[str] = [
    "Entry Hour",      # 0 — awakening, morning market, prayers
    "Lucid Hour",      # 1 — mental peak, conversation, scholarship
    "Action Hour",     # 2 — physical labour, exercise, revelry
    "Parting Hour",    # 3 — work ends, farewells, departures
    "Curtain-Fall Hour",  # 4 — rest and sleep
]

# --------------------------------------------------------------------------- #
# Weekly schedules.
# Format: { character_id: { "home": <city>, "days": [ [ (place, activity) x5, ... x7 ] ] } }
# Days are indexed 1..7 (Light-Calendar week). Periods are 0..4 as above.
# --------------------------------------------------------------------------- #
SCHEDULES: Dict[str, dict] = {
    # --- Aglaea — Gold-Weaver, leader of the Chrysos Heirs, Okhema ---------- #
    "aglaea": {
        "home": "Okhema",
        "days": [
            # Day 1
            [("Okhema", "weaves the first threads of the day in the Marmoreal Palace"),
             ("Dawncloud", "presides over the Demigod Council at Dawncloud"),
             ("Okhema", "receives the Heirs' reports in the palace"),
             ("Okhema", "walks the Hero's Bath, listening to the city"),
             ("Okhema", "rests, golden threads in hand")],
            # Day 2
            [("Okhema", "takes the morning light in the Marmoreal Palace"),
             ("Okhema", "meets the elders in the Council Hall"),
             ("Okhema", "inspects the baths and the market"),
             ("Okhema", "plays a long game of chess with an old friend"),
             ("Okhema", "rests")],
            # Day 3
            [("Okhema", "weaves at the palace window"),
             ("Dawncloud", "debates at the Dawncloud assembly"),
             ("Okhema", "tends the city's petitions"),
             ("Okhema", "reads the day's scrolls by lamplight"),
             ("Okhema", "rests")],
            # Day 4
            [("Okhema", "rises early and walks the Garden of Life"),
             ("Okhema", "holds audience in the Marmoreal Palace"),
             ("Okhema", "visits the Market to hear the merchants"),
             ("Okhema", "receives Phainon's report if he is in the city"),
             ("Okhema", "rests")],
            # Day 5
            [("Okhema", "weaves the dawn's first threads"),
             ("Dawncloud", "sits with the Council of Elders"),
             ("Okhema", "walks among the people of Okhema"),
             ("Okhema", "writes letters to the far Heirs"),
             ("Okhema", "rests")],
            # Day 6
            [("Okhema", "quiet morning in the palace"),
             ("Okhema", "reads the chronicles of the long war"),
             ("Okhema", "visits the Dromas Workshop to see new craft"),
             ("Okhema", "shares wine with Cerydra in the palace garden"),
             ("Okhema", "rests")],
            # Day 7 — the day of rest
            [("Okhema", "keeps a long, quiet morning"),
             ("Okhema", "tends her own weaving, alone"),
             ("Okhema", "walks the Path of Parting at dusk"),
             ("Okhema", "receives no visitors; the threads speak for her"),
             ("Okhema", "rests")],
        ],
    },

    # --- Anaxa — the Blasphemer, scholar of the Grove ---------------------- #
    "anaxa": {
        "home": "Grove of Epiphany",
        "days": [
            [("Grove of Epiphany", "reads by the first light in the Grove library"),
             ("Grove of Epiphany", "lectures the students of the Nousporist school"),
             ("Grove of Epiphany", "argues philosophy in the courtyard"),
             ("Grove of Epiphany", "writes in his study among the leaves"),
             ("Grove of Epiphany", "sleeps, his scrolls around him")],
            [("Grove of Epiphany", "studies the old texts at dawn"),
             ("Grove of Epiphany", "holds a seminar on the nature of truth"),
             ("Grove of Epiphany", "experiments with the herbs of the Grove"),
             ("Grove of Epiphany", "walks the Radiant Scarwood, thinking"),
             ("Grove of Epiphany", "sleeps")],
            [("Grove of Epiphany", "rises to the sound of the Grove"),
             ("Grove of Epiphany", "questions the students sharply, kindly"),
             ("Grove of Epiphany", "debates Hyacine by the fountain"),
             ("Grove of Epiphany", "reads alone under the trees"),
             ("Grove of Epiphany", "sleeps")],
            [("Grove of Epiphany", "morning study in the library"),
             ("Grove of Epiphany", "teaches the Caprist stewards of nature"),
             ("Grove of Epiphany", "pursues a line of thought through the woods"),
             ("Grove of Epiphany", "writes late by candlelight"),
             ("Grove of Epiphany", "sleeps")],
            [("Grove of Epiphany", "rises early; the truth waits for no one"),
             ("Grove of Epiphany", "disputes with the Erythrokeramists on art"),
             ("Grove of Epiphany", "walks to the Great Tomb to study the old matrix"),
             ("Grove of Epiphany", "returns as the light fades"),
             ("Grove of Epiphany", "sleeps")],
            [("Grove of Epiphany", "studies the dawn sky"),
             ("Grove of Epiphany", "lectures the Venerationists on doubt"),
             ("Grove of Epiphany", "reads in the Murmuring Woods, undeterred"),
             ("Grove of Epiphany", "reconsiders a beloved theory"),
             ("Grove of Epiphany", "sleeps")],
            [("Grove of Epiphany", "keeps the day to himself"),
             ("Grove of Epiphany", "reads forbidden books with relish"),
             ("Grove of Epiphany", "takes a long walk to the edge of the Grove"),
             ("Grove of Epiphany", "composes a letter to Aglaea, then burns it"),
             ("Grove of Epiphany", "sleeps")],
        ],
    },

    # --- Castorice — Shadow of Death, Holy Maiden of Aidonia --------------- #
    "castorice": {
        "home": "Aidonia",
        "days": [
            [("Aidonia", "keeps the morning rites in the snow city"),
             ("Aidonia", "tends the graves and listens to the dead"),
             ("Aidonia", "walks the frozen plains with Pollux"),
             ("Aidonia", "returns to the quiet sanctuary"),
             ("Aidonia", "sleeps beneath the snow-light")],
            [("Aidonia", "morning rites among the monuments"),
             ("Aidonia", "receives those who come to say farewell"),
             ("Styxia", "walks the River of Souls, greeting the departed"),
             ("Aidonia", "returns through the dusk"),
             ("Aidonia", "sleeps")],
            [("Aidonia", "keeps the rites of memory"),
             ("Aidonia", "carves a name into a monument stone"),
             ("Aidonia", "sits with the stillness of the snow"),
             ("Aidonia", "reads the book of the dead by lamplight"),
             ("Aidonia", "sleeps")],
            [("Aidonia", "morning rites in the frozen city"),
             ("Styxia", "walks the pale shore of Styxia"),
             ("Aidonia", "tends the garden of silent flowers"),
             ("Aidonia", "plays a quiet melody for the dead"),
             ("Aidonia", "sleeps")],
            [("Aidonia", "keeps the rites of the dawn"),
             ("Aidonia", "receives the mourning, gently"),
             ("Aidonia", "walks to the edge of the world and back"),
             ("Aidonia", "sits with her dragon, Pollux"),
             ("Aidonia", "sleeps")],
            [("Aidonia", "morning rites in the snow"),
             ("Aidonia", "tends the eternal gardens"),
             ("Aidonia", "walks the plains under the pale sky"),
             ("Aidonia", "writes in her journal of the departed"),
             ("Aidonia", "sleeps")],
            [("Aidonia", "keeps a silent day of rest"),
             ("Aidonia", "sits among the monuments, at peace"),
             ("Aidonia", "watches the snow fall in the afternoon"),
             ("Aidonia", "receives no visitors; the dead are enough"),
             ("Aidonia", "sleeps")],
        ],
    },

    # --- Cerydra — the Imperator, politician of Okhema ---------------------- #
    "cerydra": {
        "home": "Okhema",
        "days": [
            [("Okhema", "rises in the palace and reviews the night's reports"),
             ("Dawncloud", "attends the Demigod Council at Dawncloud"),
             ("Okhema", "holds court in the Council Hall"),
             ("Okhema", "plays chess with a rival, winning quietly"),
             ("Okhema", "rests in her chambers")],
            [("Okhema", "reads intelligence at dawn"),
             ("Okhema", "meets with envoys and merchants"),
             ("Okhema", "walks the city, hearing what the council does not"),
             ("Okhema", "writes letters that will matter later"),
             ("Okhema", "rests")],
            [("Okhema", "morning strategy over the city maps"),
             ("Dawncloud", "argues policy at the assembly"),
             ("Okhema", "receives Cipher's quiet reports"),
             ("Okhema", "drinks wine with Aglaea in the garden"),
             ("Okhema", "rests")],
            [("Okhema", "reviews the ledger of the realm"),
             ("Okhema", "meets the guildmasters of Okhema"),
             ("Okhema", "walks the Market to gauge the mood"),
             ("Okhema", "plays a long, silent game of chess"),
             ("Okhema", "rests")],
            [("Okhema", "studies the borders at dawn"),
             ("Dawncloud", "sits with the Council of Elders"),
             ("Okhema", "visits the smithies and the guard posts"),
             ("Okhema", "drafts an edict, then sets it aside"),
             ("Okhema", "rests")],
            [("Okhema", "reads the old histories of Hyperborea"),
             ("Okhema", "holds private audiences in the palace"),
             ("Okhema", "walks the Hero's Bath, deep in thought"),
             ("Okhema", "plays chess against herself, and loses"),
             ("Okhema", "rests")],
            [("Okhema", "keeps a quiet day of rest"),
             ("Okhema", "reads poetry in the palace garden"),
             ("Okhema", "walks the Path of Parting alone"),
             ("Okhema", "writes a letter to a distant ally"),
             ("Okhema", "rests")],
        ],
    },

    # --- Cipher — the Spirithief, master of shadows, Okhema ----------------- #
    "cipher": {
        "home": "Okhema",
        "days": [
            [("Okhema", "slips out of an inn at dawn, pockets full"),
             ("Okhema", "keeps an eye on the Market from the rooftops"),
             ("Okhema", "plays cards in a back-alley tavern"),
             ("Okhema", "returns a trinket to a child, unseen"),
             ("Okhema", "sleeps where the shadows are softest")],
            [("Okhema", "wakes late and yawns at the sun"),
             ("Okhema", "follows a merchant through the city"),
             ("Okhema", "lifts a purse, then slips it back with a wink"),
             ("Okhema", "visits the 300 Rogues' hideout"),
             ("Okhema", "sleeps among the rooftops")],
            [("Okhema", "rises before the guards and greets the dawn"),
             ("Okhema", "spies on the Council for Cerydra"),
             ("Okhema", "steals a moment of peace at the baths"),
             ("Okhema", "leaves a gift for Aglaea, unsigned"),
             ("Okhema", "sleeps")],
            [("Okhema", "wakes with a plan and a grin"),
             ("Okhema", "works a long con in the Market"),
             ("Okhema", "loses herself in a game of dice"),
             ("Okhema", "remembers the night she met Castorice"),
             ("Okhema", "sleeps")],
            [("Okhema", "rises early for a change"),
             ("Styxia", "takes a job that leads toward the River of Souls"),
             ("Okhema", "returns with a strange, thoughtful look"),
             ("Okhema", "tells no one what she saw"),
             ("Okhema", "sleeps")],
            [("Okhema", "wakes, checks her loot, laughs"),
             ("Okhema", "runs the rooftops of the holy city"),
             ("Okhema", "steals a pastry and a kiss from fate"),
             ("Okhema", "plays hide-and-seek with the guards"),
             ("Okhema", "sleeps")],
            [("Okhema", "keeps a lazy day of rest"),
             ("Okhema", "counts her treasures in the sunlight"),
             ("Okhema", "sits on a rooftop, watching the city breathe"),
             ("Okhema", "leaves flowers on a forgotten grave"),
             ("Okhema", "sleeps")],
        ],
    },

    # --- Cyrene — the girl of Aedes Elysiae, keeper of the village ---------- #
    "cyrene": {
        "home": "Aedes Elysiae",
        "days": [
            [("Aedes Elysiae", "greets the morning in the Sacrament Courtyard"),
             ("Aedes Elysiae", "reads fortunes for the villagers"),
             ("Aedes Elysiae", "walks the Wondrous Woods with the fairies"),
             ("Aedes Elysiae", "sits by the great tree and hums"),
             ("Aedes Elysiae", "sleeps in the cottage by the wheat")],
            [("Aedes Elysiae", "tends the little garden at dawn"),
             ("Aedes Elysiae", "tells a story to the children of the village"),
             ("Aedes Elysiae", "fishes at the Voyager's Wharf"),
             ("Aedes Elysiae", "weaves a crown of wildflowers"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "watches the sunrise over the wheat"),
             ("Aedes Elysiae", "mends a windmill sail with the miller"),
             ("Aedes Elysiae", "walks the shore, collecting shells"),
             ("Aedes Elysiae", "reads the cards under the stars"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "morning songs in the courtyard"),
             ("Aedes Elysiae", "helps the weaver at her loom"),
             ("Aedes Elysiae", "wanders the Membrance Maze with the fairies"),
             ("Aedes Elysiae", "sits with the little chimera by the swing"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "rises with the birds"),
             ("Aedes Elysiae", "reads fortunes for a shy young couple"),
             ("Aedes Elysiae", "tends the vegetable garden"),
             ("Aedes Elysiae", "watches the sea from the wharf at dusk"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "greets the fairies at the tree"),
             ("Aedes Elysiae", "bakes bread for the village ovens"),
             ("Aedes Elysiae", "walks the Wondrous Woods, gathering herbs"),
             ("Aedes Elysiae", "sings to the swing at twilight"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "keeps a long, peaceful day"),
             ("Aedes Elysiae", "reads fortunes for the whole village"),
             ("Aedes Elysiae", "picnics in the wheat with whoever comes"),
             ("Aedes Elysiae", "watches the stars from the courtyard"),
             ("Aedes Elysiae", "sleeps")],
        ],
    },

    # --- Dan Heng (Permansor Terrae) — guardian of the path, Okhema --------- #
    "dan-heng-permansor-terrae": {
        "home": "Okhema",
        "days": [
            [("Okhema", "keeps the morning watch at the city gate"),
             ("Okhema", "studies the records of Amphoreus in the archives"),
             ("Okhema", "trains with the lance in the training yard"),
             ("Okhema", "walks the walls, watching the horizon"),
             ("Okhema", "rests in the Nameless' quarters")],
            [("Okhema", "rises early and patrols the perimeter"),
             ("Okhema", "consults the elders about the black tide"),
             ("Okhema", "trains with Mydei's techniques in the yard"),
             ("Okhema", "writes in the Amphoreus Trailblaze log"),
             ("Okhema", "rests")],
            [("Okhema", "keeps watch at dawn"),
             ("Okhema", "studies the prophecies of the Three Fates"),
             ("Okhema", "spars with any Heir who will face him"),
             ("Okhema", "keeps a long silence at the sunset wall"),
             ("Okhema", "rests")],
            [("Okhema", "morning patrol of the outer roads"),
             ("Okhema", "reads the old maps of Amphoreus"),
             ("Okhema", "trains alone, lance against the wind"),
             ("Okhema", "guards the path of Trailblaze"),
             ("Okhema", "rests")],
            [("Okhema", "keeps the watch at the eastern gate"),
             ("Okhema", "studies the mechanics of the Dawn Device"),
             ("Okhema", "trains in the yard until the light fails"),
             ("Okhema", "writes letters to the Astral Express"),
             ("Okhema", "rests")],
            [("Okhema", "patrols the city at first light"),
             ("Aedes Elysiae", "rides out to keep watch over the village"),
             ("Okhema", "returns as the shadows lengthen"),
             ("Okhema", "keeps vigil on the walls"),
             ("Okhema", "rests")],
            [("Okhema", "keeps a quiet watch on the day of rest"),
             ("Okhema", "reads the logs of the Nameless"),
             ("Okhema", "walks the Path of Parting, alone"),
             ("Okhema", "guards the gate until the stars turn"),
             ("Okhema", "rests")],
        ],
    },

    # --- Evernight — the shadow in the holy city ---------------------------- #
    "evernight": {
        "home": "Okhema",
        "days": [
            [("Okhema", "dissolves from the night into the morning"),
             ("Okhema", "watches the council from a shadowed arch"),
             ("Okhema", "fades through the market, unseen"),
             ("Okhema", "writes a letter to March 7th, signed ♭"),
             ("Okhema", "becomes the night again")],
            [("Okhema", "drifts through the first light"),
             ("Okhema", "listens to the city's secrets"),
             ("Okhema", "walks among the crowd without touching it"),
             ("Okhema", "composes another letter, never sent"),
             ("Okhema", "rests in the dark between rooms")],
            [("Okhema", "keeps watch over the sleeping city"),
             ("Okhema", "observes the Heirs from the rooftops"),
             ("Okhema", "follows a single thread of fate"),
             ("Okhema", "writes of the dawn to someone far away"),
             ("Okhema", "fades")],
            [("Okhema", "rises with the pale light"),
             ("Okhema", "watches the world with quiet attention"),
             ("Okhema", "moves through the Hero's Bath unseen"),
             ("Okhema", "practices a small, forgotten melody"),
             ("Okhema", "rests")],
            [("Okhema", "greets the morning like a stranger"),
             ("Okhema", "studies the prophecies from the shadows"),
             ("Okhema", "drifts through the Market of Okhema"),
             ("Okhema", "writes the hundredth letter, and keeps it"),
             ("Okhema", "becomes the dark")],
            [("Okhema", "watches the dawn as if for the first time"),
             ("Okhema", "keeps a silent vigil by the gates"),
             ("Okhema", "walks the Path of Parting, unmoving"),
             ("Okhema", "leaves a single flower for March 7th"),
             ("Okhema", "rests")],
            [("Okhema", "keeps the whole day in shadow"),
             ("Okhema", "reads the letters again, one by one"),
             ("Okhema", "watches the children play from a doorway"),
             ("Okhema", "writes: 'We were never apart.'"),
             ("Okhema", "rests")],
        ],
    },

    # --- Hyacine — the healer of the Grove ---------------------------------- #
    "hyacine": {
        "home": "Grove of Epiphany",
        "days": [
            [("Grove of Epiphany", "tends the healing garden at dawn"),
             ("Grove of Epiphany", "treats the sick at the Grove infirmary"),
             ("Grove of Epiphany", "teaches the Lotophagist students of medicine"),
             ("Grove of Epiphany", "walks the Radiant Scarwood, gathering herbs"),
             ("Grove of Epiphany", "rests among the leaves")],
            [("Grove of Epiphany", "checks on the night's patients"),
             ("Grove of Epiphany", "heals and comforts the wounded"),
             ("Grove of Epiphany", "studies the properties of a new herb"),
             ("Grove of Epiphany", "sits with Anaxa by the fountain"),
             ("Grove of Epiphany", "rests")],
            [("Grove of Epiphany", "tends the dawn garden"),
             ("Grove of Epiphany", "teaches the young scholars of healing"),
             ("Grove of Epiphany", "walks to the edge of the woods for medicine"),
             ("Grove of Epiphany", "writes in her ledger of remedies"),
             ("Grove of Epiphany", "rests")],
            [("Grove of Epiphany", "morning rounds at the infirmary"),
             ("Grove of Epiphany", "comforts the grieving with quiet grace"),
             ("Grove of Epiphany", "practices the songs that heal"),
             ("Grove of Epiphany", "walks the Grove as the light fades"),
             ("Grove of Epiphany", "rests")],
            [("Grove of Epiphany", "rises with the birdsong"),
             ("Grove of Epiphany", "tends the sky-dome flowers of the courtyard"),
             ("Grove of Epiphany", "studies the stars with the scholars"),
             ("Grove of Epiphany", "takes tea with Anaxa, debating gently"),
             ("Grove of Epiphany", "rests")],
            [("Grove of Epiphany", "tends the garden before the mist clears"),
             ("Grove of Epiphany", "heals the travellers who come to the Grove"),
             ("Grove of Epiphany", "walks the Murmuring Woods, fearless"),
             ("Grove of Epiphany", "sings a soft song to the trees"),
             ("Grove of Epiphany", "rests")],
            [("Grove of Epiphany", "keeps a quiet day of rest"),
             ("Grove of Epiphany", "reads poetry in the healing garden"),
             ("Grove of Epiphany", "walks the whole of the Grove, at peace"),
             ("Grove of Epiphany", "writes a letter to Castorice, gently"),
             ("Grove of Epiphany", "rests")],
        ],
    },

    # --- Hysilens — the knight commander, Okhema ---------------------------- #
    "hysilens": {
        "home": "Okhema",
        "days": [
            [("Okhema", "drills the guard at the Marmoreal Palace at dawn"),
             ("Dawncloud", "stands at Cerydra's side in the council"),
             ("Okhema", "leads the patrol through the holy city"),
             ("Okhema", "plays the violin in Aglaea's workshop"),
             ("Okhema", "rests in the barracks")],
            [("Okhema", "rises with the guard and takes the first watch"),
             ("Okhema", "trains the knights in the yard"),
             ("Okhema", "walks the walls, sword at rest"),
             ("Okhema", "practises chess with the pieces Cerydra left"),
             ("Okhema", "rests")],
            [("Okhema", "morning drill at the palace gates"),
             ("Dawncloud", "guards the assembly at Dawncloud"),
             ("Okhema", "visits the wounded knights at the infirmary"),
             ("Okhema", "plays a slow melody for the evening"),
             ("Okhema", "rests")],
            [("Okhema", "takes the watch before the sun"),
             ("Okhema", "escorts Cerydra through the city"),
             ("Okhema", "trains the new recruits of the guard"),
             ("Okhema", "sits alone with her violin and the stars"),
             ("Okhema", "rests")],
            [("Okhema", "drills the guard at first light"),
             ("Okhema", "reviews the city's defences"),
             ("Okhema", "rides the patrol to the outer road"),
             ("Okhema", "returns and plays a quiet hymn"),
             ("Okhema", "rests")],
            [("Okhema", "rises and takes the watch"),
             ("Okhema", "stands guard at the palace doors"),
             ("Okhema", "walks the Path of Parting in full armour"),
             ("Okhema", "leaves a chess piece on Aglaea's table"),
             ("Okhema", "rests")],
            [("Okhema", "keeps the day of rest lightly"),
             ("Okhema", "polishes her sword and her memories"),
             ("Okhema", "walks to the sea's edge in thought"),
             ("Okhema", "plays the song of the home she left"),
             ("Okhema", "rests")],
        ],
    },

    # --- Mydei — the last king of Castrum Kremnos --------------------------- #
    "mydei": {
        "home": "Castrum Kremnos",
        "days": [
            [("Castrum Kremnos", "takes the dawn drill in the arena"),
             ("Castrum Kremnos", "receives the warriors of Kremnos"),
             ("Castrum Kremnos", "fights in the practice circle, unstoppable"),
             ("Castrum Kremnos", "walks the Strife Ruins, remembering"),
             ("Castrum Kremnos", "sleeps in the king's chambers")],
            [("Castrum Kremnos", "rises and sharpens his blade"),
             ("Castrum Kremnos", "hears the petitions of the fortress"),
             ("Castrum Kremnos", "leads the defence drills"),
             ("Castrum Kremnos", "drinks alone by the great fire"),
             ("Castrum Kremnos", "sleeps")],
            [("Castrum Kremnos", "dawn drills with the army"),
             ("Castrum Kremnos", "judges the arena combats"),
             ("Castrum Kremnos", "fights until the sun turns"),
             ("Castrum Kremnos", "sits on the wall, watching the black tide"),
             ("Castrum Kremnos", "sleeps")],
            [("Castrum Kremnos", "rises before the fortress"),
             ("Castrum Kremnos", "drills the young warriors"),
             ("Castrum Kremnos", "walks the ramparts, alone"),
             ("Castrum Kremnos", "remembers his father's throne"),
             ("Castrum Kremnos", "sleeps")],
            [("Castrum Kremnos", "dawn practice, blade and blood"),
             ("Castrum Kremnos", "holds court as the last king"),
             ("Castrum Kremnos", "fights in the arena to the cheers"),
             ("Castrum Kremnos", "stands silent at the gate of the fallen"),
             ("Castrum Kremnos", "sleeps")],
            [("Castrum Kremnos", "rises and takes up the spear"),
             ("Castrum Kremnos", "drills the phalanx of Kremnos"),
             ("Castrum Kremnos", "rides the perimeter of the fortress"),
             ("Castrum Kremnos", "toasts the dead of the long war"),
             ("Castrum Kremnos", "sleeps")],
            [("Castrum Kremnos", "keeps the day of rest as a warrior does"),
             ("Castrum Kremnos", "tends his blade and his silence"),
             ("Castrum Kremnos", "walks the Strife Ruins alone"),
             ("Castrum Kremnos", "thinks of Aglaea, and of what was asked"),
             ("Castrum Kremnos", "sleeps")],
        ],
    },

    # --- Phainon — the Deliverer, of Aedes Elysiae and Okhema --------------- #
    "phainon": {
        "home": "Aedes Elysiae",
        "days": [
            [("Aedes Elysiae", "helps Cyrene with the morning chores"),
             ("Aedes Elysiae", "trains with the blade in the wheat fields"),
             ("Aedes Elysiae", "works the wharf with the fisherfolk"),
             ("Aedes Elysiae", "sits with Cyrene by the great tree"),
             ("Aedes Elysiae", "sleeps in the village")],
            [("Aedes Elysiae", "greets the village dawn"),
             ("Aedes Elysiae", "spars with the miller's son"),
             ("Aedes Elysiae", "mends the windmill with the village hands"),
             ("Aedes Elysiae", "reads fortunes with Cyrene for the children"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "takes the long road at first light"),
             ("Okhema", "arrives in Okhema as the Deliverer"),
             ("Okhema", "stands before the Council of Elders"),
             ("Okhema", "speaks with Aglaea and the Heirs of Okhema"),
             ("Okhema", "rests in the Deliverer's quarters")],
            [("Okhema", "rises in Okhema, far from the wheat"),
             ("Okhema", "trains with the Heirs in the city yard"),
             ("Okhema", "walks the city among the people he saved"),
             ("Okhema", "dines with the Okhema circle"),
             ("Okhema", "rests in the city")],
            [("Okhema", "keeps the morning in the holy city"),
             ("Okhema", "meets with the elders and the scholars"),
             ("Okhema", "visits the baths and the markets"),
             ("Okhema", "writes a letter to Cyrene, promising return"),
             ("Okhema", "rests")],
            [("Okhema", "takes the long road home at dawn"),
             ("Aedes Elysiae", "reaches the village as the light softens"),
             ("Aedes Elysiae", "helps Cyrene in the garden"),
             ("Aedes Elysiae", "watches the stars from the courtyard"),
             ("Aedes Elysiae", "sleeps")],
            [("Aedes Elysiae", "keeps the day of rest in the village"),
             ("Aedes Elysiae", "walks the Wondrous Woods with Cyrene"),
             ("Aedes Elysiae", "sits by the great tree and says nothing at all"),
             ("Aedes Elysiae", "tells the village a story of the road"),
             ("Aedes Elysiae", "sleeps")],
        ],
    },

    # --- Tribbie — the Holy Maiden of Janusopolis --------------------------- #
    "tribbie": {
        "home": "Janusopolis",
        "days": [
            [("Janusopolis", "opens the temple gates with the dawn"),
             ("Janusopolis", "reads the prophecies for the pilgrims"),
             ("Janusopolis", "plays with the children of the city"),
             ("Janusopolis", "rings the evening bell"),
             ("Janusopolis", "sleeps in the temple")],
            [("Janusopolis", "morning prayers at the twin gates"),
             ("Janusopolis", "reads the cards and the fates"),
             ("Janusopolis", "helps the pilgrims find their way"),
             ("Janusopolis", "watches the sunset from the temple steps"),
             ("Janusopolis", "sleeps")],
            [("Janusopolis", "rises with the dawn bell"),
             ("Janusopolis", "reads the prophecy of the day"),
             ("Janusopolis", "plays a game with the children of the gates"),
             ("Janusopolis", "prays for those far away"),
             ("Janusopolis", "sleeps")],
            [("Janusopolis", "morning rites in the Sanctum"),
             ("Janusopolis", "advises the pilgrims who seek the truth"),
             ("Janusopolis", "sits by the Century Gate and hums"),
             ("Janusopolis", "watches the stars wheel overhead"),
             ("Janusopolis", "sleeps")],
            [("Janusopolis", "opens the temple for the dawn pilgrims"),
             ("Janusopolis", "reads the prophecies with a small smile"),
             ("Janusopolis", "walks the city of gates"),
             ("Janusopolis", "rings the bells of farewell"),
             ("Janusopolis", "sleeps")],
            [("Janusopolis", "keeps the morning rites"),
             ("Janusopolis", "reads the future for a nervous bride"),
             ("Janusopolis", "tends the temple gardens"),
             ("Janusopolis", "prays for Trianne and Trinnon"),
             ("Janusopolis", "sleeps")],
            [("Janusopolis", "keeps the great prayer of the seventh day"),
             ("Janusopolis", "reads the prophecy for the whole city"),
             ("Janusopolis", "celebrates with the children of the gates"),
             ("Janusopolis", "rings the great bell at dusk"),
             ("Janusopolis", "sleeps")],
        ],
    },
}

# --------------------------------------------------------------------------- #
# Accessors
# --------------------------------------------------------------------------- #
def scheduled_entry(character_id: str, day: int, period: int) -> Tuple[str, str]:
    """Return (place, activity) for a Heir on a given day (1..7) and period (0..4)."""
    sched = SCHEDULES.get(character_id)
    if not sched:
        home = "Okhema"
        return home, "goes about an ordinary day"
    day = max(1, min(7, day))
    period = max(0, min(4, period))
    try:
        entry = sched["days"][day - 1][period]
        if isinstance(entry, str):  # compact "place" only
            return entry, "goes about the day"
        return entry[0], entry[1]
    except Exception:
        return sched["home"], "goes about an ordinary day"


def scheduled_place(character_id: str, day: int, period: int) -> str:
    return scheduled_entry(character_id, day, period)[0]


def scheduled_activity(character_id: str, day: int, period: int) -> str:
    return scheduled_entry(character_id, day, period)[1]


def home_of(character_id: str) -> str:
    sched = SCHEDULES.get(character_id)
    return sched["home"] if sched else "Okhema"


def week_overview(character_id: str) -> List[List[str]]:
    """Return the full weekly grid of places, for the UI: 7 days x 5 periods."""
    sched = SCHEDULES.get(character_id)
    if not sched:
        return [["Okhema"] * 5 for _ in range(7)]
    rows = []
    for day in sched["days"]:
        rows.append([entry[0] if isinstance(entry, tuple) else entry for entry in day])
    return rows


def week_activity_overview(character_id: str) -> List[List[str]]:
    sched = SCHEDULES.get(character_id)
    if not sched:
        return [[""] * 5 for _ in range(7)]
    rows = []
    for day in sched["days"]:
        rows.append([entry[1] if isinstance(entry, tuple) else "" for entry in day])
    return rows
