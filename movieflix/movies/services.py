from typing import List, Iterable

from movieflix.adapters.repository import AbstractRepository
# wtf bro
from movieflix.domain.model import make_review, Movie, Review, Tag


class NonExistentMovieException(Exception):
    pass


class UnknownUserException(Exception):
    pass


def add_review(movie_id: int, review_text: str, user_name: str, repo: AbstractRepository):
    # Check that the movie exists.
    movie = repo.get_movie(movie_id)
    if movie is None:
        raise NonExistentMovieException

    user = repo.get_user(user_name)
    if user is None:
        raise UnknownUserException

    # Create review.
    review = make_review(review_text, user, movie)

    # Update the repository.
    repo.add_review(review)


def get_movie(movie_id: int, repo: AbstractRepository):
    movie = repo.get_movie(movie_id)

    if movie is None:
        raise NonExistentMovieException

    return movie_to_dict(movie)


def get_first_movie(repo: AbstractRepository):

    movie = repo.get_first_movie()

    return movie_to_dict(movie)


def get_last_movie(repo: AbstractRepository):

    movie = repo.get_last_movie()
    return movie_to_dict(movie)


def get_movies_by_date(date, repo: AbstractRepository):
    # Returns movies for the target date (empty if no matches), the date of the previous movie (might be null), the date of the next movie (might be null)

    movies = repo.get_movies_by_date(target_date=date)

    movies_dto = list()
    prev_date = next_date = None

    if len(movies) > 0:
        prev_date = repo.get_date_of_previous_movie(movies[0])
        next_date = repo.get_date_of_next_movie(movies[0])

        # Convert Movies to dictionary form.
        movies_dto = movies_to_dict(movies)

    return movies_dto, prev_date, next_date

# wtf bro
def get_movie_ids_for_tag(tag_name, repo: AbstractRepository):
    movie_ids = repo.get_movie_ids_for_tag(tag_name)

    return movie_ids


def get_movies_by_id(id_list, repo: AbstractRepository):
    movies = repo.get_movies_by_id(id_list)

    # Convert Movies to dictionary form.
    movies_as_dict = movies_to_dict(movies)

    return movies_as_dict


def get_reviews_for_movie(movie_id, repo: AbstractRepository):
    movie = repo.get_movie(movie_id)

    if movie is None:
        raise NonExistentMovieException

    return reviews_to_dict(movie.reviews)


# ============================================
# Functions to convert model entities to dicts
# ============================================

def movie_to_dict(movie: Movie):
    movie_dict = {
        'id': movie.id,
        'release_year': movie.release_year,
        'title': movie.title,
        'image_hyperlink': movie.image_hyperlink,
        'reviews': reviews_to_dict(movie.reviews),
        'tags': tags_to_dict(movie.tags)
    }
    return movie_dict


def movies_to_dict(movies: Iterable[Movie]):
    return [movie_to_dict(movie) for movie in movies]


def comment_to_dict(comment: Comment):
    comment_dict = {
        'user_name': comment.user.user_name,
        'movie_id': comment.movie.id,
        'comment_text': comment.comment,
        'timestamp': comment.timestamp
    }
    return comment_dict


def comments_to_dict(comments: Iterable[Comment]):
    return [comment_to_dict(comment) for comment in comments]


def tag_to_dict(tag: Tag):
    tag_dict = {
        'name': tag.tag_name,
        'tagged_movies': [movie.id for movie in tag.tagged_movies]
    }
    return tag_dict


def tags_to_dict(tags: Iterable[Tag]):
    return [tag_to_dict(tag) for tag in tags]


# ============================================
# Functions to convert dicts to model entities
# ============================================

def dict_to_movie(dict):
    movie = Movie(dict.id, dict.date, dict.title)
    # Note there's no comments or tags.
    return movie
