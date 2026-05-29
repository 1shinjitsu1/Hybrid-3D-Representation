from PIL import Image
import numpy as np
import argparse


def process_texture(file_name: str, resize: bool = True, tile_factor: int = 4):
    img = Image.open(file_name).convert("L")
    arr = np.array(img)

    if resize:
        tiled = np.tile(arr, (tile_factor, tile_factor))
        img_out = Image.fromarray(tiled).resize((2048, 2048), Image.NEAREST)

    else:
        img_out = Image.fromarray(arr)

    arr_out = np.array(img_out).astype(np.float32) / 255.0
    final_img = Image.fromarray((arr_out * 255).astype(np.uint8))
    final_img.save(file_name)
    print(f"Saved: {file_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help = "Input image file")
    parser.add_argument("--resize", action = "store_true", help = "Resizes image by copying it for detail.")
    parser.add_argument("--no-resize", action = "store_true", help = "No resizing done, keeps original")
    args = parser.parse_args()

    resize_flag = True
    if args.no_resize:
        resize_flag = False
    elif args.resize:
        resize_flag = True

    process_texture(args.file, resize = resize_flag)