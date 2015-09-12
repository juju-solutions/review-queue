from base import (
    IntegrationTestBase,
)


class IntegrationTest(IntegrationTestBase):
    def test_get_home(self):
        """ GET Home page

        GET / 200

        """
        self.app.get('/')
