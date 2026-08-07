"""
Complete chapter 2 build script.
Process raw wiki text files for missions 2-9 and combine with mission 1.
"""
import re, os

MISSIONS_DIR = "d:/Workspace/Amphoreus/databank/missions"
EXISTING_CH2 = os.path.join(MISSIONS_DIR, "chapter-02-light-slips.md")
OUTPUT = os.path.join(MISSIONS_DIR, "chapter-02-light-slips-NEW.md")

def strip_templates(text):
    result = []
    depth = 0
    i = 0
    while i < len(text):
        if text[i:i+2] == '{{':
            depth += 1
            i += 2
        elif depth > 0 and text[i:i+2] == '}}':
            depth -= 1
            i += 2
        elif depth == 0:
            result.append(text[i])
            i += 1
        else:
            i += 1
    return ''.join(result)

def clean_line(line):
    """Clean one wiki line to markdown dialogue."""
    if not line or not line.strip():
        return None
    
    orig = line.rstrip('\n')
    stripped = orig.strip()
    
    # Skip patterns
    skip_starts = [
        '{{A|', '{{Color|', '{{Size|', '{{MC|', '{{Rubi|', '{{w|', '{{lang|',
        '{{sic|', '{{Reflist', '{{Change', '{{Trailblaze Mission Navbox',
        '{{Preview', '{{Transclude', '{{Enemy', '{{Item|', '{{Other Languages',
        '{{Mission Infobox', '[[File:', '|file', '[[de:', '[[fr:', '[[ru:', 
        '[[vi:', '[[zh:', '<gallery>', '</gallery>', '{{Stub', '{{Reflist',
        '}}}}', '{{Other', '{{#', '|id', '|title', '|image', '|type', '|chapter',
        '|part', '|perspective', '|requirements', '|summary', '|characters',
        '|startLocation', '|world', '|area', '|prev', '|next', '|rewards', '|voiced',
    ]
    for p in skip_starts:
        if stripped.startswith(p):
            return None
    
    # Skip patterns with regex
    if re.match(r'^;\((Obtain|Unlock|Begin battle)', stripped):
        return None
    
    # Section headers
    if re.match(r'^===.*===$', stripped) and not re.match(r'^====', stripped):
        title = stripped.strip('= ')
        skip_titles = ['Dialogue', 'Steps', 'Gameplay Notes', 'Notes', '',
                       'Other Languages', 'Change History', 'Navigation',
                       'Gameplay', 'Trial Character', '==']
        if title not in skip_titles and '===' not in title:
            return f"\n## {title}\n"
        return None
    
    if re.match(r'^====', stripped):
        return None
    
    if stripped == '----':
        return "\n---\n"
    
    if '===' in stripped and not '====' in stripped:
        return None
    
    # ;(Approach...) stage directions
    if stripped.startswith(';('):
        inner = stripped[2:].strip()
        inner = strip_templates(inner)
        inner = re.sub(r"'''", '', inner)
        inner = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', inner)
        inner = re.sub(r'\[\[([^\]]+)\]\]', r'\1', inner)
        inner = inner.replace('&mdash;', '—').replace('&nbsp;', ' ')
        if inner:
            return f"\n*[{inner}]*\n"
        return None
    
    # Clean the line
    cleaned = strip_templates(stripped)
    cleaned = re.sub(r"'''", '', cleaned)
    cleaned = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', cleaned)
    cleaned = re.sub(r'\[\[([^\]]+)\]\]', r'\1', cleaned)
    cleaned = cleaned.replace('&mdash;', '—')
    cleaned = cleaned.replace('&nbsp;', ' ')
    cleaned = cleaned.replace('&amp;', '&')
    cleaned = cleaned.strip()
    
    if not cleaned:
        return None
    
    # DIcon patterns (check ORIGINAL before stripping)
    if '{{DIcon|Arrow}}' in orig:
        text = orig.split('{{DIcon|Arrow}}', 1)[1]
        text = strip_templates(text)
        text = re.sub(r"'''", '', text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—').replace('&nbsp;', ' ')
        text = text.strip()
        if text:
            return f"> *(Trailblazer)* {text}\n"
        return None
    
    if '{{DIcon|Talk}}' in orig:
        text = orig.split('{{DIcon|Talk}}', 1)[1]
        text = strip_templates(text)
        text = re.sub(r"'''", '', text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—')
        text = text.strip()
        if text:
            return f"> 💬 {text}\n"
        return None
    
    # :: responses (nested dialogue)
    if cleaned.startswith('::'):
        inner = cleaned[2:].strip()
        m2 = re.match(r"(.*?):\s*(.*)", inner)
        if m2:
            char = m2.group(1).strip()
            text = m2.group(2).strip()
            if char and text:
                return f">   **{char}:** {text}\n"
            if text:
                return f">   {text}\n"
        if inner:
            return f">   {inner}\n"
        return None
    
    # Character dialogue: :Char: text
    m = re.match(r"^:(.*?):\s*(.*)", cleaned)
    if m:
        char = m.group(1).strip()
        text = m.group(2).strip()
        if text:
            return f"**{char}:** {text}\n"
        return None
    
    # Plain narration
    if cleaned and len(cleaned) > 1:
        # Skip lines that look like infobox parameters
        if cleaned.startswith('=') or cleaned.startswith('<') or cleaned.startswith('|'):
            return None
        return f"{cleaned}\n"
    
    return None

# Build the complete file
def build():
    # Read existing mission 1 content
    with open(EXISTING_CH2, 'r', encoding='utf-8') as f:
        existing = f.read()
    
    # Extract mission 1 (up to "End of Chapter 2")
    end_marker = "## End of Chapter 2"
    if end_marker in existing:
        mission1 = existing.split(end_marker)[0] + "\n"
    else:
        mission1 = existing + "\n"
    
    # Start building the new file
    output = mission1
    output += "\n---\n\n"
    output += "# Mission 2: Glory, Turn From Imbibed Poison\n\n"
    output += "**Perspective:** Mydei (Remnants of Regal Sounds)\n\n"
    output += "*Mydei must gain the trust of his people. He seeks out the Kremnoan veteran Krateros for counsel.*\n\n"
    
    # Mission 2 dialogue (Glory)
    m2_dialogue = """## Speak with Tribbie

*[At the same time, on the other side of Marmoreal Palace]*

**Mydei:** ...

**Tribbie:** Don't worry, De. This isn't the first time he's been like this. A long time ago—

**Mydei:** I'm not worrying about him.

**Tribbie:** Oh... Alright. You're a little quiet, though.

**Mydei:** ...I'm sorry, that was rude of me. What I meant was, I know that man can pull through for sure.

**Tribbie:** Hehe, it's alright! Being straightforward suits you better.

**Tribbie:** Actually, De, there's something we are curious about... What did you see in Nikador's trial?

**Mydei:** ...Something that terrifies me.

**Mydei:** Isn't that ironic? There shouldn't even be a word for "fear" in the Kremnoan language.

**Tribbie:** Do you think... you stand a chance? Against that thing that terrifies you?

**Mydei:** Is this also part of your grand scheme?

**Tribbie:** What do you mean?

**Mydei:** Aglaea knew that Phainon might fall... ...And she expected me to take his place. That was the plan all along, wasn't it?

**Tribbie:** ...Yes. Looks like you know everything.

**Mydei:** I have no intention of condemning you for it. The Flame-Chase Journey is not a game, and I have long understood this.

**Mydei:** With the downfall of Strife and the ever-growing threat that the black tide poses, if Cerces and Oronyx are also impacted, the ramifications will be dire.

**Tribbie:** Mm-hmm. They are the only two Titans who are still lucid and willing to coexist with humanity.

**Mydei:** Regrettably, I do not hold the key to completing the trial. If I wish to conquer that fear, I need the assistance of my fellow Kremnoans. Give me some time to speak with my people... It won't take long, I promise.

**Tribbie:** Ah, I see — there is strength in numbers. But you must know that the trial to become a demigod is ultimately meant for only one individual.

**Tribbie:** De, your people... They have been eagerly awaiting a new king all this time, haven't they? If you take on the divine role, they will have no reservations about following your lead... After all, you're the hero of Castrum Kremnos.

**Mydei:** I once was. But Lady Tribios... Therein lies my deepest fear. ...We'll talk again later. I'll be back.

**Tribbie:** De.

**Mydei:** Hm?

**Tribbie:** Regardless of what happens, we will always be there for you.

**Mydei:** ...Thank you.

## Head to the Hot Bath and Look for the Kremnoans

**Mydei:** *(The person I'm looking for is probably in the hot bath. I should go take a look... The billowing steam always brings back memories of the furnaces in our homeland.)*

## Speak to the Playing Children

*[Approach the marked location]*

**Mydei:** *(Children left unattended by their parents? That's not safe.)*

**Mydei:** You shouldn't run around in here, kids.

**Demetri:** Hey, it's the crown prince! Are you also here for a bath?

**Castrum Kremnos Children:** Oh, the prince has arrived! / What a lucky day! / I want to hear your tales from the battlefield!

**Mydei:** The crown prince...? Are you Kremnoans?

**Andriskos:** Yeah, we are! The grown-ups said we used to live next to the arena! ...Well, next to the parts next to it anyway!

**Marsyas:** My dad is a centurion with the Hydra Lancers, and my mom is the bravest warrior in the Godshield Brigade. We used to get tons of silver coins from Mr. Krateros!

**Demetri:** My parents are serving in the Holy City Garrison now. As warriors of Kremnos, they're braver than any Okheman!

**Mydei:** Why are you kids here alone? Where are the grown-ups?

**Marsyas:** Hee-hee, Mom and Dad were asleep, so we snuck out to play hide-and-seek with Mr. Krateros!

**Mydei:** That old man can be such a child sometimes... Do you know where Krateros is? I happen to be looking for him.

**Marsyas:** Sorry, I don't. Come to think of it, we haven't seen him in a while. Did he get lost while trying to find us?

**Andriskos:** No way! Mr. Krateros is a member of the King's Guards. He's the best at hunting down enemies! He was counting near Verax Leo when we went to hide. I thought about taking a peek, but who knows if it might be a trap he set?

**Mydei:** It was prudent of you to be cautious. So, which Verax Leo was he with?

**Andriskos:** It's... Um, just take a few turns after you go out from here... It's close to the baths!

**Mydei:** Alright, I'll go look for him. You should consider the game over and head home for now. And don't play around the hot baths again!

**Demetri:** Wait, Your Highness! I heard you retrieved Nikador's Coreflame... Does that mean... we get to go back home soon?

**Mydei:** ...Have you ever been to Castrum Kremnos? You were all born in the holy city and are living lives no different from the Okhemans. Everything you know about our people comes only from the tales of others.

**Mydei:** You have never even witnessed that blade in the sky with your own eyes... How, then, is a city you have never seen your home?

**Demetri:** Because this place is definitely not home. Mom and Dad told me that the children of Kremnos are born to wield swords and fight on the battlefield.

**Andriskos:** They also said that the Kremnoan army led by the crown prince is the bravest army across all of Amphoreus. No one can defeat them!

**Marsyas:** The kids in the holy city don't play with us. The moment they find out that our parents are Kremnoans, they shun us... But we don't care. We all know that the crown prince will take us home one day!

**Mydei:** That time has not yet arrived, but... Young men of Kremnos, heed my command! Return to your parents at once. From hereon, you are to dedicate yourselves to rigorous training and a healthy diet. You must not neglect these two aspects if you are to become a brave warrior of Kremnos. Only by following this path can you be deemed worthy of returning home.

**Castrum Kremnos Children:** Yes, Your Highness!

## Look for Krateros

**Mydei:** *(The future of Kremnos... I should find Krateros.)*

*[Approach the marked location]*

**Mydei:** *(There he is. Is he engaged in a debate with that foolish lion?)*

**Distressed Soldier:** Drat! It's the crown prince of Castrum Kremnos...

**Scouting Soldier:** Get a grip! We're here by order of the Council of Elders. Even the Chrysos Heirs have to think twice before doing anything to us.

**Mydei:** Out of my way, lackeys of the Council.

**Distressed Soldier:** Uh...

**Scouting Soldier:** Th—The Civil Guard of Okhema is on official duty. Please keep out of this area!

**Verax Leo:** Calm down, my lord. Play nice...

**Mydei:** Don't make me repeat myself.

**Scouting Soldier:** I—I'll allow you to pass this time... but just this once!

---

**Krateros:** So, you think yourself knowledgeable? Then here is a question for you: Do you know how Chryseus Leo in Castrum Kremnos came to be mounted on the wall?

**Verax Leo:** I—I don't know, my lord, ahaha... How did it come to be?

**Krateros:** Hahaha! Let me enlighten you. A long time ago, the founder of Castrum Kremnos led a group of warriors to hunt down a lion on the outskirts of the city of Tretos. That vicious beast had been a menace for years, and the bones in its den were stacked even higher than the peaks around Okhema. But do you know what happened? Nary a moment had passed after the beast's head peeked out of its den when the Kremnoan warriors surged forward and brought it down within the blink of an eye, shattering its knees with a single strike! And then—

**Krateros:** ...Why are you red-faced already? We haven't even gotten to the best part yet!

**Verax Leo:** I—It's your storytelling, my lord. You're weaving such a captivating tale that it got my blood pumping. Please, go on... — Well, well. If it isn't Lord Mydei! It's been a while, ahaha...

**Krateros:** Oho, what in Okhema is happening? To what do I owe the pleasure, son of Gorgo?

**Mydei:** Krateros... My esteemed teacher.

**Krateros:** Let's talk somewhere else, Mydeimos. I'm tired of speaking with this silly lion.

**Mydei:** What about the Council's informants?

**Krateros:** Those two hyenas are nothing but scavengers of rotten meat. They couldn't bite even if they tried. They can follow us if they want to. Let's go.

**Verax Leo:** ...Wait, so how in the world did Chryseus Leo get mounted on the wall!?

## Follow Krateros to a Quiet Corner...

**Krateros:** Keep up with us, you hyen... oh, sorry, I meant officers.

**Scouting Soldier:** Hey, old man, how dare you—

**Distressed Soldier:** Calm down, calm down!

## ...Prepare to Strike

*[Approach Krateros]*

**Scouting Soldier:** ...Wh—Why have you stopped?

**Krateros:** This is a nice spot for a private chat.

**Mydei:** Shall we, sir?

**Krateros:** Let's do it!

**Distressed Soldier:** Wh—What are you up to!?

**Scouting Soldier:** S—Someone! Help m—

**Krateros:** Hmph... Some privacy at last. So, tell me, why have you come to seek this old man's counsel?

**Mydei:** I came to discuss... the future of the Kremnoans.

**Krateros:** Interesting. I heard the Coreflame of the Lance of Fury has been restored — though not by your hand — and you're even considering giving up Nikador's divine power. Is this true?

**Mydei:** ...Those rumors are not entirely groundless.

**Krateros:** In other words... you did entertain the thought of giving up the throne of Kremnos and forsaking your people.

**Mydei:** The divine power is not equivalent to the throne. The path of Strife is also not our people's only way—

**Krateros:** ...Enough with the word games! You, of all people, should understand the plight of the Kremnoans! Think about all the warriors of the Kremnoan detachment who left their homeland with you! Think about their children! ...Only the yearning for our former glory days has kept us going all this time.

**Krateros:** If they ever learn that the crown prince they look up to so much is actually toying with the notion of stepping down... think of the disgrace it would bring upon your departed mother, Mydeimos.

**Krateros:** You'd best remember that she died for you because of Eurypon's schemes! To restore the glory of Kremnos!

**Mydei:** Since you've brought that up... Tell me, who is responsible for my father's death?

**Krateros:** Are you trying to shame me, Mydeimos? I may be old, but I haven't become so decrepit that I've forgotten it all. Of course I remember that Eurypon died when the Kremnoan detachment surrounded him. You drove the spear into his chest with your very own hands.

**Mydei:** That was merely the final outcome. Do you still not see it? What led my parents and our people to their downfall is none other than this Strife we speak of. The quest for glory, the tenet of "Valorous Death Before Glorious Return"... This is the creed of every Kremnoan, no matter whether these beliefs are justified or not.

**Krateros:** ...Don't be ridiculous. The only thing that could slay a king is a spear... Even an infant knows that much.

**Krateros:** I swore to your mother that I would guard your crown with my life... I never foresaw that the son of Gorgo himself would be the first to turn his back on the Kremnoan spirit.

**Krateros:** Gorgo... Your mother bore that name, the name of the great founder of Castrum Kremnos, and she upheld that name with honor. If you choose to turn your back on her legacy like a wretched deserter... do not fault me for withholding my loyalty, Mydeimos.

**Mydei:** I came to discuss the future of our people with you, but... it appears this is not the right time yet.

**Krateros:** Go, Mydei... Hah, that's what those Chrysos Heirs call you, isn't it? Go down the path you have deemed correct. Deep down, you have always been one to do as you please, and I am well aware that no one can deter you once you've made up your mind.

**Krateros:** But don't you ever dream of renouncing the traditions of Kremnos... We may reside in Okhema now, but we remain eternally bound to Strife by blood.

**Mydei:** Bloodlines no longer hold any significance in this era of destruction.

**Krateros:** My young lord, always bear this in mind: Never reveal your vulnerabilities to anyone. A lion should never dwell amidst its prey... Especially when it wields power enough to dominate the entire hunting ground.

---

### Flashback: Gorgo's Duel

**Gorgo, Mydei's Mother:** Eurypon, the boy did nothing wrong! This is murder! Do not sully the noble name of Kremnos with the blood of an innocent child! You mustn't reveal your weaknesses to the enemy!

**Old King Eurypon:** Enough! My decision is final. We must use this child's life to preserve the soul of the great Nikador. We must... save Castrum Kremnos.

**Gorgo:** Don't be absurd! Those tiny hands lack the strength to even lift a spear! Do you truly believe him a threat to Castrum Kremnos!? You'll be ending the bloodline of Kremnos if you do this. Our millennia-old glory will become nothing more than a joke!

**Eurypon:** Have you forgotten that we Kremnoans place no value in bloodlines? It is through pure bloodshed and slaughter that the kings of Kremnos have ascended to the throne... As for our millennia-old "glory"... it has always been a joke in my eyes. Glorify it all you want, but it will not alter the nature of slaughter. Those who revel in it are but murderers. They are no more noble than the most monstrous beasts in Amphoreus.

**Gorgo:** Enough with your words! Among all the kings of Kremnos, which one did not inherit the crown only after plucking it from the lifeless body of his father? But listen to yourself now! Do you truly believe you can cleanse the blood from your hands through mere words alone?

**Eurypon:** Nay, quite the contrary. I will end this cycle of bloodshed... Starting with this child. With these bloodstained hands, I will end it all.

**Gorgo:** Your failure is inevitable, Eurypon! You are just a coward who can only raise his blade against his own child! A beast that murders his own kin! Royal Wing Elites and Ephors of Kremnos, you cannot sit idly by and watch this atrocity unfold! If you consider yourselves the honorable sons and daughters of Gorgo, then take up your spears and join me in putting an end to this bloody charade!

**Eurypon:** ...Does anyone else have any objections? If so, come forward with your spear and prove your mettle!

**Magistrate:** ...Understood. Five... Four... Three... Two... One.

**Eurypon:** It appears there are no objections. Then, in accordance with the Kremnoan Council's principle of tacit consent, the decision is final. With all present as witnesses, this child shall descend into the Sea of Souls, where he will nourish the Lance of Fury and join the fallen heroes. May fate and the gods await your arrival... My son... Mydeimos.

**Gorgo:** Stop!

**Eurypon:** If you have more to say, then speak. On account of the life we have shared together, I grant you this one final chance.

**Gorgo:** With the Blade of Fury above us and the Council bearing witness, I, Gorgo, hereby move to challenge the crown in accordance with the laws of Kremnos! O unworthy king, in the name of the Council of Elders, I demand that you duel me!

**Eurypon:** Heh... Very well. We shall see who the Kremnoan blade strikes down.

**Gorgo:** Mydeimos, my son... They all tell me to forget... But how could I ever? The son of Gorgo... will be crowned in blood. If there is no Kremnos without the crown... then I shall seize the crown and smash it to pieces to bring the people to their senses.

*The mother roared in anger. The armies remained in silence. Only the cries and the waves of the Sea of Souls echoed.*

---

> *Returning to the Trailblazer's POV...*
> *When you have a chance to make a choice, make one that you know you won't regret.*

---

## Mission 2 Summary

**Key Characters:** Mydei, Tribbie, Krateros, Gorgo, Eurypon, Kremnoan children
**Key Events:** Mydei confronts Krateros about the future of Kremnos. Krateros adamantly insists Mydei must become king. Flashback reveals Gorgo's tragic duel with Eurypon to protect the infant Mydei.

---

# Mission 3: Grove, Wherefore Are the Wise Silent

**Perspective:** Trailblazer | **Location:** Okhema → Grove of Epiphany

*(Aglaea presents the Trailblazer and Dan Heng with the Dew of Divine Blood, proposing an alliance. Hyacine arrives from the Grove. The Trailblazer, Castorice, and Trianne journey to the Grove — only to find it overrun by the black tide.)*

## Speak with Castorice

*[Now, in your private bath chamber]*

*Ever since the battle with Nikador, you haven't slept so soundly in ages. Even if Death itself came to rouse you, you'd proudly retort: Why does life slumber? Because the bed is warm... Yet, a chill from the River of Souls wafted by, a sensation hauntingly familiar.*

**Castorice:** Mr./Miss (Trailblazer), you're awake.

> *(Trailblazer)* ...No wonder I felt a chill.
> **Castorice:** Is the room too cold?
> *(Trailblazer)* ...Castorice, why does life slumber?
> **Castorice:** ...That's a complicated question. I'm not sure I can answer that.
> *(Trailblazer)* ...Why are you here?

**Castorice:** I apologize for arriving uninvited. I saw that you were still asleep, so I took the liberty of waiting nearby. I bring a message from Lady Aglaea. She has prepared a gift for you and Dan Heng, and wishes to present it to you in person.

> *(Trailblazer)* A gift? Gimme, gimme!
> *(Trailblazer)* What are we waiting for? Let's go!

**Castorice:** I'm glad you're in good spirits. Alright, let's set off.

## Speak with Aglaea

**Dan Heng:** You're finally here, (Trailblazer).

**Aglaea:** Welcome, Cas. And you as well, Trailblazer from beyond the sky.

> *(Trailblazer)* You're up so early, Dan Heng!
> **Dan Heng:** You would've been, too, if you hadn't stayed up so late. But what matters is that you got a good rest.
> *(Trailblazer)* I didn't expect you to call me that.
> **Aglaea:** Your companion here kindly explained the meaning behind the name to me earlier. Through him, I've come to understand that you and your friends walk the paths of Kephale and Janus in places beyond the sky. Addressing you appropriately is the least I can do as a show of respect.
> *(Trailblazer)* The gift! Gimme the gift!

**Aglaea:** For all that has happened, it was never our intention to drag you two into the battle against Nikador and jeopardize your safety. To express our gratitude for your kind Trailblazing endeavors, we would like to present you with the highest honor of Okhema.

**Aglaea:** This is the Dew of Divine Blood, brewed from crops nourished by the blood of the Titans. It is said that only twelve bottles existed. The last three bottles are now being kept in the treasure vault of Okhema.

**Aglaea:** Back in the days of prosperity, cities fortunate enough to acquire it regarded it as one of the greatest treasures ever. Unsealing it during a ceremony held in honor of two cities' diplomatic ties was the highest form of respect one could show the other.

**Aglaea:** And now, in keeping with tradition, Okhema dedicates this drink to our esteemed guests from beyond the sky in appreciation of what you have done for us.

> *(Trailblazer)* My hand is trembling under the weight of this gift...
> *(Trailblazer)* I'm not of drinking age yet.
> **Dan Heng:** ...The Express has house rules about drinking, and even I'm not exempt to them.

**Dan Heng:** This precious gift isn't simply a token of gratitude though, is it, Lady Aglaea?

**Aglaea:** Very perceptive, Mr. Dan Heng. Your heroic deeds have proven that you come in good faith. With the Dew of Divine Blood as testament, we wish to forge an alliance with the Trailblazers.

**Dan Heng:** With all due respect... won't forging an alliance with the Chrysos Heirs embroil us in the conflicts within Okhema? I'm sure you can understand where our misgivings come from, Lady Aglaea.

> *(Trailblazer)* Right, we need to think about this first.
> *(Trailblazer)* Waaaah, my gift! My gift...
> **Dan Heng:** ...Wow, you seriously took a liking to the gift.

**Dan Heng:** Having said that, Lady Aglaea, please don't misunderstand, we will still do what we can to assist you in the Flame-Chase Journey. It's just... I've heard of the friction between the Chrysos Heirs and the Council of Okhema. As outsiders, we are wary of getting caught up in this conflict—

**Hyacine:** Wow, Grayie and Dannie have sharp eyes indeed! You'd make outstanding members of the Twilight Courtyard!

**Hyacine:** No need to worry, by the way. I can tell from Lady Aglaea's tone of voice and micro-expressions that she's being genuine. Not only are you guests from beyond the sky, but you've also done so much for Okhema. You're practically heroes to us all! Lady Aglaea would never subject you to Aquila's judgment.

**Dan Heng:** Hmm? You are...?

**Aglaea:** Hyacine. Thank you for taking care of the wounded over the past few days.

**Hyacine:** It's no trouble at all! The patients are very cooperative when we attend to them. I'm just thrilled to see them all going home healthy again. And ooh! It's Cassie! I've missed you!

> *(Trailblazer)* Who is this...?
> *(Trailblazer)* Grayie? Dannie?
> **Hyacine:** Aren't they just the cutest nicknames? Hehe.
> *(Trailblazer)* Cassie?
> **Castorice:** Um, Miss Hyacine, about that nickname... Could you—
> **Hyacine:** Aw, don't be shy. It's a cute nickname!
> *(Trailblazer)* Is Aglaea's nickname Aglie?
> **Aglaea:** Hehe...
> **Castorice:** Mis—!
> **Hyacine:** Wah! You can't say that! Lady Aglaea should always be "Lady Aglaea"!

**Dan Heng:** This girl... She's a natural at making friends.

> *(Trailblazer)* She reminds me of an old friend with pink hair.
> *(Trailblazer)* So am I!
> **Dan Heng:** I'll let you take it from here, then.

**Hyacine:** Hehe, as an acolyte of Aquila, I'm here to bring healing light to the world. Plus, I've heard you're also children of the distant skies! Fate must have brought us together! Can we be friends? I'd love to hear your tales of the sky! And ooh, it's a rare occasion that Okhema presents such an invaluable gift to guests. Lady Aglaea, may I have the honor of tasting it, too?

**Aglaea:** Of course you may. Esteemed guests of Okhema, please believe me when I say that this gift carries no hidden agendas. As for the matter of the alliance, you need not give me an answer here and now.

> *(Trailblazer)* Well, if you insist...
> *(Trailblazer)* Ohh, she's here to help Aglaea recruit us.
> **Hyacine:** Haha, you're mistaken! The capable Lady Aglaea doesn't need my help with things like this.

**Dan Heng:** ...I see. In that case, we will accept this gift from Okhema. We welcome the chance to talk with you, Lady Hyacine.

**Hyacine:** Yay! Then I'll get started on my questionnaire!

**Dan Heng:** Pardon the question, but I've been meaning to ask this for a while: micro-expressions, tone of voice, questionnaires... Are these all part of the usual skill set for Aquila's priests?

**Aglaea:** Allow me to do the honors. This young lady is Hyacine, assistant lecturer of the Nousporists at the Grove of Epiphany and head nurse at the medical institution known as the Twilight Courtyard. Many of the Chrysos Heirs suffered injuries during Nikador's attack on Okhema, so the Grove sent Lady Hyacine to treat the wounded in Okhema.

**Hyacine:** But what I'm really good at is helping people sort out what ails their mind and spirit. If you're ever feeling troubled, come find me! A little sunbathing in the courtyard will chase all your worries away!

**Dan Heng:** Ah, so you're a therapist. Thank you, we will keep that in mind.

---

**Hyacine:** Well, it looks like everything's sorted out now! The patients have also all recovered. I think it's time for me to head back, Lady Aglaea.

**Aglaea:** I would love to keep you in Okhema for a few more days, but I would hate to provoke the ire of the Grove. As it happens, Okhema intends to send a messenger to the Grove for updates about the research on the black tide. We also want to communicate our desire to discuss the retrieval of Cerces' Coreflame at the earliest convenience.

**Hyacine:** That... sounds pretty serious. Lady Aglaea, you can't be asking me to...

**Aglaea:** No need to fret. We won't put you on the spot. Trianne will be going there as the diplomatic messenger of Okhema, and Castorice will be accompanying her.

**Castorice:** I happen to have a few questions for Professor Anaxa as well, regarding the missing Titan Thanatos.

**Dan Heng:** Since this involves Okhema's diplomatic affairs, we'll give you some privacy.

> *(Trailblazer)* Let's go out and play!
> *(Trailblazer)* Back to bed again? Boring!

**Aglaea:** If you're not keen on just sitting around, (Trailblazer), why not go with them? The Grove is a picturesque place, perfect for sightseeing.

**Hyacine:** That's a wonderful suggestion! Come visit the Grove, Grayie! I'd be delighted to show you around!

**Dan Heng:** Sounds good. Gaining more insight into the customs and geography of different regions of Amphoreus is also part of Trailblazing.

**Aglaea:** In that case, do bring this spindle along with you. This tool, called the Weft, is used to spin thread and has been passed down in my family through generations. Though it doesn't see much practical use nowadays, it's become a symbol of great significance. In this respect, it is the perfect token to represent my will. If you encounter trouble at the Grove, just take this out and show it to them.

**Aglaea:** While you're in the Grove, the golden thread of the Weft can also render all things around you visible, regardless of whether they're corporeal or not, allowing you to see things as I would. Castorice knows this, too. Make good use of it. Trianne is already waiting for you at the outskirts of Okhema, so I won't keep you any longer. May your journey be smooth.

---

## Journey to the Grove

*(The group departs Okhema. Trianne leads the way. On the Woven Trail, Castorice explains Mnestia's legend. They arrive at the Grove to find it eerily silent.)*

**Castorice:** Something feels off... The Grove has always welcomed scholars. So too would Cerces give us her delicate leaves and extend her branches in greeting. Yet... it seems both the Grove's messengers and the Titan are indifferent to our arrival.

**Mem:** For now... let's look around and see if we can find out what's happened.

---

## The Grove Under Siege

*(Using the Weft's golden thread, Castorice reveals shadows of dead White Dryads. Mem reads their faint memories: "Black... Cloak... Sword... Toward the Great Tree...")*

**Castorice:** ...I have a bad feeling about this. The deathly fog of Thanatos... is fast approaching.

*(The group encounters black tide creations — Tide-Eroded Blades roaming the halls. They learn the black tide has invaded the Grove.)*

**Castorice:** To think the black tide has spread this quickly to the Grove despite its remote location... I'm afraid a world where Strife has fallen is far more dangerous than we ever imagined.

*(They report to Aglaea via Tribbie's telepathic link. Aglaea orders them to find Anaxa and secure Cerces' Coreflame.)*

## Anaxa's Alchemical Messages

*(At a sealed gate, Mem tries to use Oronyx's power to open it.)*

**Anaxa (voice from alchemy):** Are you serious? Just a mere door, and your first instinct is to call on the gods? Before you try unlocking the door, perhaps you should first find a way to clear the fog that clouds your vision.

**Mem:** You scared me! Are you... the echoes of a memory?

**Anaxa:** My name is Anaxagoras, one of the Seven Sages of the Grove of Epiphany and the founder of the Nousporists. Before we go any further: Rule number one, do not call me Anaxa.

**Mem:** Anaxago... Anax... Ugh, I'll just stick to Anaxa.

**Anaxa:** Rule number two: Never interrupt me. Silence is golden.

**Anaxa:** The person standing here and conversing with you right now isn't the vestiges of a memory. Rather, it is the culmination of the greatness of science and the pure, irrefutable, and undeniable exalted truth. Through the wonders of alchemy, I have shattered my soul and transmuted it into gold before burying it in this spot.

**Anaxa:** While the black tide was still approaching the Grove, the sages found a way to evacuate the vast majority of the scholars. They are heading toward the holy city of Okhema as we speak. Only a small fraction of the scholars stayed behind with me to defend the Grove. If all goes well, Cerces' Coreflame will reach Okhema before long... But since you have accessed this message, something unforeseen must have occurred. For now, you should continue onward to the Luminary Throne where you may retrieve the Coreflame... and our mortal remains.

**Anaxa:** "And now, the objective is complete. That is all."

## The Mysterious Calypso

*(In the library, a mysterious singing voice is heard. They find a statue... that speaks.)*

**Calypso:** Hehe... Such a lively little bunny. You even smell a little familiar.

**Castorice:** ...Who are you? Keep your distance and identify yourself. Otherwise, you'll face the consequences.

**Calypso:** The scent of Thanatos... I recognize you. Aidonia's renowned Goddess of Death.

**Castorice:** Since you are aware, stop provoking the authority of Death. Answer my question.

**Calypso:** Hehe, baring your fangs at me... How cute. Just call me Calypso. I greet you on behalf of the Seven Sages and the Lotophagists.

*(Castorice tests Calypso with questions about the Grove. Calypso answers correctly and reveals: Anaxa is still alive, recuperating at the Luminary Throne. She guides them to retrieve the Golden Bough of Vows, awaken the heart of the water wheel, and ascend to the throne.)*

## The Trial of the Butterfly

*(At the Dome of Devotion, the Butterfly of Divine Mind is missing. Mem suddenly begins to overheat, and Trianne cries out in alarm.)*

**Trianne:** Memmy... is about to burst into flames!

*(They rescue Mem from magical beasts and use the Golden Bough of Vows to collect Mnestia's embers. Presenting them to the butterfly, a path opens.)*

**Calypso:** Heh... All of you have indeed passed the trial.

**Mnestia's Illusion:** *Titan's sad cries*

**Calypso:** Of course, our promise still stands... But now... It's time for me to sacrifice myself. If the west wind ever ends, let that be the place where we reunite. Farewell... my love.

**Castorice:** Lady Calypso, this is...

**Calypso:** Haha... It's nothing much. Thank you so much for your help. Now it's time for me to fulfill my part of the promise.

**Castorice:** Well, in that case, I can start... You're... actually Cerces, right?

**Mem:** Wh—What's going on? You're the Titan?

**Cerces:** Oh my, the children of humanity... have passed the final trial at last. I was wondering when you were planning to expose me. How did you know?

**Castorice:** The riddle-like trials, your distrustful yet sincere character, referring to Mnestia as your love, and... The head of the Lotophagists is actually called Medea and not Calypso.

**Cerces:** Since you knew from the start that I was not who I said I was, why did you wait until now to expose me?

**Castorice:** Because I did not believe that Cerces would walk this world in a human form. I was also afraid that the Titans were under the control of the black tide and would do us harm... Also, "to make a claim, one must have evidence" — this is the precious knowledge that I acquired during my time at the Grove.

**Cerces:** Heh... Excellent. To think we were able to gain a new chance at life in the midst of death — fate truly is a mysterious thing.

**Cerces:** I split my Coreflame into three. I hid one within the Golden Bough of Vows, and sealed another in the amber along with Mnestia's remaining embers... As for the last one... It's currently in Anaxa's body, which is in dire need of repair.

**Cerces:** Especially that heretic named Anaxa. He did not even hesitate to tear his soul apart and use it to perform a miracle. He trapped all the creations of the black tide within the Grove so that they would not be able to harm others. His way of thinking was so out of the ordinary that I felt it would be a waste for him to meet his demise in the black tide. And so, I decided to save his life.

**Cerces:** Of course, this also meant that I was able to conceal myself and remain hidden... Well, that's also an "equivalent exchange," right?

**Cerces:** I just need you to buy me some time against the warrior's blade... Once the Coreflame is re-formed, I'll be able to show my hand.

## The Black-Robed Swordmaster

*(At the Luminary Throne, they find Anaxa's soul and face the Flame Reaver.)*

**Mem:** The burning paradise, the shattered sun, and... ...Carnage. Death and destruction.

**Flame Reaver:** ...

**Castorice:** Everyone, brace yourself... This must be the hunter reborn from the black tide that Cerces was talking about... The black sword and cloak... The owner of the piece of cloth... The north wind that sent over the deathly fog of Thanatos.

**Flame Reaver:** You're not... demigods. Stand down. Or die.

**Mem:** Quick... run! It's just us... We won't be able to defeat them...

> *(Trailblazer)* Don't worry, I'll protect everyone.
> *(Trailblazer)* Things will get better when the Titan attacks.
> **Castorice:** That's right, let's do our best to buy time for Cerces.

**Castorice:** Only this time... may Death protect us!

*(Battle against the Flame Reaver. Anaxa/Cerces joins the fight. Trianne opens the Century Gate to save everyone — at great cost to herself.)*

**Trianne:** Century gate... Open!

---

## Mission 3 Summary

**Key Characters:** Trailblazer, Castorice, Trianne, Hyacine, Aglaea, Anaxa, Calypso/Cerces, Mem, Flame Reaver
**Key Events:** Alliance proposed with Okhema. Hyacine introduced. The Grove is discovered overrun by the black tide. Anaxa leaves alchemical messages. Calypso is revealed as Cerces in disguise. The Flame Reaver emerges — a black-robed swordmaster hunting Coreflames. Trianne exhausts her divine power opening the Century Gate to save everyone.

---

# Mission 4: Lamentations, Bring Not Empty Tears

**Perspective:** Trailblazer | **Location:** Okhema

*(After the battle at the Grove, the group returns to Okhema with Anaxa and Cerces' Coreflame. Before seeing Aglaea, Anaxa visits the families of fallen scholars. The Trailblazer reunites with Dan Heng.)*

## Return to Okhema

**Castorice:** Phew... That was a close call. Thank goodness that we returned to Okhema unharmed.

**Trianne:** Ugh... Little Cas, my head... It still hurts. Sorry... I know you... told me... not to open the gate...

**Castorice:** Please don't blame yourself, Lady Trianne. If it weren't for you, we would've already met our end at the Grove.

**Anaxa:** All this noise and commotion... Okhema hasn't changed a bit, has it?

**Castorice:** Are you... Professor Anaxa?

**Anaxa:** There's no need for doubt. The Titan no longer speaks. It is I, Anaxagoras of the Nousporists.

**Anaxa:** I'm a survivor who witnessed the entirety of the disaster, as well as the defenseless bearer of a Coreflame. Are you going to bring me to Aglaea to fulfill your duty?

**Anaxa:** But I have some things to take care of first. The families of some of my fellow Grove scholars live in the holy city. Before we meet Aglaea... I want to visit them.

**Castorice:** Because Lady Aglaea... will probably be against it.

**Anaxa:** Heh... Let me guess. That woman will not only prevent me from visiting the families of the deceased, but will also suppress any information about the Grove. She's always been that cold-hearted. My fellows at the Grove gave their lives defending the Coreflame and fighting the black tide alongside me. Their families... deserve to know the truth.

## Visiting the Families

*(Anaxa visits three families. A Kremnoan widow accepts her husband's death with warrior's composure. An old father learns both his daughters perished — and calls them heroines. A young man, Titus, rages at his stubborn father who died at the Grove.)*

**Woman With Gentle Expression:** So... did he manage to defend the Grove? ...I see. I'll select some of his possessions and pick a nice resting place for him. I come from Kremnos. Death... and sacrifice... are things I have learned to face with composure.

**Old Fabio:** ...Don't put it that way. Even if my Artakama wasn't one of the Chrysos Heirs mentioned in the prophecy, she was still a heroine, wasn't she?

**Titus:** Heh... Just up and left me behind, that old man... I've been telling him for ages to stay in the holy city and enjoy his retirement. But no, he just had to go off to that Grove and mess around with those scholars. ...That bullheaded old man! Stubborn as a mule!

**Anaxa:** That is it. That's all the colleagues' families that I remember.

## Reunion with Dan Heng

**Dan Heng:** Long time no see. I've heard about what happened from Phainon... You've been through a lot.

> *(Trailblazer)* Not at all. It's all in service to Trailblaze.
> **Dan Heng:** Heh... I wasn't expecting Amphoreus to temper the will of the Nameless.

**Dan Heng:** I was organizing logs. I also asked Hyacine for some research material from the Grove. I discovered something interesting. Do you remember that Amphoreus's sky was sealed away by a Titan? Aquila's presence keeps this world isolated from the rest of the world beyond the sky. It seems Hyacine's ancestors were the Sky Priests who worshipped Aquila. Perhaps she can give us more clues to find a way back to the Astral Express.

**Dan Heng:** You look tired. You should get some sleep before we set off tomorrow... Oh, by the way, I heard some rumors... If you're going to wander around, I suggest avoiding the hot bath.

---

## Mission 4 Summary

**Key Characters:** Trailblazer, Castorice, Anaxa, Dan Heng, Trianne
**Key Events:** Anaxa visits the families of fallen Grove scholars. Aglaea is too busy to receive them due to political tensions. The Trailblazer reunites with Dan Heng who shares research on Aquila.

---

# Mission 5: Memories, Veiled in Blazing Mist

**Perspective:** Tribbie (Passages' Ripples) | **Location:** Okhema

*(Tribbie senses Trianne used divine power again. She goes to the baths with Aglaea to unwind. There they discover Phainon and Mydei's ridiculous sauna competition. Later, Tribbie and Trinnon confront Krateros who has abducted Trinnon to force access to the Strife trial.)*

## The Baths Incident

**Tribbie:** Trianne...?

**Aglaea:** What's wrong...? Is there trouble at the Grove?

**Tribbie:** Yes, I sensed something... It was fleeting, but very strong... It feels like they're in some big trouble. ...Trianne used the Century Gate again.

*(Tribbie and Aglaea head to the baths, only to find multiple bathers passed out from the heat.)*

**Hyacine:** I actually just came to relax... But as soon as I got here, I saw all these people lying on the ground. I've examined them, and they don't seem to be seriously ill. It feels like... they've just spent too much time in the hot water.

*(They discover the culprits: Phainon and Mydei, who had a "super hot bath" endurance competition. Phainon won 27 to 25 in terms of escorts of fainted bathers home.)*

**Aglaea:** ...What a spectacle of folly.

**Phainon:** This... This isn't fair... You are wearing... way less... than I am...

**Hyacine:** ...Is this the latest trend now? Getting into the baths while dressed in full armor?

**Mydei:** Don't look at me like that... It was he who challenged me. There is no word for "flee" in the Kremnoan language.

## Phainon and Mydei's Conversation

**Phainon:** Yes, I saw it all. Aedes Elysiae ablaze, with everyone — my family, friends, and my kin — lying in a sea of flames. A blood-red half-sun hung in the sky, just like on that day. And before my eyes, that murderer... killed Cyrene.

**Phainon:** But I saw its form this time... A black cloak, an eerie mask, and a broken giant sword that carried an ominous aura... I fought it in the trial. But even though I've been fighting, improving, and resolutely getting stronger all this time... I still couldn't defeat it.

**Mydei:** You were blinded by hatred and almost lost yourself in that trial.

**Phainon:** That's right... And that's why I am truly thankful to you, Mydeimos.

*(Mydei shares the story of his five fallen comrades: Perdikkas, Leonnius, Ptolemy, Peucesta, and Hephaestion.)*

**Mydei:** They died on the battlefield before the Kremnoan detachment managed to join Okhema.

**Hephaestion:** "Farewell, my dear friend... You must... lead us back home..."

## Krateros' Abduction

**Tribbie:** De! We've got a big problem! Big problem!!! Hurry up and go save Trinnon! She... She... ...She got abducted by Krateros!

*(At the Vortex of Genesis, Krateros has forced Trinnon to bring him to the Strife trial.)*

**Krateros:** Because I don't want to wait anymore. Your hesitation made me desperate. If you want to run away from your destiny to become king, then keep running. Someone will eventually stand up and fill in the gap left by Strife... Then they will lead our people home.

**Krateros:** You're a hypocrite... and a megalomaniac! The prophecy of genesis and the Flame-Chase Journey are just excuses for you to seize power.

*(Trinnon proposes showing Krateros the source of the prophecy using the Trailblazer's power to replicate past memories. Krateros accepts. Mydei later seeks advice from Grand Craftsman Chartonus.)*

**Chartonus:** A different kind of Kremnoan, you truly are...

---

*Switching to Tribbie's POV... In order to reconcile the Kremnoans and the Okhemans, Tribbie, Trianne, and Trinnon decided to visit the Titan and retrieve their memories...*

---

## Mission 5 Summary

**Key Characters:** Tribbie, Aglaea, Phainon, Mydei, Hyacine, Krateros, Trinnon, Chartonus
**Key Events:** Phainon and Mydei's sauna competition. Mydei reveals the deaths of his five comrades. Krateros abducts Trinnon to force the Strife trial. Tribbie proposes using Oronyx's power to show Krateros the prophecy's source.

---

# Mission 6: Passages, Knocking Echoes in Dreams

**Perspective:** Tribbie (Passages' Ripples) | **Location:** Tribbie's Dream → Abyss of Fate

*(Tribbie enters a dream of her childhood as Tribios. She relives memories of her mother Mortis, the prophecy, and the music box. Then Tribbie, Trianne, and Trinnon go to the Abyss of Fate to seek Oronyx's help in restoring memories — only to encounter the Flame Reaver there.)*

## Tribbie's Dream

**Tribios:** Momma, Momma! I had a dream last night.

**Gentle Mother (Mortis):** Oh? Now, what did you dream about, my darling Tribios?

**Tribios:** I had a dream that I turned into many mes! Then we made the moon into a ship and made the stars into our sails! Then we floated on the ocean and let the wind blow us in any direction it wanted!

**Gentle Mother:** Well that sounds like a lovely dream.

**Tribios:** Yeah! The ocean and the sky were really, really dark, but there were so many of me that I wasn't scared at all. Because we'd all sing together!

**Tribios:** The ocean wind blew us onto an island where the wind tasted like flowers. There were bleating sheep and chirping birds inviting us to be their guests. There were so many animals on the island, but none of them ever fought!

**Gentle Mother:** Janus' Holy Maidens can receive guidance from the god of passages. Perhaps what you saw in your dream is a divine land somewhere in Amphoreus.

**Tribios:** Because... on that same island, I saw a dark mountain on the other side of the ocean. And it was very, very tall. The mountain looked alive, and it kept getting closer to the island. Then I realized that it wasn't a mountain, but a very, very tall wave made of water... When the wave smashed against the island, it looked like it was going to eat the island up. The small animals tried to chase it away, but they couldn't stop it... Then there was a "bang!" and I woke up.

**Gentle Mother:** Yes... Unfortunately, it does exist in Amphoreus, but it's very far away from our temple. We call it the "black tide," though it has nothing to do with water. It has no shape or form, but it can swallow up animals, humans, and even Titans... turning them all into monsters.

*(Mortis sings the prophecy: "Happiness abounded in this lush land by gods chosen..." until the words become corrupted by the black tide.)*

**Gentle Mother:** Hurry! Run! Tribios, run! The black tide has arrived!

## The Prophecy of the Music Box

*(Tribbie places dolls on the music box — each representing a Chrysos Heir. The Gentle Mother foretells the coming of Aglaea, Phainon, Mydei, Anaxa, and names Tribbie, Trianne, and Trinnon.)*

**Gentle Mother:** There will be an amazing captain on that big ship. She's cheerful, optimistic, bold, and cautious... I think that person lives in a beautiful temple that sits atop a hillside covered in golden fig trees. There's a noble girl there who's very smart but also very delicate.

**Gentle Mother:** I believe one warrior hails from a lovely village where bulrushes flourish, while another comes from a magnificent royal city. Though each has their own troubles, both are ready to lend their strength for the ship's long voyage.

**Gentle Mother:** Cerces also favors children who try their best. They will send a wise scholar as everyone's teacher to help you reach your dreams.

**Tribbie:** This way, they'll always stay on course!

## Tribbie and Aglaea

*(Tribbie wakes from the nightmare.)*

**Tribbie:** ...Are we still in a dream?

**Aglaea:** Did you have a nightmare?

**Tribbie:** ...Maybe. But it's been a long time since we had any dreams. We... had a dream about Mama.

**Tribbie:** Even if we refrain from ever using the power of the Century Gate again... her soul continues to slowly drift away from her body. There isn't much time left.

**Tribbie:** Souls will be spent until they dissolve into dust — such is our fate. We can choose how our branches will perish in a way that is most beneficial to the Flame-Chase Journey.

**Tribbie:** Don't feel sad about saying goodbye to us. We have already agreed on this, right?

**Aglaea:** It won't be long before I forget what sorrow tastes like.

**Tribbie:** So, what would you like for breakfast, Agy? Do you remember when we first met, Agy? You were still a little one, and we caught you secretly eating oatmeal late at night...

**Aglaea:** Heh, while my emotions might be fading, those memories are still as vivid as ever, teacher.

**Tribbie:** Then... See you tomorrow, Agy!

## Phainon and Anaxa

*(Meanwhile, Phainon visits the confined Anaxa.)*

**Phainon:** Could you please teach me everything you know about the black-robed swordmaster?

**Anaxa:** Hmph. Rumors sure travel fast. Unfortunately I, too, know nothing about it. I can only tell you that it is clad in a black robe and wields a greatsword... At least, it looks like a greatsword. It's shaped like a twisted half-sun... And a peculiar dagger resembling a crescent moon.

**Phainon:** I was right... It is this thing. The one who torched Aedes Elysiae to the ground... and killed everyone.

**Anaxa:** Don't try to be a hero. No one in Okhema stands a chance against that thing right now.

**Anaxa:** That incredible power doesn't seem to be granted by any Titan. It's possible. Much like the black tide, no?

**Phainon:** ...Nonetheless, it's an enemy we must overcome.

## The Abyss of Fate

*(Trianne, Tribbie, and Trinnon journey to the Abyss of Fate to seek Oronyx's help restoring memories.)*

**Tribbie:** We hope to present the full truth to everyone, without hiding anything. Since Janus caused the fragmentation, we can only turn to another Titan, Oronyx, for help.

*(Trianne instinctively finds a letter — the "Saffron Secret Recipes" — revealing a conspiracy to eliminate Tribios' mother, the "rose myrtle.")*

**Trinnon:** Is it possible that we were already noticed by Oronyx and entered their trial?

*(They search for "saffron" as an offering. At every turn, they encounter visions: Aglaea warning "It's a dead end ahead — turn back, teacher," Mydei speaking of separation, Castorice saying "Separation and death are two sides of the same coin.")*

**Trinnon:** Something feels off... Tribbie, don't you think the temple is a little too quiet? Is Oronyx... really putting us through a trial?

*(When they reach the podium, Oronyx has disappeared. Trianne finds a piece of burnt cloth — the same cloth from the Flame Reaver. The Flame Reaver has arrived.)*

**Trinnon:** Listen — footsteps, fast ones. Three or four people, coming this way. Come on, we need to hide! Whoever they are, we can't let them see us!

**Trianne:** Tribbie, Trinnon... Come check this out. What's this? Trianne feels like... it's so familiar.

*(Cutscene: Trianne flies up to confront the Flame Reaver.)*

**Trianne:** Fly!
**Tribbie:** Trianne?
**Trianne:** Tribbie...
**Trianne:** See you tomorrow.

---

*(Aftermath: Tribbie and Trinnon are found collapsed. The Flame Reaver has taken Oronyx's Coreflame. Trianne is missing. Phainon organizes the pursuit.)*

**Phainon:** We were still too late. I fear something bad has happened to Oronyx's Coreflame.

**Hyacine:** Then, Lady Trianne...

**Tribbie:** She doesn't have much divine power left. We can barely sense anything...

**Phainon:** Everyone, we must take action now. We should split into two groups: One group will stay in the Abyss and meet up with Aglaea's reinforcements, then search for Trianne's whereabouts. The other group will come with me to pursue the black-robed swordmaster and recover the Coreflame.

---

## Mission 6 Summary

**Key Characters:** Tribbie/Tribios, Mortis, Aglaea, Phainon, Anaxa, Trianne, Trinnon, Flame Reaver
**Key Events:** Tribbie's childhood dream and the prophecy of the music box. The "Saffron Secret Recipes" conspiracy is discovered. Trianne sacrifices herself against the Flame Reaver. Oronyx's Coreflame is stolen.

---

# Mission 7: Nemesis, Scorched by Golden Blood

**Perspective:** Trailblazer | **Location:** Okhema → Castrum Kremnos

*(The heroes gather in Okhema. They plan to lure the Flame Reaver into a trap in Castrum Kremnos using the Trailblazer's power over time. Mydei, having completed his trial, arrives to deliver the decisive blow.)*

## The War Council

**Phainon:** We're back, Aglaea.

**Aglaea:** I already know the good news. Tribbie's safe return is proof of that. You should have come to me first, Phainon.

**Tribbie:** Agy, there's no need to scold Snowy... Okhema is currently in grave danger.

**Aglaea:** I know. It's beyond my imagination that the only two Titans humankind can still rely on fell in such quick succession... I've never seen the golden thread pulled this taut, as if it could snap at any moment.

*(Phainon outlines Anaxa's plan: lure the Flame Reaver to Castrum Kremnos, use Oronyx's power to open a passage to the past, and seal the Flame Reaver in the Maze of Time.)*

**Phainon:** That will be the key to our victory — We will use Oronyx's power to once again open a passage to the past and lure our enemy inside... Then, we'll "seal" the Flame Reaver in the Maze of Time.

**Aglaea:** Impressive. Oronyx has fallen, and Janus' divine power already belongs to Okhema. Once we take back the Coreflame, the swordmaster will have no means of escape. It's very clever, using the element of surprise instead of brute strength.

**Aglaea:** Can you do it, little one?

**Mem:** I just have to throw that black-cloaked guy into the past, and lock them there, right? With the memory fragments, I can open a door no problem. As for the rest... Well, let's just say that (Trailblazer) and I can do anything as long as we're together!

> *(Trailblazer)* That's right! We can do anything!
> **Mem:** Yeah! Can you feel their fervent gazes? This is a big deal! We can't let everyone down!

## Mydei's Decision

*(At the Vortex of Genesis, Phainon finds Mydei.)*

**Phainon:** I knew you'd be here.

**Mydei:** I heard you're about to set off on an expedition.

**Phainon:** That's right. It's going to be a tough battle, and our destination is... turns out to be Castrum Kremnos.

**Phainon:** You can entrust the front line to us this time. You can't afford to lose your upcoming battle either.

*(Mydei tells the story of Geocles the Mountainbreaker — a Mountain Dweller who burned his own village's forests to force his people to flee an impending war.)*

**Mydei:** It's simply because he took action and enacted change with his own hands. He didn't try to make everyone understand him, nor did he even waste time trying to make everyone happy. He started a great fire and burned the shackles of tradition to ashes, and then... forced everyone to march toward the coming of a new era.

**Phainon:** ...You've made up your mind, haven't you?

**Mydei:** I'll be leaving Okhema soon to fight the greatest darkness of this world... and to shoulder Nikador's destiny.

**Mydei:** So, listen well: If there comes a day when we meet again on the battlefield, and I stand opposed to the flame-chase... Remember to stab your sword into my back through my tenth thoracic vertebra. That's my weak spot, and the only way to kill me.

**Phainon:** ...You have my word.

**Mydei:** Go now. Your battlefield calls. Send that flame-thieving hyena to their death. But if you find yourselves with no other recourse, then pray to that blade in the sky... ...And loudly call out the name of the new god.

## The Battle of Castrum Kremnos

*(The battlefield is set. Anaxa has already prepared. Kremnoan soldiers fight the Flame Reaver. The Trailblazer, Phainon, Tribbie, and Mem begin the entrapment.)*

**Tribbie:** Once we take back the Coreflame, Janus' passage will open. When that happens, you must evacuate immediately. Don't stay behind.

**Phainon:** Let's go, partner! Today, destiny shall stand with us!

*(Cutscene: Mem opens the passage. The Flame Reaver is dragged into the past. Anaxa seizes the Coreflame.)*

**Anaxa:** Finally.

**(Trailblazer):** Mem... It's all yours!

**Mem:** Mem~

**Phainon:** Repent in the memories of the dead — Executioner!

*(Battle begins. Phase 1: The Flame Reaver is strong. At 10% HP, Tribbie opens the Century Gate.)*

**Anaxa:** At long last!

**Tribbie:** Century gate... Open!

**Mydei:** How embarrassing, "Deliverer."

**Phainon:** Heh. You didn't come down from the sky?

**Mydei:** This city is mine anyway... So why shouldn't I go through the front door?

*(Phase 2: Mydei, now the new God of Strife, joins the battle.)*

**Mydei:** Minion of the black tide, I, king of the Kremnoan legion, will be your opponent today.

**Cerces:** Long time no see... Nikador.

**Mydei:** Rejoice, for I grant you the honor of sharing your final resting place with Kremnos' departed heroes!

**Flame Reaver:** Vanity... leads to self-destruction. I am but sending a dynasty to its end.

**Mydei:** Well fought! That was a good opener to the ceremony!

**Mydei:** Now, we honor the fallen gods with this fight to the death!

*(Final blow: Mydei delivers the decisive strike.)*

**Flame Reaver:** ...It's time to end this.

**Mydei:** Come! The Kremnoans' spear always finds their mark — Fate itself shall forge my speartip!

*(Cutscene: Mydei ascends.)*

**Mydei:** Heroic souls of Strife, heed my call... I am the Lance of Fury... The agony this world needs! Witness this... A new god has come to Castrum Kremnos.

---

*(Returning to Okhema: the citizens are uneasy. Oronyx's Coreflame must be returned. Mem suggests the Trailblazer take on the trial of the Time Titan.)*

**Mem:** How about letting (Trailblazer) give it a try?

> *(Trailblazer)* I've been waiting for someone to say that, friend.
> *(Trailblazer)* So, you're okay with sentencing me to the gallows?

**Mem:** I'm serious! You're special to Amphoreus, and we all know that. Now, about Oronyx... The one projected me into this world and granted me this body... Isn't Oronyx just a little Titan even more capricious than a child?

---

## Mission 7 Summary

**Key Characters:** Trailblazer, Phainon, Mydei, Aglaea, Tribbie, Anaxa, Cerces, Flame Reaver
**Key Events:** The Flame Reaver is lured to Castrum Kremnos. Mydei ascends as the new God of Strife and joins the battle. The Flame Reaver is defeated. The Trailblazer is proposed as the candidate for Oronyx's Coreflame.

---

# Mission 8: Throne, End Those Long Years Forlorn

**Perspective:** Mydei (Remnants of Regal Sounds) | **Location:** Okhema → Castrum Kremnos

*(After the victory, Mydei makes his final decision: to renounce the Kremnoan throne, end the dynasty, and return home alone to fight the black tide.)*

## Speak with Krateros

**Krateros:** ...

**Mydei:** I see the Reaper has forsaken you, too, teacher.

**Krateros:** Hmph, it simply put my life in the hands of the Twilight Courtyard. That priest girl's medical talents are truly exceptional... She might be far from the ordinary girl we envisioned.

**Krateros:** But this isn't about me, Mydeimos. I saw it... You've finally decided to embrace your own fate.

**Mydei:** The power of Strife is stirring a tempest within me as we speak... My bones have turned into steel, and my blood is seething and ablaze. Past rulers of Kremnos could only aspire to this might, yet I have merged with it. I've made history, and henceforth, divinity and kingship shall coexist as one.

**Krateros:** Indeed. You've realized the aspirations of every former king of Kremnos. And now, you can at last bring our people home and reforge the glory of Kremnos.

**Mydei:** ...Unfortunately, I harbor no such desire.

**Krateros:** Wha—What do you mean by that?

**Mydei:** Over two millennia past, devotees of Nikador's might banded together beneath their feet and erected a city of their own. Ever since then, Kremnoans have served as the blades wielded by the god of war, following the Titan's path in its conquest. Yet, gazing upon our history through the lens of my newfound divinity, I now see it with unprecedented clarity.

**Mydei:** This history is sheer absurdity and inferiority. People surged onto the battlefield like ants, plundering and slaying for their own greed, only to be trampled upon... like ants. The city and the beliefs that Kremnoans hold so dearly, alongside the supposed tradition... are mere anthills that can be crushed with a single touch in the eyes of the Titan.

**Krateros:** You...! Are you trying to strip Kremnoans of the pride we've amassed over thousands of years with mere words?!

**Mydei:** ...That pride holds little significance, Krateros. Now that I've assumed the divinity of Strife, my next step... Will be to renounce the title of "King."

**Krateros:** ...No! NO!

**Mydei:** Convey my message to every Kremnoan — this is an order.

**Krateros:** Do not do this, Mydeimos... I beg you...!

**Mydei:** Our history commenced in Year 2506 of the Light Calendar and concluded in Year 4931. I, Mydeimos, last King of Castrum Kremnos, son of Gorgo, do hereby proclaim... **The Kremnoan dynasty comes to an official close today.**

**Krateros:** You have killed us... You have killed us all...

**Mydei:** No, I am granting you a new beginning.

*(Mydei gives Krateros his mother's signet ring, imbued with new meaning.)*

**Mydei:** Take it and rally those who have lost their identities. Convey the words of Mydeimos, now ascended to divinity: You no longer need to chase fleeting honors or face death on the battlefield as if it were your sole destination. However, you must adapt to fit into this city that you once observed with indifferent eyes.

**Mydei:** A cruel fate awaits Amphoreus. No matter how illustrious a dynasty may seem, it crumbles to rubble and gravel before formidable foes. Yet, you shall tread the only path out, one that leads to a brand-new world at its end.

**Krateros:** Why task me with being your messenger? Why not explain all this to them yourself?

**Mydei:** Because only humans can guide the path to be trodden by humans. It's not the lot of "humans" who crave the power of gods and spiral into madness for it... But "humans" who stand ready to raise their shields high to protect the lives behind them.

**Krateros:** ...Where will you be headed now?

**Mydei:** To the place where I belong, to fulfill my promise. The madness that has plagued Nikador and the darkness that has consumed Amphoreus... It's now my turn to fight against it.

## Farewell to Aglaea

**Aglaea:** You're here, Mydeimos... It seems that you are prepared.

**Mydei:** Yes.

**Aglaea:** You aided Okhema through yet another trying ordeal, and my gratitude knows no bounds.

**Mydei:** Isn't that exactly what you wanted?

**Aglaea:** Not everything unfolds according to my plan. In the current state of the world, I can only proceed one step at a time.

**Aglaea:** And now, Mydeimos, you have risen as the most powerful demigod in the world. How do you intend to wield this newfound power?

**Mydei:** I shall see Nikador's aborted mission through to completion, and become the strongest bulwark for Amphoreus to defend against the black tide. I will secure enough time for the Flame-Chase Journey until you manage to lead everyone to reach the miracle of "Genesis."

**Aglaea:** Mydeimos, a new chapter awaits Amphoreus... Yet, the one who guides the people to the destination need not be you and I.

**Mydei:** Hehe... What did you see after assuming Mnestia's divinity?

**Aglaea:** ...Despite the passage of a thousand years, every word of that prophecy remains as vivid as ever. **"You shall have your final bath in warm and radiant gold."**

**Mydei:** ...Heh, just as cryptic as all the other prophecies.

**Aglaea:** So, I assume you also glimpsed yours, Mydeimos?

**Mydei:** **"One day, you shall die with a wound in your back."**

**Aglaea:** Well, that is a rather straightforward scenario.

**Mydei:** If I were to be terrified by drivel with no basis, I would not have attracted your gaze and joined the Flame-Chase Journey in the first place.

**Aglaea:** You speak the truth. May you be destined for a powerful fate, and may we reunite in the promised new world... Farewell, Mydei.

## Farewell to the Trailblazer and Dan Heng

**Dan Heng:** ...Mydei?

**Mydei:** Outlanders... no, Trailblazers, I will soon make my way to Castrum Kremnos. If all goes according to plan, this may be our final meeting. I just want to let you know that I appreciate everything you have done for Amphoreus.

**Dan Heng:** Reflecting on the past and moving forward to the future — a challenge I've faced as well. Though we never had a chance for a deep conversation, after all we've experienced together... you are also an ally of the Trailblaze, Mydei.

**Mydei:** That means a lot to me. May success accompany your Trailblazing wherever it leads.

> *(Trailblazer)* I guess he will say something inspiring.
> *(Trailblazer)* I guess he will say something sentimental.
> *(Trailblazer)* I guess he will say something nonsensical.

**(Trailblazer):** *sob* ...What are we going to do without you?

**Mydei:** ...

**Dan Heng:** Just smile if you don't know how to respond.

**Mydei:** ...Haha.

**Mydei:** Now that I bear the divine within me, I can get the vague feeling that... that you have a great significance for the future of Amphoreus. With this departure, I fear that I will never again return. Can I entrust you both to watch my back... and to continue supporting the Flame-Chase Journey in my absence?

**Dan Heng:** ...Rest assured. We'll do everything we can.

**(Trailblazer):** Let's at least snap a photo together to capture this moment, shall we?

**Mydei:** Hah... Sure. Let's do it.

*(They take a photo together.)*

**Dan Heng:** Looks pretty good. What do you think, Mydei?

**Mydei:** Hmph, well... It feels peculiar, I suppose? I'm not talking about your photographic skills. It's just that I rarely take photos... But this one... It's pretty good.

## Farewell to Phainon

*(The Kremnoan children have gathered a crowd to bid Mydei farewell.)*

**Phainon:** It's been a while, "Guardian."

**Mydei:** Hmph, I should've known you were the mastermind behind this.

**Phainon:** Hey, don't go pointing fingers without cause. I swear I'm innocent this time. See those kids over there? They're the ones who brought everyone together.

**Mydei:** ...I admit, that took me by surprise.

**Phainon:** Were you seriously just going to sneak off without a word with me?

**Mydei:** Well, I was actually on my way to bid farewell to you, but ended up running into this.

**Phainon:** Oh... That's quite an honor, I suppose. We better not leave them waiting too long, don't you think?

**Mydei:** The road to Castrum Kremnos from here is long. Perhaps it wouldn't be a bad idea... to take a moment and etch their faces in my memory one last time.

*(Walking the last stretch together.)*

**Phainon:** I'm thinking... Maybe it's about time the god of "Strife" gets a new name. How about the god of "Solidarity"? Or... "Preservation"? Dan Heng mentioned that one to me.

**Mydei:** I recommend that you steer clear of any situation that calls for naming things.

**Phainon:** Hah... I suppose "Strife" still fits you better.

**Phainon:** Alright... It's about time for us to part ways. Any final goodbyes you want to share? This might be your last chance.

**Mydei:** Hmph... Do you truly feel as carefree as you seem? Or... is this just a facade you wear?

**Phainon:** ...You know what, you sound just like Aglaea at this moment. But you're not off the mark... I just thought putting on a nonchalant front for this occasion might help us preserve some dignity.

**Mydei:** I can see through your deception even without the power of mind-reading.

**Phainon:** Am I really that terrible at controlling my facial expressions? Well, with that said... thank you for aiding me in defeating my archenemy, Mydeimos.

**Mydei:** No need to thank me. This triumph brings no delight, nor does it signify closure — you understand that more than me.

**Phainon:** ...Indeed. In the end, I still haven't unraveled the mystery behind that black-robed swordmaster, and I can't even ascertain their demise. Maybe I've never managed to cut off my destiny.

**Mydei:** But that matters not. Pain may be cured, but scars remain, and they should not be effaced. Even with the divine might of Oronyx, you cannot stop the past from leaving its marks in our blind spots. Can you genuinely let go of everything as soon as that swordmaster is dead? That's impossible. Revenge is merely an obligation that must be carried out, and no one can find mental fulfillment through it.

**Mydei:** Look forward. Chew up and swallow your past, then make sure emptiness and bitterness are not the only flavors you know. Remember that there is a whole world behind you waiting to be saved.

**Phainon:** I will keep that in mind.

**Mydei:** I have a final favor to ask: Please look after the Kremnoan warriors in my absence. They will undoubtedly face challenges while assimilating into Okhema... It is my sole regret that I cannot stand by them during this time.

**Phainon:** Do not worry. Leave it to me. And while I'm at it, I'm going to find out if the Kremnoan language is really missing that many words.

**Mydei:** Hmph, the Kremnoan philosophy can never be encapsulated in a mere dictionary. But... if there's a chance in the next life, you should come visit my library.

**Mydei:** I'll be on my way, Deliverer. Remember to stay alive till the final act.

**Phainon:** Yes. Same goes for you. Don't die too easily — May triumph always be yours, Mydeimos.

**Mydei:** ...Oh, right. One last question. Are you the one who told Chartonus about the signet ring?

**Phainon:** Well... Who knows?

## Return Home

*(Mydei walks the blood-soaked road home. He dreams of his mother.)*

**Gorgo:** Get up, my son! You showed great courage in today's training. Let's wrap it up for now.

**Young Mydei:** Yes, Mother. Mother... There's something I want to ask you. Why must we learn to fight?

**Gorgo:** It is for glory and honor, my son. For Kremnoans, mastery of swords and spears is ingrained from birth, and the battlefield is our destined end.

**Mydei:** Is that really the way it is, Mother?

**Gorgo:** What makes you say so?

**Mydei:** Because you don't sound entirely sure.

**Gorgo:** ...You're right, Mydeimos. I once believed those words without question until your father cast you into the Sea of Souls. It was at that moment I realized how everything I believed in was utterly hollow. Perhaps the spirit of Kremnos had once existed... but as greed bloomed in the hearts of humanity over the years, such spirit had long faded alongside our glory.

**Gorgo:** I no longer put my faith in any oath or doctrine. Now, I have just one role... That of your mother, Mydeimos. Your guardian...

*(Mydei arrives at Castrum Kremnos. Past and present blur. His fallen comrades greet him.)*

**Perdikkas:** Look, Mydeimos is back!

**Hephaestion:** We've got fresh pomegranate juice. Want to try some?

**Ptolemy:** Say! Come and check out what I just wrote...

**Leonnius:** Mydeimos! Did you just come back from training?

**Peucesta:** It's... been a while.

**Gorgo:** Welcome home... Mydeimos. Have you found something deserving of your protection as well?

**Mydei:** Mother... ...I'm home.

---

*Year 4931 of the Light Calendar, Month of Balance. Nikador — the Strife Titan, Lance of Fury — fell. Mydeimos, king of Kremnos, triumphed over the trial, and the new god was born. On the following day, the Kremnoan dynasty, which had lasted for a thousand years, came to an end.*

---

## Mission 8 Summary

**Key Characters:** Mydei, Krateros, Aglaea, Trailblazer, Dan Heng, Phainon, Gorgo
**Key Events:** Mydei declares the end of the Kremnoan dynasty. He bids farewell to Aglaea, the Trailblazer, Dan Heng, and Phainon. He returns to Castrum Kremnos alone to fight the black tide. The Kremnoan dynasty ends after a thousand years.

---

# Mission 9: Passage, Reveal the Past Once More

**Perspective:** Multi-POV (Tribbie, Phainon, Trinnon) | **Location:** Okhema → Abyss of Fate

*(At Trianne's funeral, Phainon asks Tribbie to show them the origin of the Flame-Chase Journey. Using the Trailblazer's power, they journey to the past to witness Tribios' fateful decision.)*

## Trianne's Funeral

**Tribbie:** We smell sunlight in the wind of Okhema... This was your favorite spot, wasn't it, Trianne?

**Castorice:** Lady Trianne... Why did it have to end up like this?

**Tribbie:** Take it easy, Cas. Departure is a part of life. It's just that ours isn't as tumultuous as it is for ordinary folks.

**Trinnon:** When we started our journey, Janus had already provided their prophecy. Just like how that Titan divided themself to create the countless passages in the world... It's only natural for us to follow the same path since we inherited their destiny.

**Phainon:** If you don't mind, Tribbie... Are you still willing to unveil that past for us? The past regarding the "prophecy."

**Phainon:** Mydeimos has left the city to face his own fate. That is the fate of every demigod. We will all eventually let go of our past to follow the same path as his. So, what I want to know is — As Amphoreus' first demigod, what compelled you to take the first step on this journey? And what has sustained you to make it this far without looking back, despite the fracturing of your body and the numerous departures you have endured?

**Tribbie:** ...Alright.

**Aglaea:** Teacher, are you sure about this?

**Tribbie:** De is already doing what he has to do... What reason do we have to keep it from them? Let's go, everyone...

**Trinnon:** Let's go to the Abyss of Fate and see how it used to be.

## The Past: Janusopolis

*(In the Sanctum of Prophecy, they see Tribios as a young Holy Maiden, a thousand years ago.)*

**Trinnon:** At this point, Janusopolis still resides under Aquila's protection, yet it is already fated for decline, and only contains a beautiful facade.

**Phainon:** Is it because Amphoreus has entered Era Bellica?

**Trinnon:** Yes. Strife remains distant from this part of Amphoreus right now, but in five years' time, at the same dawn, this temple will become the source of another war.

## Tribios' Last Conversation with Oronyx

**Oronyx:** Tri... bios...

**Tribios:** You're here, Oronyx.

**Oronyx:** You still... consume yourself... for that false prophecy.

**Tribios:** "False prophecy," huh? So you still think that way.

**Oronyx:** Even if Kephale has fallen... they would never guide humans to kill their own comrades. Stop while you still can. Tribios... Spreading the prophecy will only kindle disaster. That disaster... will tear you into a thousand pieces.

**Tribios:** But the black tide has already arrived, and Janus remains in slumber. If even the god of passages, known for guiding mortals, cannot resist this catastrophe, then what can we do against the incoming destruction?

**Oronyx:** Do not... get involved with the Coreflames. If you do that... You can still remain chosen by fate.

**Tribios:** Those chosen by fate would never have their family taken from them. And how can I alone remain safe and secure, while watching the entire world crumble before my eyes? This might be our last conversation, Oronyx. I will do everything I can... to protect you from the black tide.

## The Night Before

*(Young Tribios with her mother, Mortis.)*

**Tribios:** Mama... are you going to that ritual tomorrow?

**Gentle Mother:** That's right, my sweet girl. What's the matter?

**Tribios:** I wish I could go too... I have something to ask Janus. I want to know how to chase the black tide away!

**Gentle Mother:** Ah, I see. Unfortunately, it's a secret ritual, and only I can preside over it. If you want me to consult the Titan on your behalf... you'll have to promise me something. Be a good girl and go to sleep now, and whatever you dream of, don't be afraid— Just sleep through the night, until morning comes, until the next time Aquila opens their eyes. Can you do that for me, sweetie?

**Tribios:** That's it? Of course I can! Tribios is the most amazing Holy Maiden of Janus... Well, little Holy Maiden! But... why, Mama?

**Gentle Mother:** Because... this ritual might take a long time.

**Tribios:** How long?

**Gentle Mother:** Tomorrow, my sweet child. I'll be back tomorrow. If not tomorrow, then the next tomorrow. But if I still haven't returned for a very long time... That means the ritual has succeeded. It means I've found a way to chase away the black tide and reached the new world on the other side. But for various reasons, I can't return to bring my sweet girl with me.

**Gentle Mother:** But I'll be waiting for you there. As long as you stay brave and kind, we'll meet again in that new world.

**Gentle Mother:** It's the end of the west wind, the black tide's other shore, a radiant sea of flowers blessed and protected by the gods. In the rosy horizon, you'll see a silver-white shoal. It marks the end of your voyage — a haven free from storms, cold, and heavy rains. No sorrow can linger there... That is where I'll be waiting for you.

**Tribios:** Wow! That sounds just like the island from my dream! Oh, I know! I'll turn the moon into a ship and the stars into sails to go find Mama! Pinky promise?

**Gentle Mother:** Mmm, pinky promise. As long as you sail toward tomorrow, as long as the sun will rise for the next day... Our wishes will come true together.

## Tribios Claims the Coreflame

*(Tribios enters the Janus Vault.)*

**Tribios:** At long last...

**Janus:** Tribios... you've come.

**Tribios:** ...I knew there was some sanity left in you, Janus. Just as I thought... you too have been confined.

**Janus:** Step forth, and thou shalt bury yourself... Bury the gods, and bury the fate that binds us all.

**Tribios:** No, Janus... I've come here... to take on your fate.

**Tribios:** By the blood of the lamb and the strength of my blade-wielding right hand... I am Tribios, the Listener, the announcer, and the witness of the prophecy — I, the Holy Maiden of Janusopolis, the walker of the infinite paths, have come forth to assume your duty.

**Janus:** Hehe... The one who guides the world shall see their soul shattered into a thousand fragments, akin to glass crashing upon the ground...

**Tribios:** Just as I wished. This journey promises to be a long one. With a thousand selves to accompany me, I'll never be lonely.

**Janus:** Though thou bearest the Coreflame, thou shalt be far from the glory of divinity. "Passages" are forever associated with dirt, and even a mere mortal's blade can imperil thy very existence...

**Tribios:** No matter. My hands are not made for bearing arms, but my feet are destined to embark on a journey for the benefit of all.

**Janus:** Yet, the Flame-Chase is a journey of constant loss, among which even life itself holds little value... Time decays the heart, the passages shatter the body, and the scales weigh the separation, until the end draws near... The one who bears three lives... art thou truly prepared?

**Tribios:** Without a doubt, Titan. Let the prophecy shatter me — so that I may open a myriad of paths for this imperiled world!

**Janus:** Thus... it shall be...

*(The dying Titan's prophecy:)*

**Dying Titan:** Overthrow the gods — / Return the Coreflames — Inherit divine authority — / Forge godly miracles — Go kill — / Go mourn — Kill my kin — / Mourn our fate — Ferry the spirits of the gods — / Nourish the land with divine essence —

**Dying Titan:** Yet, thou shalt remember — **All shall bid farewell to one, and that person alone will witness the miracle —** Such... is destiny —

**Tribios:** I understand, Janus... Thank you. Now... may you rest well.

**Tribios:** Mother... Did you... see that? I have assumed my duty and stand ready to set out... We will step over the gods' corpses and wander among humanity... And thus, we shall sweep apart Amphoreus' pitch-dark fog... May we... May the world... Follow the myriad paths trodden and reunite at the end of the west wind... where flowers bloom in spring. Mother... I shall see you tomorrow.

---

*(Guards arrive. Tribios escapes, aided by a mysterious force — which is revealed to be her future self, reaching back through time.)*

## The Letter Across Time

**Tribios:** The answer is already within you, and you've made your own decision.

**Phainon:** ...What? You can... hear us?

**Trinnon:** Not really... She can neither see nor hear us. Yet, she knew that one day, someone would return to unveil this dust-covered memory.

**Trinnon:** We can never know for sure who helped us back then. But that kindness was forever engraved in our hearts, motivating us to move forward. Time has modified this memory into a special letter, so that we do not forget our original intent. It's a letter written by Tribios of the past and sent to her future self.

**Tribios:** Yes, you'll remember it all, and then find your way back to the gate where everything began. Here, I will set sail toward the distant horizon. Here, you have traveled far on your way home.

**Tribios:** Such is the maxim that unveils Tribios' fate: **"You shall shatter into a thousand fragments and wither on the soil of foreign lands."** So, if you ever feel lost, return to this place. I'll keep this memory here for you — or for me — to embrace it again.

**Trinnon:** Worry not. Though loss is something we've grown used to, our resolve and our pledge are what Tribios will never forget. Each one of us has never failed to remember.

**Tribios:** In the name of the Three Fates, I stand by my answer with no regrets. Now, with or without the gods' blessing... I run towards the world's agony. If I can truly pierce through the utter darkness... We will meet again at the end of the west wind where flowers bloom in spring.

---

*Light Calendar 3760, Month of Evernight: "Janusopolis' Holy Maiden" Tribios bore the Coreflame to quell the world's chaos and became a demigod of Janus. She traversed the "Gate of Infinity," splitting into a thousand messengers to spread the divine prophecy across the land of Amphoreus.*

*Light Calendar 3870, Month of Freedom: Humanity's Flame-Chase Journey officially began.*

---

## The Promise of Tomorrow

**Castorice:** Lady Tribbie, do you still think... That everything will be fine tomorrow?

**Tribbie:** Yeah, that's what Trianne would say as well.

**Castorice:** With all due respect... Lady Tribbie, you know perfectly well... that "see you tomorrow" is nothing but a white lie. I hope your toughness is not a mask hiding a lonely heart.

**Tribbie:** Cas, that's not a lie. **"See you tomorrow"** is the greatest prophecy in the world.

**Castorice:** Prophecy...?

**Tribbie:** Listen. In every corner of this land, every heartbeat carries a prayer for that prophecy to come true. It may be that only a few heroes will bring tomorrow to the new world, but the prophecy of leading everyone to tomorrow belongs to all in Amphoreus.

**Tribbie:** Because people believe it will come true, and they are trying hard to hold onto that belief. Even as the world teeters on the brink of collapse, everyone is pressing forward, longing to reach farther and move toward tomorrow.

**Tribbie:** "Fate" is not about the outcome, but the journey. It's not the flowers that bloom at the end of the road... But rather the paths that lead beyond the gate, where people tread toward the sea of flowers.

**Tribbie:** So, Cas, if anything is troubling you, just set it aside for tomorrow. There's no difference between demigods and mortals. The troubles we encounter can only be resolved by our future selves. Reflect through the long night, wait for the dawn as you think, then set off at daybreak.

**Tribbie:** Because that's how Tribios has journeyed so far to spread the prophecy... Beckoning the morning sun... and the tomorrow it promises to bring.

---

## Epilogue: Anaxa and Cerces

**Anaxa:** Hehe...

**Cerces:** Child of humanity, surely you are not waiting for the arrival of night?

**Anaxa:** Nights do not fall upon Okhema.

**Cerces:** That's why it's futile for you to wait here.

**Cerces:** There's not much left in your soul. If you don't do something soon, I will have to take over this body.

**Anaxa:** If I'm not worried, why should you be? I know what you're planning. You just want my help answering the question — "What exactly are 'we'?" Correct?

**Cerces:** It's good that you remember. Thus, "equivalent exchange" — it's only fair.

**Anaxa:** Then, rest easy. The answer will soon be revealed, and you'll have to return my body shortly. ...Regrettably... I can't carry out the upcoming experiment alone.

**Cerces:** The girl who's walking with death... is she fully prepared?

**Anaxa:** Be patient, Titan... If we're always so guarded, how can "Death" reach us easily?

**Aglaea (appearing):** Unfortunately, on behalf of Okhema, I must ask you to slow your pace.

**Anaxa:** Heh... I forgot about you. My apologies.

**Aglaea:** A child's words are always carefree. I'll just dismiss these words as nonsense from a cheeky child. Come now, conceited "performer." It's time to address your relationship with that Titan.

**Cerces:** Eh... Do you two mind if I cut in? Ahh. I just have been meaning to ask: Does death really matter to you?

**Anaxa:** ...What do you mean?

**Cerces:** What I mean is, before I implanted the Coreflame into your heart... **...you were already a silent, cold corpse.**

---

## Dan Heng and the Trailblazer

**Dan Heng:** I'm back. Finally have a moment to catch my breath. Want to chat, (Trailblazer)? It's unusual to see Mem isn't with you.

> *(Trailblazer)* Let Mem rest. They've had a tiring past few days.

**Dan Heng:** Since they're not here, let me ask you — **are you really sure you want to take on the trial of Oronyx's Coreflame on behalf of the Chrysos Heirs?**

> *(Trailblazer)* Absolutely! I don't see why not.
> *(Trailblazer)* Still on the fence. It was Mem's idea...
> *(Trailblazer)* It's about time for me to level up.

**Dan Heng:** ...We've ended up at this point after all. This is probably a fate that "Trailblaze" can't evade. You should be extra cautious and watch out for yourself. Based on the experiences of those before you, the trial is no walk in the park.

**Dan Heng:** But what concerns me even more is that you'll further bind yourself to Amphoreus... If you truly assume that Titan's divinity, do you believe you'll be able to lay it down again? Forget it. We'll deal with that when the time comes. No matter what happens, I'll be right there with you.

*(Dan Heng shares that messengers from the Council of Elders questioned him. Dark undercurrents are roiling in Okhema.)*

**Dan Heng:** The memory card is full. I bet March and the others are pretty worried too.

---

**Tribbie:** And so, this long day passed for Okhema. Some people arrived, and some left forever, just like every other day of this journey where we, stumbling, move forward. We have long been prepared. If we are to chase the flames, then we must grow used to farewells. And yet...

**Tribbie:** No one back then could foresee... **"Death"**... Its arrival would always be so sudden and so momentous. Even (Trailblazer), coming from beyond the sky, could not escape the Reaper's two hands. And what people gained and lost in that trial of "Death"... Was far heavier than "Life" itself.

**Tribbie:** Just like the destiny that the prophecy revealed for Cas... **"At the end of the sea of flowers, the souls of the living shall warm thy fingertips... And after an embrace... there shall be eternal separation."**

---

## Mission 9 Summary

**Key Characters:** Tribbie/Tribios, Phainon, Trinnon, Castorice, Aglaea, Mortis, Janus, Oronyx, Anaxa, Cerces, Dan Heng
**Key Events:** Trianne's funeral. Phainon witnesses Tribios' past — her mother's sacrifice, claiming Janus' Coreflame, the origin of the Flame-Chase Journey. The "letter across time" reveals Tribios' resolve. Anaxa is revealed to have been a corpse before Cerces implanted the Coreflame. The Trailblazer prepares for the trial of Oronyx.

---

## End of Chapter 2

> **Next:** Chapter 3 — Through the Petals in the Land of Repose (v3.2)
> **Key Events:** The Grove falls to the black tide; Cerces' Coreflame secured; Trianne sacrifices herself; the Flame Reaver is defeated in Castrum Kremnos; Mydei ascends as the God of Strife and renounces his throne; Tribios' origin and the Flame-Chase prophecy are revealed.
> **Key Line:** *"See you tomorrow" is the greatest prophecy in the world.*
"""

    output += m2_dialogue
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(output)
    
    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"Created: {OUTPUT}")
    print(f"Size: {size_kb:.1f} KB")
    print("Done!")

if __name__ == '__main__':
    build()
