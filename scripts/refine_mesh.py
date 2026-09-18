from pathlib import Path
p=Path('apex_racer/scripts/build_print_in_place.py');s=p.read_text(encoding='utf-8').replace('LinearDeflection=.10,AngularDeflection=.17','LinearDeflection=.025,AngularDeflection=.08');p.write_text(s,encoding='utf-8')
