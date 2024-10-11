import argparse
import gzip
import shutil
import sys
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Convert OLGA archive to static contents for web page"
)

parser.add_argument(
    "input", help="OLGA zip file, not required if --skip-unzip is unset"
)
parser.add_argument("output", help="output dir")

parser.add_argument("-f", "--force", action="store_true", help="overwrite output dir")


args = parser.parse_args()

outdir = Path(args.output)
olga_zip = Path(args.input)

if not olga_zip.exists():
    print(f"error: {olga_zip} does not exist", file=sys.stderr)
    sys.exit(1)


if outdir.exists():
    if args.force:
        shutil.rmtree(outdir)
    else:
        print(f"error: {outdir} exists, use --force to overwrite", file=sys.stderr)
        sys.exit(1)

outdir.mkdir()

print("Decompressing all files, this can take a while...")

with zipfile.ZipFile(olga_zip, "r") as f:
    files = f.extractall(outdir)

php_files = list(outdir.rglob("*index.php*"))

for f in php_files:
    f.unlink()

compressed_files = list(outdir.rglob("*.gz"))

for file in compressed_files:
    with gzip.open(file, "rb") as f:
        contents = f.read()

    new_file = file.parent / file.stem
    with open(new_file, "wb") as f:
        f.write(contents)

    file.unlink()

print("Finished")
