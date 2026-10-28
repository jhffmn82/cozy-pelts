"""Contact sheet of images, scaled up with hard pixels on a backdrop: python tools/peek.py out.png scale img...  """
import sys
from PIL import Image
out, scale, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(p).convert("RGBA") for p in paths]
w = sum(i.width * scale + 8 for i in ims) + 8
h = max(i.height * scale for i in ims) + 16
sheet = Image.new("RGBA", (w, h), (70, 90, 120, 255))
x = 8
for i in ims:
    big = i.resize((i.width * scale, i.height * scale), Image.NEAREST)
    sheet.alpha_composite(big, (x, 8))
    x += big.width + 8
sheet.save(out)
print(out, sheet.size)
