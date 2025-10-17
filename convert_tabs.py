# convert_tabs.py
import io
p = "main.py"
text = io.open(p, "r", encoding="utf-8").read()
new = text.replace("\t", "    ")
io.open(p, "w", encoding="utf-8").write(new)
print("Converted tabs -> 4 spaces in", p)
