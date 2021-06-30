import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route(r"/api/1.0/export/<format>")
def export(format):
    """
    Download data selected in the current section
    """
    ...  # TODO
    # fname = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    # self.set_header("Content-Disposition", 'attachment; filename="{}.{}"'.format(fname, format))
    # if format == "csv":
    #     self.set_header("Content-Type", "text/csv")
    # else:
    #     self.set_header("Content-Type", "application/octet-stream")
    # writer = WriteToHandler(self)
    # yield to_tornado_future(asyncio.ensure_future(self.application.session.export(format, writer)))
