from .random import Random
from .recommender import Recommender
import random


class ContextualMod(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    users = dict()

    def __init__(self, tracks_redis, catalog):
        self.tracks_redis = tracks_redis
        self.random = Random(tracks_redis)
        self.catalog = catalog

    @staticmethod
    def choose_prev(list_prev_tracks):
        _, times_list = zip(*list_prev_tracks)
        indexes = [i for i in range(len(times_list))]
        chosen_index = random.choices(indexes, weights=times_list)[0]
        return list_prev_tracks[chosen_index]

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:

        if prev_track_time == 1:  # будем считать это как новый день
            self.users[user] = list()
        self.users[user].append((prev_track, prev_track_time))
        list_prev_tracks = self.users[user]

        prev_track, prev_track_time = self.choose_prev(list_prev_tracks)

        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.random.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if not recommendations:
            return self.random.recommend_next(user, prev_track, prev_track_time)

        return random.choice(recommendations)
