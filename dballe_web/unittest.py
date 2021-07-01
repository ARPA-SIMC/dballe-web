from .webserver import make_app


class DballeWebMixin:
    def make_app(self):
        return make_app("sqlite://:memory:")

    def setUp(self):
        super().setUp()
        self.app = self.make_app()

    def tearDown(self):
        self.app = None
        super().tearDown()
