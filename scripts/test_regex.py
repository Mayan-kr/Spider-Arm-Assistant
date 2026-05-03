import re

instructions = [
    "create a file GUPTA.py and write LOL in it",
    "create GUPTA.txt and write HI Mayan in it",
    "write Done for today in work.txt",
    "Add 'Remember to buy milk' to notes.txt",
    "Create a note called hello.txt saying hi",
    "create a file hello world and write nothing"
]

for instruction in instructions:
    print(f"--- {instruction}")
    
    # 1. Extract filename (e.g., ends in .txt, .py)
    name_match = re.search(r'\b([\w-]+\.[a-zA-Z0-9]+)\b', instruction)
    name = name_match.group(1) if name_match else None
    
    # 2. Extract content
    content = None
    quote_match = re.search(r'["\'](.*?)["\']', instruction)
    if quote_match:
        content = quote_match.group(1)
    else:
        # We split by ' in ', ' to ', ' inside ' if they exist
        # e.g., 'write LOL in it'
        m = re.search(r'\b(?:write|add|saying|say)\s+(.*?)$', instruction, re.IGNORECASE)
        if m:
            raw = m.group(1)
            # Remove trailing ' in it', ' to work.txt', etc
            raw = re.split(r'\s+(?:in|to|inside)\b', raw)[0]
            content = raw.strip()
            
    print(f"Name: {name}, Content: {content}")
