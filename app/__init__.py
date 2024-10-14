from pathlib import Path

from flask import Flask, render_template, request

from app.db import get_db


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=Path("db.sqlite3"),
    )

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            return search(request.form["search-bar"])

        db = get_db()
        resource_search = db.execute(
            "SELECT title from resources ORDER BY title ASC",
        ).fetchall()
        resources = []
        for result in resource_search:
            title_result = result["title"]
            title = format_col(title_result)
            resources.append(
                {
                    "entry": f"{title}",
                    "link": f"/resources?title={title_result}",
                }
            )

        return render_template("index.html", resources=resources)

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

    @app.route("/resources")
    def get_resource():
        title = request.args["title"]
        params = {
            "title": title,
        }

        db = get_db()
        content = db.execute(
            "SELECT content from resources WHERE title == :title",
            params,
        ).fetchone()

        document_title = format_col(title)
        html = txt_to_html(content["content"])
        return render_template("document.html", content=html, title=document_title)

    def search(search_text):
        params = {"search": search_text}

        db = get_db()
        tab_search = db.execute(
            "SELECT * FROM tabs_fts WHERE tabs_fts MATCH :search ORDER BY rank",
            params,
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

        return render_template("result.html", tabs=tabs)

    def format_col(col):
        return Path(col).stem.replace("_", " ").title()

    def txt_to_html(txt):
        html = ""
        for line in txt.splitlines():
            html += f"{line}<br>"
        return html

    return app
