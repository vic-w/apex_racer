"""Local A1 mini slicing check. Produces diagnostics only; never sends a print."""

from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile


root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bambu-dir', type=Path, default=Path(r'D:\soft\Bambu Studio'))
args = parser.parse_args()
profiles = args.bambu_dir / 'resources/profiles/BBL'
paths = {path.stem: path for path in profiles.rglob('*.json')}
out = root / '.freecad_local/slicing'
out.mkdir(parents=True, exist_ok=True)


def flatten(name):
    data = json.loads(paths[name].read_text(encoding='utf-8'))
    parent = data.get('inherits')
    result = flatten(parent) if parent else {}
    result.update(data)
    result.pop('inherits', None)
    return result


for kind, name in [('machine', 'Bambu Lab A1 mini 0.4 nozzle'),
                   ('process', '0.20mm Standard @BBL A1M'),
                   ('filament', 'Generic PLA @BBL A1M')]:
    data = flatten(name)
    if kind == 'process':
        data.update(enable_support='0', wall_loops='3', sparse_infill_density='15%',
                    brim_type='no_brim', curr_bed_type='Textured PEI Plate')
    (out / (kind + '.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')

stl = root / 'print_in_place/apex_racer_side_down.stl'
project = out / 'supportless_check.3mf'
gcode_path = out / 'plate_1.gcode'
# Remove only this check's previous outputs so a failed run cannot appear fresh.
for generated in (project, gcode_path):
    generated.unlink(missing_ok=True)
with (out / 'slice.log').open('w', encoding='utf-8') as log:
    subprocess.run([
        str(args.bambu_dir / 'bambu-studio.exe'), '--debug', '2',
        '--load-settings', str(out / 'machine.json') + ';' + str(out / 'process.json'),
        '--load-filaments', str(out / 'filament.json'),
        '--orient', '0', '--arrange', '1', '--slice', '0',
        '--export-3mf', project.name, '--outputdir', str(out), str(stl),
    ], cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)

gcode = gcode_path.read_text(encoding='utf-8')
with zipfile.ZipFile(project) as archive:
    assert archive.testzip() is None
    info = ET.fromstring(archive.read('Metadata/slice_info.config'))
    settings = json.loads(archive.read('Metadata/project_settings.config'))
    model = ET.fromstring(archive.read('Metadata/model_settings.config'))
    assert archive.read('Metadata/plate_1.gcode') == gcode_path.read_bytes()
plate = info.find('plate')
metadata = {item.get('key'): item.get('value') for item in plate.findall('metadata')}
assert len(info.findall('plate')) == 1
assert metadata['outside'] == 'false' and metadata['support_used'] == 'false'
assert all(item.get('skipped') == 'false' for item in plate.findall('object'))
assert settings['printer_model'] == 'Bambu Lab A1 mini'
assert settings['enable_support'] == '0' and settings['curr_bed_type'] == 'Textured PEI Plate'
assert float(settings['layer_height']) == .2
features = set(re.findall(r'^; FEATURE: (.+)$', gcode, re.MULTILINE))
assert not any('support' in feature.lower() for feature in features), features
layers = int(re.search(r'^; total layer number: (\d+)', gcode, re.MULTILINE)[1])
assert layers == 282, layers
repairs = [item.attrib for item in model.findall('.//mesh_stat')]
assert repairs and all(int(value) == 0 for item in repairs
                       for key, value in item.items() if key != 'face_count'), repairs
version = next(item.get('value') for item in info.findall('header/header_item')
               if item.get('key') == 'X-BBL-Client-Version')
result = {
    'slicer': 'Bambu Studio ' + version,
    'stl_sha256': hashlib.sha256(stl.read_bytes()).hexdigest(),
    'printer': settings['printer_model'], 'nozzle_diameter_mm': .4,
    'layer_height_mm': .2, 'filament': 'Generic PLA',
    'plate': settings['curr_bed_type'], 'wall_loops': 3, 'infill_percent': 15,
    'brim_enabled': False, 'supports_enabled': False, 'support_toolpaths': False,
    'slicing_succeeded': True, 'layer_count': layers,
    'model_outside_build_volume': False, 'mesh_repairs': repairs,
    'estimated_seconds': int(metadata['prediction']),
    'estimated_filament_g': float(metadata['weight']),
    'limitation': 'Successful slicing without support is not a physical print test.',
}
report_path = root / 'print_in_place/validation_report.json'
report = json.loads(report_path.read_text())
report['slicing_check'] = result
report_path.write_text(json.dumps(report, indent=2))
print(json.dumps(result, indent=2))
