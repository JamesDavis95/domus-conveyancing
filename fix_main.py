import io, re, sys

p = "main.py"
with io.open(p, "r", encoding="utf-8") as f:
    s = f.read()
orig = s

# 1) Split glued decorators: ")@app..." or "))@app..."
s = re.sub(r"\)\)\s*@app\.", ")\n@app.", s)
s = re.sub(r"\)\s*@app\.", ")\n@app.", s)

# 2) Fix unterminated logging line seen in your traceback
s = re.sub(
    r'logging\.info\("Processing file: %s \(content_type=%s\).*',
    'logging.info("Processing file: %s (content_type=%s)")',
    s
)

# 3) Normalize chained SQLAlchemy calls written with backslashes
lines = s.splitlines(True)  # keep \n
out = []
i = 0
while i < len(lines):
    line = lines[i]

    # detect start of a chain like: "name = session.query(...)\"
    m = re.match(r'^(\s*[A-Za-z_][A-Za-z0-9_]*)\s*=\s*session\.query\((.*)\)\s*\\?\s*$',
                 line)
    if not m:
        out.append(line)
        i += 1
        continue

    var = m.group(1)
    query_args = m.group(2)
    block = [line.rstrip("\\\r\n")]
    j = i + 1
    while j < len(lines):
        nxt = lines[j]
        # gather lines like "   .filter(...)\", ".order_by(...)\", ".all()"
        if re.match(r'^\s*\.\w+\(.*\)\s*\\?\s*$', nxt.strip()):
            block.append(nxt.rstrip("\\\r\n"))
            j += 1
            continue
        break

    methods = [b.strip() for b in block[1:]]  # keep calls intact

    # rebuild safely with parentheses
    rebuilt = var + " = (\n"
    rebuilt += "    session.query(" + query_args + ")\n"
    for mcall in methods:
        rebuilt += "    " + mcall + "\n"
    rebuilt += ")\n"

    out.append(rebuilt)
    i = j

s2 = "".join(out)
if s2 != orig:
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s2)
print("fix_main.py: applied" if s2 != orig else "fix_main.py: no changes needed")
