from .application import create_app


class DballeWebMixin:
    def create_app(self):
        app = create_app("sqlite://:memory:")
        app.db.reset()
        app.config["SERVER_NAME"] = "localhost"
        return app

    def setUp(self):
        super().setUp()
        self.app = self.create_app()

    def tearDown(self):
        self.app = None
        super().tearDown()
