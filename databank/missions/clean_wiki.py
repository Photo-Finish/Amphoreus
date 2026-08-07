#!/usr/bin/env python3
"""
Build upgraded chapter files for Amphoreus Trailblaze Missions.
Processes raw wiki text from fetched pages into clean markdown dialogue.
"""
import re, os, sys

def strip_all_templates(text):
    """Remove all {{...}} templates from text."""
    # Handle nested templates (like {{Rubi|[[A]]|B}})
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

def clean_wiki_line(line):
    """Transform a raw wiki line into clean dialogue format."""
    if not line.strip():
        return None
    
    # Skip various wiki boilerplate
    skip_prefixes = [
        '{{A|', '{{DIcon|', '{{Color|', '{{Size|', '{{MC|',
        '{{Rubi|', '{{w|', '{{lang|', '{{sic|',
        '{{Reflist', '{{Change', '{{Trailblaze Mission Navbox',
        '[[File:', '|file', '[[de:', '[[fr:', '[[ru:', '[[vi:', '[[zh:',
        ';(Obtain', ';(Unlock',
    ]
    for p in skip_prefixes:
        if line.strip().startswith(p):
            return None
    
    if re.match(r'^;\(Begin battle', line.strip()):
        return None
    if re.match(r'^\{\{(Mission|Dialogue|Black|Preview|Transclude|Enemy|Item|Rubi)', line.strip()):
        return None
    
    # PRE-CLEAN: Strip all wiki templates first
    cleaned = strip_all_templates(line)
    cleaned = cleaned.strip()
    
    if not cleaned:
        return None
    
    # Convert step headers to scene headers
    if re.match(r'^===.*===$', cleaned) and not re.match(r'^=====', cleaned):
        title = cleaned.strip('= ')
        if title not in ('Dialogue', 'Steps', 'Gameplay Notes', 'Notes', 
                         'Other Languages', 'Change History', 'Navigation'):
            return f"\n## {title}\n"
    
    if re.match(r'^====.*====$', cleaned):
        return None
    
    # Clean remaining wiki link syntax: [[Link]] -> Link, [[Link|Text]] -> Text
    cleaned = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', cleaned)
    cleaned = re.sub(r'\[\[([^\]]+)\]\]', r'\1', cleaned)
    cleaned = cleaned.replace('&mdash;', '—')
    cleaned = cleaned.replace('&nbsp;', ' ')
    cleaned = cleaned.replace('&amp;', '&')
    cleaned = re.sub(r"'''", '', cleaned)
    
    # Detect character dialogue: :'''Char:''' Text or :Char: Text
    # First check for DIcon pattern (before template stripping we check)
    if '{{DIcon|Arrow}}' in line:
        text = re.sub(r'.*\{\{DIcon\|Arrow\}\}\s*', '', line)
        text = strip_all_templates(text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—').replace('&nbsp;', ' ').replace('&amp;', '&')
        text = re.sub(r"'''", '', text).strip()
        return f"> *(Trailblazer)* {text}\n"
    
    if '{{DIcon|Talk}}' in line:
        text = re.sub(r'.*\{\{DIcon\|Talk\}\}\s*', '', line)
        text = strip_all_templates(text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—').replace('&nbsp;', ' ').replace('&amp;', '&')
        text = re.sub(r"'''", '', text).strip()
        return f"> 💬 {text}\n"
    
    if '{{DIcon|Exit}}' in line:
        text = re.sub(r'.*\{\{DIcon\|Exit\}\}\s*', '', line)
        text = strip_all_templates(text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—').replace('&nbsp;', ' ').replace('&amp;', '&')
        text = re.sub(r"'''", '', text).strip()
        return f"> 🚪 {text}\n"
    m = re.match(r":(.*?):\s*(.*)", cleaned)
    if m:
        char = m.group(1).strip()
        text = m.group(2).strip()
        if not text:
            return None
        # Stage directions
        if char.startswith('(') and char.endswith(')'):
            return f"*[{char.strip('()')}: {text}]*\n"
        return f"**{char}:** {text}\n"
    
    # Dialogue option lines (start with ::)
    if cleaned.startswith('::'):
        inner = cleaned[2:].strip()
        m2 = re.match(r"(.*?):\s*(.*)", inner)
        if m2:
            char = m2.group(1).strip()
            text = m2.group(2).strip()
            return f">   **{char}:** {text}\n"
        else:
            return f">   {inner}\n"
    
    # Trailblazer dialogue choices
    if cleaned.startswith('{{DIcon|Arrow}}') or cleaned.startswith('→'):
        text = re.sub(r'^(\{\{DIcon\|Arrow\}\}|→)\s*', '', cleaned)
        return f"> *(Trailblazer)* {text}\n"
    
    # Plain narration
    if cleaned:
        return f"{cleaned}\n"
    
    return None

def build_mission_summary(missions_data):
    """Build a concise summary table for mission listing."""
    pass

# Main: for now, just test the cleaning
if __name__ == '__main__':
    test = """:{{A|VO chapter4 12 castorice 101 m.ogg}} {{A|VO chapter4 12 castorice 101 f.ogg}} '''Castorice:''' {{MC|m=Mr.|f=Miss}} (Trailblazer), you're awake."""
    result = clean_wiki_line(test)
    print(f"Input:  {test}")
    print(f"Output: {result}")
    
    test2 = """:{{DIcon|Arrow}} ...No wonder I felt a chill."""
    result2 = clean_wiki_line(test2)
    print(f"\nInput:  {test2}")
    print(f"Output: {result2}")
    
    test3 = """:{{DIcon|Arrow}} The [[Astral Express|Express]] has house rules about drinking."""
    result3 = clean_wiki_line(test3)
    print(f"\nInput:  {test3}")
    print(f"Output: {result3}")

    test4 = """===Speak with Castorice==="""
    result4 = clean_wiki_line(test4)
    print(f"\nInput:  {test4}")
    print(f"Output: {result4}")
