from pathlib import Path
p=Path('apex_racer/scripts/build_racer.py');s=p.read_text(encoding='utf-8');head,tail=s.split("scene={'meshes':{},'instances':[]}",1);p.write_text(head+"if __name__ == '__main__':\n"+'\n'.join('    '+line if line else '' for line in ("scene={'meshes':{},'instances':[]} "+tail).splitlines())+'\n',encoding='utf-8')
