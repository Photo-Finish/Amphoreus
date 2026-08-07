"""
Build Chapter 2 verbatim file from raw wiki text files.
Usage: python build_ch2.py
Reads raw text files from raw_ch2/ directory, cleans them, and outputs markdown.
"""
import re, os, glob

def strip_templates(text):
    """Remove {{...}} templates including nested ones."""
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

def clean_dialogue_line(line):
    """Clean one line of wiki dialogue into markdown format."""
    if not line.strip():
        return None
    
    orig = line
    
    # Skip boilerplate
    skip_starts = [
        '{{A|', '{{Color|', '{{Size|', '{{MC|', '{{Rubi|', '{{w|', '{{lang|',
        '{{sic|', '{{Reflist', '{{Change', '{{Trailblaze Mission Navbox',
        '{{Preview', '{{Transclude', '{{Enemy', '{{Item|', '{{Other',
        '[[File:', '|file', '[[de:', '[[fr:', '[[ru:', '[[vi:', '[[zh:',
        '<gallery>', '</gallery>', '{{Gallery', '{{Stub', '{{Reflist',
    ]
    stripped = line.strip()
    for p in skip_starts:
        if stripped.startswith(p):
            return None
    
    # Skip special patterns
    if re.match(r'^\{\{(Mission|Dialogue|Black|Enemy|Item|Rubi)', stripped):
        return None
    if re.match(r'^;\(', stripped):  # ;(Obtain, ;(Begin battle, ;(Approach
        if 'Obtain' in stripped or 'Unlock' in stripped or 'Begin battle' in stripped:
            return None
        # Stage directions like ;(Approach the marked location)
        inner = stripped[2:].strip()
        # Clean
        inner = strip_templates(inner)
        inner = re.sub(r"'''", '', inner)
        inner = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', inner)
        inner = re.sub(r'\[\[([^\]]+)\]\]', r'\1', inner)
        inner = inner.replace('&mdash;', '—').replace('&nbsp;', ' ')
        return f"\n*[{inner}]*\n"
    
    # Section headers
    if re.match(r'^===.*===$', stripped) and not re.match(r'^=====', stripped):
        title = stripped.strip('= ')
        if title in ('Dialogue', 'Steps', 'Gameplay Notes', 'Notes', 
                     'Other Languages', 'Change History', 'Navigation', '', ' '):
            return None
        return f"\n## {title}\n"
    
    if re.match(r'^=====', stripped):
        return None
    
    # ---- separators
    if stripped == '----':
        return "\n---\n"
    
    # === Section headers without template mess
    if '===' in stripped:
        return None
    
    # Pre-clean the line: strip templates, wiki links, HTML entities
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
    
    # Handle DIcon patterns (check in original line)
    if '{{DIcon|Arrow}}' in orig:
        text = orig.split('{{DIcon|Arrow}}', 1)[1].strip()
        text = strip_templates(text)
        text = re.sub(r"'''", '', text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—').replace('&nbsp;', ' ')
        if text:
            return f"> *(Trailblazer)* {text}\n"
        return None
    
    if '{{DIcon|Talk}}' in orig:
        text = orig.split('{{DIcon|Talk}}', 1)[1].strip()
        text = strip_templates(text)
        text = re.sub(r"'''", '', text)
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = text.replace('&mdash;', '—')
        if text:
            return f"> 💬 {text}\n"
        return None
    
    # Check for :: responses FIRST (nested dialogue, responses to choices)
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
        return f">   {inner}\n"
    
    # Check for character dialogue: :'''Char:''' text
    m = re.match(r"^:(.*?):\s*(.*)", cleaned)
    if m:
        char = m.group(1).strip()
        text = m.group(2).strip()
        if text:
            return f"**{char}:** {text}\n"
    
    # Plain narration (starts with colon but no visible character)
    # E.g., ":A giant tree..."
    if cleaned.startswith(':') and ':' not in cleaned[1:]:
        text = cleaned[1:].strip()
        if text:
            return f"{text}\n"
        return None
    
    # Generic cleaned text
    if cleaned and len(cleaned) > 1:
        return f"{cleaned}\n"
    
    return None

# Test some lines
TESTS = [
    ":{{A|VO chapter4 12 castorice 101 m.ogg}} {{A|VO chapter4 12 castorice 101 f.ogg}} '''Castorice:''' {{MC|m=Mr.|f=Miss}} (Trailblazer), you're awake.",
    ":{{DIcon|Arrow}} ...No wonder I felt a chill.",
    ":{{DIcon|Arrow}} The [[Astral Express|Express]] has house rules about drinking.",
    ":{{A|VO chapter4 12 danheng 101 m.ogg}} {{A|VO chapter4 12 danheng 101 f.ogg}} '''Dan Heng:''' You're finally here, (Trailblazer).",
    "===Speak with Castorice===",
    """===Grove, Wherefore Are the Wise Silent===""",
    "----",
    ";(Approach the marked location)",
    "::{{A|VO chapter4 12 castorice 122.ogg}} '''Castorice:''' Um, Miss Hyacine, about that nickname...",
]

for t in TESTS:
    result = clean_dialogue_line(t)
    print(f"IN:  {t[:80]}...")
    print(f"OUT: {result}")
    print()
