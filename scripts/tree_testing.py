from pathlib import Path
import sys
from typing import List
from util import Vertex, vertex_id, discover_files, load_all_vertex, write_all
import itertools
import util


def point_on_line(a: int, b: int, p:  int, vertex_list: List[Vertex]) -> Vertex:
    a, b, p = (vertex_list[vi] for vi in (a, b, p))

    axis = "x" if a.y == b.y else "y"

    t = (getattr(p, axis) - getattr(a, axis)) / (getattr(b, axis) - getattr(a, axis))
    assert 0 < t < 1, f"{a}, {b}, {p}, {axis}, {t}"

    new_z = a.z - t * (a.z - b.z)

    return Vertex(p.x, p.y, new_z)


class TreeFace:
    children: List["TreeFace"]
    corners: List[int]
    min_z: float
    max_z: float
    size: int

    def __init__(self, x: int, y: int, x_count: int, size: int, dz: float, vertex_list: List[Vertex]):
        self.size = size
        self.children = []
        self.corners = [vertex_id(x+dx, y+dy, x_count) for (dx ,dy) in [(0,0), (0,size), (size, size), (size,0)]]

        self.min_z = min(vertex_list[i].z for i in self.corners)
        self.max_z = max(vertex_list[i].z for i in self.corners)

        if size <= 1:
            return

        n = size // 2

        self.children = [
            TreeFace(x+dx, y+dy, x_count, n, dz, vertex_list) for (dx, dy) in [(0, 0), (n, 0), (n, n), (0, n)]
        ]

        minz = min(f.min_z for f in self.children)
        maxz = max(f.max_z for f in self.children)

        if (maxz - minz) >= dz:
            return

        for i in range(1, size):
            horizontal_offset = [(i, 0), (i, size), (0, i), (size, i)]
            corners = [(0, 3), (1, 2), (0, 1), (3, 2)]
            for (dx, dy), (c1, c2) in zip(horizontal_offset, corners):
                v_id = vertex_id(x + dx, y + dy, x_count)
                vertex_list[v_id] = point_on_line(self.corners[c1], self.corners[c2], v_id, vertex_list)

        self.children = []

    def return_faces(self) -> List:
        if self.children:
            for c in self.children:
                yield from c.return_faces()
        else:
            if self.min_z < 0.1:
                yield []
            else:
                yield tuple(map(lambda x: x + 1, self.corners))


def expand_vertex_list(v: List[Vertex], size: int):
    needed_size = 1 << (size-1).bit_length()
    end_index = needed_size + 1

    for (x, y) in itertools.product(range(end_index), range(end_index)):
        if x >= size or y >= size:
            v.append(Vertex(x, y, 0))
    v.sort()

    return end_index


def load_all(p: Path):
    work = discover_files(root=p)
    print(work.extent)

    ver = sorted(load_all_vertex(work.xyz_files, work.extent.min_x, work.extent.min_y))
    util.subtract_with_image(ver, p / "negative_test_2.png", work.extent, skip=1)

    n = expand_vertex_list(ver,  work.extent.count_x)
    t = TreeFace(0, 0, n, n-1, .5, ver)

    faces = list(t.return_faces())

    write_all(faces, ver, Path("tree_test.obj"), work.extent, scale=1e-2)


if __name__ == '__main__':
    load_all(Path(sys.argv[1]))
