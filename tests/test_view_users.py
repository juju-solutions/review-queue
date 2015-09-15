from pyramid import testing

from base import (
    UnitTestBase,
    IntegrationTestBase,
)


class UsersUnitTest(UnitTestBase):
    def test_show(self):
        from reviewqueue.views.users import show

        request = testing.DummyRequest()
        request.context = self.user

        response = show(request)
        self.assertEqual(response, dict(user=self.user))


class UsersIntegrationTest(IntegrationTestBase):
    def test_show(self):
        self.app.get('/users/tester', status=200)
