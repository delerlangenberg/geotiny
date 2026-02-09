def attach_pages(app):
    from flask import render_template, redirect

    @app.get("/spectrum")
    def page_spectrum():
        return render_template("pages/spectrum.html")

    @app.get("/")
    def home_overview():
        return render_template("pages/overview.html")
