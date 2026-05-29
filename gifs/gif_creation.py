from PIL import Image

def load_rgba(path):
    return Image.open(path).convert("RGBA")

frames_rgba = [load_rgba(f"../logs/pinkfur/media/test/{i:02d}.png") for i in range(30)]
base = frames_rgba[0].convert("P", palette=Image.ADAPTIVE, colors=255)
palette = base.getpalette()

def convert_with_palette(img):
    p = img.convert("RGB").quantize(palette=base)
    alpha = img.getchannel("A")
    mask = alpha.point(lambda a: 255 if a == 0 else 0)
    p.paste(0, mask) 
    return p

frames = [convert_with_palette(f) for f in frames_rgba]

frames_rgba[0].save(
    "pinkfur_cow.webp",
    save_all=True,
    append_images=frames_rgba[1:],
    duration=150,
    loop=0
)