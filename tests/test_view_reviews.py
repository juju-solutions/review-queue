from pyramid import testing

from base import (
    UnitTestBase,
    IntegrationTestBase,
)


class ReviewsUnitTest(UnitTestBase):
    def test_index(self):
        from reviewqueue.views.reviews import index

        request = testing.DummyRequest()

        response = index(request)
        self.assertEqual(1, response['reviews'].count())

    def test_new(self):
        from reviewqueue.views.reviews import new

        request = testing.DummyRequest()

        response = new(request)
        self.assertEqual(response, {})

    def test_create(self):
        from reviewqueue.views.reviews import create

        self.config.add_route('reviews_index', '/reviews')

        request = testing.DummyRequest()
        request.user = self.user
        request.params = dict(source_url='cs:foo')

        response = create(request)
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.location, request.route_url('reviews_index'))

    def test_show(self):
        from reviewqueue.views.reviews import show

        request = testing.DummyRequest()
        request.context = self.review

        response = show(request)
        self.assertEqual(response, dict(review=self.review))


class ReviewsIntegrationTest(IntegrationTestBase):
    def test_index(self):
        self.app.get('/reviews', status=200)

    def test_new_anonymous(self):
        self.app.get('/reviews/new', status=403)

    def test_create(self):
        pass

    def test_show(self):
        self.app.get('/reviews/{}'.format(self.review.id), status=200)
