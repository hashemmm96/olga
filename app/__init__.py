from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from app.db import get_db


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=Path("db.sqlite3"),
    )

    @app.route("/", methods=["GET", "POST"])
    def home():
        if request.method == "POST":
            return search(request.form["search-bar"])

        return render_template("index.html")

    @app.route("/tabs")
    def get_tab():
        artist = request.args["artist"]
        title = request.args["title"]
        params = {
            "artist": artist,
            "title": title,
        }

        db = get_db()
        content = db.execute(
            "SELECT content from tabs WHERE artist == :artist AND title == :title",
            params,
        ).fetchone()

        document_title = f"{format_col(artist)}: {format_col(title)}"
        html = txt_to_html(content["content"])
        return render_template("document.html", content=html, title=document_title)

    @app.route("/guides")
    def get_guide():
        return "HEJ"

    def search(search_text):
        subs = {
            " ": "_",
            "-": "_",
            "å": "a",
            "ä": "a",
            "ö": "o",
        }
        expr = search_text.strip()
        for k, v in subs.items():
            expr = expr.replace(k, v)

        params = {"expr": f".*{expr}.*"}

        db = get_db()
        tab_search = db.execute(
            "SELECT artist,title from tabs WHERE artist REGEXP :expr OR title REGEXP :expr",
            params,
        ).fetchall()
        guide_search = db.execute(
            "SELECT title from guides WHERE title REGEXP :expr", params
        ).fetchall()

        tabs = []
        for result in tab_search:
            artist_result = result["artist"]
            title_result = result["title"]
            artist = format_col(artist_result)
            title = format_col(title_result)

            tabs.append(
                {
                    "entry": f"{artist}: {title}",
                    "link": f"/tabs?artist={artist_result}&title={title_result}",
                }
            )

        guides = []
        for result in guide_search:
            title_result = result["title"]
            title = format_col(title_result)
            guides.append(
                {
                    "entry": f"{title}",
                    "link": f"/guides?title={title_result}",
                }
            )

        return render_template("result.html", tabs=tabs, guides=guides)

    def format_col(col):
        return Path(col).stem.replace("_", " ").title()

    def txt_to_html(txt):
        html = ""
        for line in txt.splitlines():
            html += f"{line}<br>"
        return html

    return app
