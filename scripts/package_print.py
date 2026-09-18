from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
names = ('apex_racer_side_down.stl', 'README.md', 'validation_report.json',
         'bed_contact_preview.png')
for name in names:
    if not (root / 'print_in_place' / name).is_file():
        raise FileNotFoundError(root / 'print_in_place' / name)

with zipfile.ZipFile(root / 'apex_racer_print_pack.zip', 'w',
                     compression=zipfile.ZIP_DEFLATED) as archive:
    for name in names:
        archive.write(root / 'print_in_place' / name, arcname=name)
print('Print archive saved: apex_racer_print_pack.zip')
