from pathlib import Path
import sys
import itertools
import util


def load_all(p: Path):
    work = util.discover_files(root=p)

    outmap = [[0 for _ in range(work.extent.count_y)] for _ in range(work.extent.count_x)]
    verts = list(util.load_all_vertex(work.xyz_files, work.extent.min_x, work.extent.min_y))

    skip = 1
    scale = 1

    util.subtract_with_image(verts, p / "negative_new.png", work.extent, skip=skip)

    for v in verts:
        outmap[v.x][v.y] = v.z

    out_folder = Path() / "out_final_full"
    out_folder.mkdir(exist_ok=True)

    with (out_folder / f"all.obj").open("w") as out_file:
        out_file.write("mtllib image.mtl\no Terrain\n")

        for (x, y) in itertools.product(range(work.extent.count_x), range(work.extent.count_y)):
            if(x % skip) != 0 or (y % skip) != 0:
                continue
            out_file.write(f"v {float(x) * scale} {float(y) * scale} {outmap[x][y] * scale}\n")

        out_file.write("usemtl Material.001\ns off\n")

        face_count = {"x": work.extent.count_x // skip, "y": work.extent.count_y // skip}

        u_factor = 1.0 / (face_count['x'] - 1)
        v_factor = 1.0 / (face_count['y'] - 1)

        for x in range(face_count['x']):
            for y in range(face_count['y']):
                u = x * u_factor
                v = y * v_factor
                out_file.write(f"vt {u} {v}\n")

        faces = []

        min_face_x = 0
        max_face_x = face_count['x'] - 1 - 0
        min_face_y = 0
        max_face_y = face_count['y'] - 1 - 0

        print(min_face_x, max_face_x, face_count['x'])
        print(min_face_y, max_face_y, face_count['y'])

        for y in range(min_face_y, max_face_y):
            for x in range(min_face_x, max_face_x):
                corner = x + face_count['y'] * y
                corners = (corner, corner + 1, corner + face_count['x'] + 1, corner + face_count['x'])
                corners = [(c + 1, c + 1) for c in corners]
                faces.append(list(reversed(corners)))

        for face in faces:
            t_faces = map(lambda x: f"{x[0]}/{x[1]}", face)
            out_file.write(f"f {' '.join(t_faces)}\n")

    with (out_folder / f"image.mtl").open("w") as out_file:
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
    # import building_json
    # building_json.apply_all(gml_files, out_folder, (min_x, min_y, 0), scale)


if __name__ == '__main__':
    load_all(Path(sys.argv[1]))
