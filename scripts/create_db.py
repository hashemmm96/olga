import argparse
import gzip
import sqlite3
import sys
import zipfile
from pathlib import Path

import magic
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(description="Convert OLGA archive to sqlite3 db")

    parser.add_argument("input", help="OLGA zip file")
    parser.add_argument(
        "--db", default="db.sqlite3", help="database path (default: %(default)s)"
    )
    parser.add_argument(
        "--skip-unzip",
        action="store_true",
        help="skip unzip",
    )
    parser.add_argument(
        "--skip-gunzip",
        action="store_true",
        help="skip gunzip",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="skip db populate",
    )

    args = parser.parse_args()

    olga_zip = Path(args.input)

    if not olga_zip.exists():
        print(f"error: {olga_zip} does not exist", file=sys.stderr)
        sys.exit(1)

    tmpdir = Path(".tmp")
    if not tmpdir.exists():
        tmpdir.mkdir()

    if not args.skip_unzip:
        unzip(olga_zip, tmpdir)

    if not args.skip_gunzip:
        gunzip(tmpdir)

    if not args.skip_db:
        create_records(args.db, tmpdir)


def unzip(zip, tmpdir):
    with zipfile.ZipFile(zip) as z:
        # Instead of extractall, iterate to get progress bar
        for file in tqdm(z.namelist(), desc="Extracting zipfile..."):
            fp = tmpdir / Path(file)

            if fp.suffix != ".gz":
                continue

            if fp.exists():
                continue

            z.extract(file, path=tmpdir)


def gunzip(tmpdir):
    files = walk(tmpdir)
    for file in tqdm(files, desc="Extracting gzipped files..."):
        if file.suffix != ".gz":
            continue

        extracted_file = file.parent / file.stem
        if extracted_file.exists():
            continue

        with gzip.open(file) as f:
            content = f.read()

        with open(extracted_file, "wb") as f:
            f.write(content)


def create_records(db, tmpdir):
    files = walk(tmpdir)
    tab_data = []
    other_data = []
    for file in tqdm(files, desc="Creating records..."):
        if file.suffix == ".gz":
            continue

        if not is_text_mimetype_file(file):
            continue

        with open(file, "rb") as f:
            content = f.read().decode(encoding="utf-8", errors="replace")

        record = {
            "title": file.name,
            "content": content,
        }

        if "tabs" in file.parts:
            record["artist"] = file.parent.name
            tab_data.append(record)

        else:
            other_data.append(record)

    print("Populating database...")
    db = sqlite3.connect(db)

    artist = "artist"
    title = "title"
    content = "content"
    tab_values = f"{artist}, {title}, {content}"
    tab_values_parameters = f":{artist}, :{title}, :{content}"
    tab_name = "tabs"

    # For other_stuff folder
    resource_values = "title, content"
    resource_values_parameters = "".join(
        [":" + value for value in resource_values.split(" ")]
    )
    resource_name = "resources"
    resource_table = f"{resource_name}({resource_values})"

    fts_values = f"{artist}, {title}"
    fts_name = f"{tab_name}_fts"

    with db:
        db.executescript(
            f"""
            BEGIN;

            CREATE TABLE IF NOT EXISTS {tab_name}({tab_values}, UNIQUE({tab_values}));
            CREATE TABLE IF NOT EXISTS {resource_name}({resource_values}, UNIQUE({resource_values}));
            CREATE VIRTUAL TABLE IF NOT EXISTS {fts_name} USING fts5 ({fts_values});

            CREATE TRIGGER IF NOT EXISTS insert_{fts_name} AFTER INSERT ON {tab_name}
            BEGIN 
                INSERT INTO {fts_name} ({fts_values}) VALUES (NEW.{artist}, NEW.{title});
            END;

            CREATE TRIGGER IF NOT EXISTS update_{fts_name}
            AFTER UPDATE ON {tab_name}
            BEGIN
                UPDATE {fts_name} SET {title}=NEW.{title} WHERE {artist}=NEW.{artist};
            END;

            CREATE TRIGGER IF NOT EXISTS delete_{fts_name}
            AFTER DELETE ON {tab_name}
            BEGIN
                DELETE FROM {fts_name}
                WHERE {title} = OLD.{title};
            END;

            COMMIT;
            """
        )

        db.executemany(
            f"INSERT OR IGNORE INTO {tab_name}({tab_values}) VALUES({tab_values_parameters})",
            tab_data,
        )
        db.executemany(
            f"INSERT OR IGNORE INTO {resource_name}({resource_values}) VALUES({resource_values_parameters})",
            other_data,
        )

    db.close()


def is_text_mimetype_file(file):
    mimetype = magic.from_file(file, mime=True)
    return mimetype == "text/plain" or mimetype == "message/rfc822"


def new_sql_values(values):
    new_values = []
    for val in values.split(" "):
        new_values.append("NEW." + val)
    return "".join(new_values)


def walk(path):
    files = []

    for item in path.iterdir():
        if item.is_dir():
            files += walk(item)
        if item.is_file():
            files.append(item)

    return files


if __name__ == "__main__":
    main()
