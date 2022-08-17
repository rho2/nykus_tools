from nykus_tools.scripts.model import Wall, Building
from typing import Dict, List
import json
from util import Vertex
import functools

def calc_model(model: Dict, local_var: Dict):
    assert all(k["name"] in local_var for k in model["input"])

    calc_vars = {**local_var}

    for v in model["variables"]:
        if v["name"] in calc_vars:
            continue
        calc_vars[v["name"]] = v["default"]

    for eq in model["equations"]:
        res = eval(eq["calc"], calc_vars)
        calc_vars[eq["result"]] = res

    points = {}
    for p in model['points']:
        coords = [c if isinstance(c, float) else eval(c, calc_vars) for c in p["value"]]
        points[p["index"]] = coords

    faces = {f["name"]: Wall(f["mat"], f["vertices"]) for f in model["faces"]}

    return points, faces


@functools.lru_cache
def load_model():
    with open("prototypes/rectangle_window.json") as fp:
        model = json.load(fp)
        return model


def create_windows(house: Building, points: Dict[str, List], hi: int):
    walls = [w for w in house.walls if w.wall_type == "WallSurface" and len(w.vertex_ids) == 4]

    if len(walls) != 4:
        # print(f"Not creating windows for building with {len(walls)} walls")
        return None

    model = load_model()

    current_var = {"b": .05, "e": 1.0}

    real_points = {}
    real_faces = []

    for wall_index, w in enumerate(walls):
        A, B, C, D = (Vertex(*points[v_id]) for v_id in w.vertex_ids)
        BA = (A - B)
        CB = (B - C)

        w = BA.length()
        h = CB.length()

        normal = BA.norm().cross(CB.norm()).norm()
        n = int((w - 2 * current_var["e"]) / 1.5)

        if n == 0:
            return None

        current_var["w_n"] = (w-2 * current_var["e"]) / n
        current_var["h_s"] = h / house.stories

        offsets, faces = calc_model(model, current_var)

        BAn = BA.norm()
        CBn = CB.norm()

        ccc = CBn * current_var["h_s"]

        for name, (o1, o2, o3) in offsets.items():
            offset = BAn*o1 + CBn * o2 + normal * (-o3)
            for ni in range(n):
                n_offset = BAn * (ni * current_var["w_n"] + current_var["e"]) + C
                for si in range(house.stories):
                    origin = n_offset + ccc * si
                    real_point = origin + offset
                    real_points[f"{hi}_{wall_index}_{name}_{ni}_{si}"] = real_point

                    base1 = f"{hi}_{wall_index}_"
                    base2 = f"_{ni}_{si}"

                    for fname, f in faces.items():
                        # real_faces.append(f)
                        real_faces.append(Wall(f.wall_type, [f"{base1}{vi}{base2}" for vi in f.vertex_ids]))

        real_points[f"{hi}_{wall_index}_elA"] = (C + BAn * current_var["e"] + CBn * h)
        real_points[f"{hi}_{wall_index}_elB"] = (C + CBn * h)
        real_points[f"{hi}_{wall_index}_elC"] = (C)
        real_points[f"{hi}_{wall_index}_elD"] = (C + BAn * current_var["e"])

        real_points[f"{hi}_{wall_index}_erA"] = (C + BAn * w + CBn * h)
        real_points[f"{hi}_{wall_index}_erB"] = (C + BAn * (w - current_var["e"])+ CBn * h)
        real_points[f"{hi}_{wall_index}_erC"] = (C + BAn * (w - current_var["e"]))
        real_points[f"{hi}_{wall_index}_erD"] = (C + BAn * w)

        real_faces.append(Wall("DecoSurface", [
            f"{hi}_{wall_index}_elA",
            f"{hi}_{wall_index}_elB",
            f"{hi}_{wall_index}_elC",
            f"{hi}_{wall_index}_elD"
        ]))
        real_faces.append(Wall("DecoSurface", [
            f"{hi}_{wall_index}_erA",
            f"{hi}_{wall_index}_erB",
            f"{hi}_{wall_index}_erC",
            f"{hi}_{wall_index}_erD"
        ]))

    # print(real_faces[0])
    # print(real_faces[1])
    return real_points, real_faces