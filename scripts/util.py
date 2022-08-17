from pathlib import Path
from typing import Tuple, NamedTuple, List, Optional
import numpy as np
import cv2
import math


class Vertex(NamedTuple):
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Vertex(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other) -> "Vertex":
        assert isinstance(other, float) or isinstance(other, int)
        return Vertex(self.x * other, self.y * other, self.z * other)

    def length(self):
        return math.sqrt(sum(x*x for x in self))

    def norm(self):
        l = math.sqrt(sum(x*x for x in self))
        return Vertex(self.x / l, self.y / l, self.z / l)

    def cross(self, other):
        return Vertex(
            self.y * other.z - other.y * self.z,
            other.x * self.z - self.x * other.z,
            self.x * other.y - other.x * self.y,
        )

class FullExtent(NamedTuple):
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    count_x: int
    count_y: int


class Workfolder(NamedTuple):
    xyz_files: List[Path]
    csv_files: List[Path]
    gml_files: List[Path]
    tiff_files: List[Path]
    extent: FullExtent


def subtract_with_image(arr: List[Vertex], image_file: Path, extent: FullExtent, skip: int, factor: float = 40):
    img = cv2.imread(str(image_file), cv2.IMREAD_UNCHANGED)
    # resized = cv2.resize(img, (extent.count_x, extent.count_y), interpolation=cv2.INTER_AREA)

    print("Subtracting")
    for i, (x, y, z) in enumerate(arr):
        if i % 100000 == 0:
            print(i)

        # if (x % skip) != 0 or (y % skip) != 0:
        #     continue
        uy = min(x / (extent.count_x - 2), 1)
        ux = 1 - min(y / (extent.count_y - 2), 1)
        xxx = int(ux * (img.shape[0] - 1))
        yyy = int(uy * (img.shape[0] - 1))

        image_value = img[xxx, yyy][3] / 255
        assert 0 <= image_value <= 1
        if image_value > 0.0001:
            new_value = Vertex(x, y, 0 if (250 <= img[xxx, yyy][0]) else z - image_value * factor)
            arr[i] = new_value


def vertex_id(x: int, y: int, x_count: int) -> int:
    return x + y * x_count


def dot_prod(x: Vertex, y: Vertex) -> float:
    return sum(a*b for a, b in zip(x, y))


def apply_transform_negative(point: Tuple[float, ...], transform: Tuple[float, ...], scale: float) -> Tuple[float, ...]:
    return tuple(scale * (coord - t) for coord, t in zip(point, transform))


def load_extent(csv_file: Path) -> Tuple[Tuple[int, int]]:
    csv_lines = csv_file.read_text().splitlines()
    ukn, corners, date = csv_lines[1].split(";")
    c = tuple(map(int, corners.split()))
    return ((c[0], c[2]), (c[1], c[3]))


def load_full_extent(csv_files: List[Path]) -> FullExtent:
    extents = [load_extent(f) for f in csv_files]

    min_x = min(e[0][0] for e in extents)
    min_y = min(e[1][0] for e in extents)

    max_x = max(e[0][1] for e in extents)
    max_y = max(e[1][1] for e in extents)

    x_count = max_x - min_x
    y_count = max_y - min_y

    return FullExtent(min_x, min_y, max_x, max_y, x_count, y_count)


def discover_files(root: Path):
    dgm1_folders = [f for f in sorted(root.iterdir()) if f.is_dir() and f.name.startswith("dgm1")]
    lod2_folders = [f for f in sorted(root.iterdir()) if f.is_dir() and f.name.startswith("lod2")]
    dop20_folders = [f for f in sorted(root.iterdir()) if f.is_dir() and f.name.startswith("dop20")]

    assert len(dgm1_folders) == len(lod2_folders) == len(dop20_folders)

    xyz_files = [next(folder.glob("*.xyz")) for folder in dgm1_folders]
    csv_files = [next(folder.glob("*.csv")) for folder in dgm1_folders]
    gml_files = [next(folder.glob("*.json")) for folder in lod2_folders]
    tiff_files = [next(folder.glob("*.tif")) for folder in dop20_folders]

    print(f"Found {len(xyz_files)} xyz files")

    full_extent = load_full_extent(csv_files)

    return Workfolder(xyz_files, csv_files, gml_files, tiff_files, full_extent)


def load_vertex(xyz_file: Path, min_x: int, min_y: int):
    print("Loading", xyz_file)
    for line in xyz_file.read_text().splitlines():
        x, y, z = map(float, line.split())
        yield Vertex(int(x) - min_x, int(y)-min_y, z)


def load_all_vertex(p: List[Path], min_x: int, min_y: int):
    for f in p:
        yield from load_vertex(f, min_x, min_y)


def write_faces(faces: List, fp, include_texture: bool = True):
    for face in faces:
        if not face:
            continue
        if include_texture:
            face = (f"{a}/{a}" for a in face)
        fp.write(f"f {' '.join(map(str, face))}\n")


def write_points(points: List, fp, extent: Optional[FullExtent] = None, scale: float = 1.0, texture_index: bool = True):
    for (x, y, z) in points:
        fp.write(f"v {float(x) * scale} {float(y) * scale} {z * scale}\n")

    if not texture_index:
        return

    for (x, y, z) in points:
        u = x / (extent.count_x - 1)
        v = y / (extent.count_y - 1)
        fp.write(f"vt {u} {v}\n")


def write_all(faces: List, points: List, outfile: Path, extent: Optional[FullExtent] = None, scale: float = 1.0, texture_index: bool = True):
    with outfile.open("w") as fp:
        fp.write("mtllib image.mtl\no Terrain\n")
        write_points(points, fp, extent, scale, texture_index)
        fp.write("usemtl Material.001\ns off\n")
        write_faces(faces, fp)

        with (outfile.parent / f"image.mtl").open("w") as out_file:
            out_file.write("""newmtl Material.001
Ns 225.000000
Ka 1.000000 1.000000 1.000000
Kd 0.800000 0.800000 0.800000
Ks 0.000000 0.000000 0.000000
Ke 0.000000 0.000000 0.000000
Ni 1.450000
d 1.000000
illum 2
map_Kd texture.png
""")
