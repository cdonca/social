from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, QuerySet


class PostManager(QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def feed(self, user: object):
        return self\
            .posts()\
            .filter(Q(author__followers=user) | Q(author=user))\
            .distinct()

    def posts(self):
        reply_ids = ArrayAgg(
            'alt__author_id',
            filter=Q(alt__is_reply=True, alt__is_active=True),
        )
        repost_ids = ArrayAgg(
            'alt__author_id',
            filter=Q(alt__is_reply=False, alt__is_active=True),
        )
        return self\
            .active()\
            .filter(is_reply=False)\
            .prefetch_related('author__following')\
            .prefetch_related('author__followers')\
            .prefetch_related('liked')\
            .select_related('author__profile')\
            .annotate(
                reply_ids=reply_ids,
                repost_ids=repost_ids,
            )

    def profile_posts(self, user):
        return self.posts().filter(author=user)

    def recommend_posts(self, user: object, long=False):
        qs = self.posts()\
            .exclude(author__followers=user)\
            .filter(
                ~Q(author=user),
                parent=None,
            )\
            .order_by('?')
        if long is False:
            qs = qs[:5]
        return qs