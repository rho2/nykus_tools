import numpy as np
import cv2
import os
import sys
from pathlib import Path
from typing import Tuple
import do_all
import util

def load_extent(csv_file: Path) -> Tuple[Tuple[int, int]]:
    csv_lines = csv_file.read_text().splitlines()
    ukn, corners, date = csv_lines[1].split(";")
    c = tuple(map(int, corners.split()))
    return c

p = Path(sys.argv[1])
# for folder in os.listdir(sys.argv[1]):
#     if not folder.endswith("tiff"):
#         continue
#     print(folder)
#     image_file = next(a for a in os.listdir(os.path.join(sys.argv[1], folder)) if a.endswith("tif") and a.startswith("dop"))
#     print(image_file)
#     img = cv2.imread(os.path.join(sys.argv[1], folder, image_file), 1)
#     img_small = cv2.resize(img, (0, 0), fx=0.2, fy=0.2)
#     cv2.imwrite(os.path.join(sys.argv[1], folder, f"small_{image_file}"), img_small)
scale = 0.2

dgm1_folders = [f for f in sorted(p.iterdir()) if f.is_dir() and f.name.startswith("dgm1")]
csv_files = [next(folder.glob("*.csv")) for folder in dgm1_folders]

extent = util.load_full_extent(csv_files)

single_len = extent.max_x - extent.min_x
ll = int(extent.count_x / single_len)
print(ll)

blank_image = np.zeros((10000 * ll, 10000 * ll, 3), np.uint8)

for folder in os.listdir(sys.argv[1]):
    if not folder.endswith("tiff"):
        continue
    print(folder)
    image_file = next(a for a in os.listdir(os.path.join(sys.argv[1], folder)) if a.endswith("tif") and a.startswith("dop"))
    csv_file = next(a for a in os.listdir(os.path.join(sys.argv[1], folder)) if a.endswith("csv") and a.startswith("dop"))

    min_x_, min_y_, max_x_, max_y_ = load_extent(p / folder / csv_file)
    foo_x = (min_x_ - extent.min_x) // single_len
    foo_y = ll - (min_y_ - extent.min_y) // single_len - 1

    foo_x *= 10000
    foo_y *= 10000

    print(foo_x, foo_y)

    img = cv2.imread(os.path.join(sys.argv[1], folder, image_file), 1)

    dx = img.shape[1]
    dy = img.shape[0]
    print(image_file)

    blank_image[foo_y:foo_y + dy, foo_x:foo_x + dx] = img

for i in range(1,6):
    scale = 1/i
    print("Writing sclae", scale)
    img_small = cv2.resize(blank_image, (0, 0), fx=scale, fy=scale)
    cv2.imwrite(os.path.join(sys.argv[1], f"texture_{i}.png"), img_small)