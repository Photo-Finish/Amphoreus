"""The Guide — a friendly, in-app page that teaches the visitor how to use the
Sanctuary, including the second layer of life (the vivid world & the human
Heirs). Rendered as its own tab in the UI.
"""

import streamlit as st


def _section(title, body):
    st.markdown(f"### {title}")
    st.markdown(body)


def render_guide(manager, characters):
    st.title("❓ How to use the Sanctuary")
    st.caption(
        "A short guide to the little Amphoreus — what you can do here, and how "
        "the world around the Heirs is alive."
    )

    # A live line showing the current experience mode.
    try:
        from src.core.visitor_mode import current_mode
        mode = current_mode()
        if mode == "aftermath":
            st.info("✨ You are in **Aftermath** mode — the Heirs remember you as a war-companion.")
        else:
            st.info("🗺️ You are in **Journey** mode — you are newly arrived; the Heirs do not know you yet.")
    except Exception:
        pass

    _section("The five places to go", (
        "The tabs across the top are your doorway into Amphoreus:\n\n"
        "- **💬 Visit an Heir** — talk with one of the thirteen Chrysos Heirs. "
        "Choose them in the sidebar on the left.\n"
        "- **📖 A Chronicle of Amphoreus** — the Gazette, a newspaper of the "
        "world's days: the sky, the news, the Heirs' moods, the whispers, your "
        "mailbox, and the written record.\n"
        "- **🗺️ Map of Amphoreus** — the real geography. Click any place or "
        "Heir for a pop-up. Silver ⏳ nodes are the Dawn-era (past) forms; the "
        "purple † node is the Nether.\n"
        "- **🛠️ Admin Console** — the operational view (memory, world state, "
        "the quality loop).\n"
        "- **🎬 Galgame** — the same conversation as a visual novel.\n"
    ))

    _section("🕳️ The black tide (optional — a live threat)", (
        "In the **sidebar** there is a switch: **“🕳️ Live black tide”**.\n\n"
        "- **On** — the tide can stir along the edge cities. Travel into a "
        "surged city takes an extra day, and the Heirs who live there grow "
        "weary. You will see the warning in the Gazette and on the Map.\n"
        "- **Off** — Amphoreus rests at peace, and the tide never stirs.\n\n"
        "It is a toggle, not a difficulty setting — switch it whenever you like."
    ))

    _section("🎁 Gifts from the market", (
        "Open any Heir in **💬 Visit an Heir**, then open **“🎁 Give a gift”**.\n\n"
        "The market is the Heir's *own* city, so every gift is something from "
        "their world. Giving one becomes a memory they keep, and it warms their "
        "mood — you will see them soften."
    ))

    _section("📬 Your mailbox", (
        "The Heirs write to you. In the **Gazette**, the **“📬 Your Mailbox”** "
        "section holds notes left for you — including times an Heir reached out "
        "*on their own* (they think of you now and then, unprompted)."
    ))

    _section("🌥️ Moods — how an Heir is feeling", (
        "Every Heir carries an emotional weather of their own. Look in the "
        "**sidebar** (under their bond) or the Gazette's **“🌥️ The Heirs' "
        "Moods”**. It comes from what happens in the world — a black tide, a "
        "gift, a kind word, or a wound — and it slowly settles back toward calm. "
        "It colours their voice, but never commands it."
    ))

    _section("📖 The deeper story (slow-burn arcs)", (
        "Each Heir carries something they will only share as they come to trust "
        "you. As your bond deepens (stranger → friend → close friend → best "
        "friend), a new layer of their story opens — the sidebar shows "
        "**“📖 Carries: …”** once it has begun."
    ))

    _section("💔 Hurt, and how to mend it", (
        "The Heirs hold real values. If your words cross one of them, they will "
        "feel it — the sidebar will show **“💔 Something sits unresolved between "
        "you”**, and their mood will darken. An honest apology (*“I'm sorry”*) "
        "mends it. They remember both."
    ))

    _section("🌫️ The social web", (
        "- **What you tell one Heir can reach another.** If you mention an Heir "
        "to a different one, the word may travel to the one spoken of, and the "
        "bond between the two Heirs shifts a little.\n"
        "- **They remember shared moments.** A gift, a lesson, a moment together "
        "may surface again later, re-told in the present.\n"
        "- **They are grounded in place.** The sky, the hour, and their mood "
        "shape how the day feels where they stand.\n"
    ))

    _section("A gentle path to begin", (
        "1. Pick an Heir in the sidebar and say hello.\n"
        "2. Visit again tomorrow — they remember you, and the world will have "
        "moved on.\n"
        "3. Check the **Gazette** to see the sky, the whispers, and your "
        "mailbox.\n"
        "4. When you have grown close, bring a **gift** from their city, and "
        "let the deeper story open.\n"
    ))

    st.caption(
        "The world runs on the Light Calendar and moves only when the world "
        "engine is awake — but everything you do here is remembered."
    )
