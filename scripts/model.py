from typing import Tuple, List, NamedTuple, Dict


class Wall(NamedTuple):
    wall_type: str
    vertex_ids: List[str]


class Building:
    name: str
    stories: int
    walls: List[Wall]

    def __init__(self, name: str, stories: int):
        self.name = name
        self.stories = stories
        self.walls = []

    def __repr__(self):
        return f"{self.name} {self.stories} {self.walls}"

    def replace_actual_walls(self, walls: List[Wall]):
        # print(f"Building {self.name} has {len(self.walls)} walls")
        self.walls = [w for w in self.walls if w.wall_type != "WallSurface" or len(w.vertex_ids) != 4]
        assert isinstance(walls[0], Wall)
        assert isinstance(walls[-1], Wall), walls[-1]
        self.walls.extend(walls)
        # print(f"Building {self.name} has {len(self.walls)} walls")