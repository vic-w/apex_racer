from pathlib import Path

import Mesh


root = Path(__file__).resolve().parents[1]
mesh = Mesh.Mesh(str(root / "print_in_place" / "apex_racer_side_down.stl"))
assert mesh.isSolid()
mesh.write(str(root / "apex_racer.3mf"))
print("Standard 3MF exported")
