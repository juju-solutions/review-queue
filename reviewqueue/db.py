from . import models as M


class DB(object):
    def __init__(self):
        self.session = M.DBSession()

    def _get_object(self, klass, **kw):
        return self.session.query(klass) \
            .filter_by(**kw) \
            .first()

    def flush(self):
        self.session.flush()

    def get_review(self, **kw):
        return self._get_object(M.Review, **kw)

    def get_reviews(self):
        return self.session.query(M.Review) \
            .order_by(M.Review.created_at)

    def create_review(self, user, **kw):
        review = M.Review(**kw)
        review.status = M.Status.TESTING
        user.reviews.append(review)
        return review

    def vote_on_review(self, review, user, vote):
        if (vote == 0 or vote not in
                range(review.MIN_SCORE,
                      review.MAX_SCORE + 1)):
            return False

        review.votes.append(
            M.Vote(user=user, vote=vote))

        if review.score <= review.MIN_SCORE:
            review.reject()

        if review.score >= review.MAX_SCORE:
            review.accept()

        return True

    def get_user(self, **kw):
        return self._get_object(M.User, **kw)

    def create_user(self, **kw):
        u = M.User(**kw)
        self.session.add(u)
        return u
