import csv
import os
from datetime import date, datetime
from typing import List

from bisect import bisect_left, insort_left

from werkzeug.security import generate_password_hash

from movieflix.adapters.repository import AbstractRepository, RepositoryException
from movieflix.domain.model import Movie, User, Review, make_genre_association, make_review


class MemoryRepository(AbstractRepository):
    # Movies ordered by release year, not id. id is assumed unique.

    def __init__(self):
        # wtf bro Movie_file_CSV_reader()
        self._movies = list()
        self._movies_index = dict()
        self._genres = list()
        self._users = list()
        self._reviews = list()

    def add_user(self, user: User):
        self._users.append(user)

    def get_user(self, user_name) -> User:
        return next((user for user in self._users if user.user_name == user_name), None)

    def add_movie(self, movie: Movie):
        insort_left(self._movies, movie)
        self._movies_index[movie.id] = movie

    def get_movie(self, id: int) -> Movie:
        movie = None

        try:
            movie = self._movies_index[id]
        except KeyError:
            pass  # Ignore exception and return None.

        return movie

    def get_movies_by_year(self, target_year: date) -> List[Movie]:
        target_movie = Movie(

            release_year=target_year,
            title=None,
            description=None,
            director=None,
            actors=None,
            genres=None,
            runtime_minutes=None
        )
        matching_movies = list()

        try:
            index = self.movie_index(target_movie)
            for movie in self._movies[index:None]:
                if movie.release_year == target_year:
                    matching_movies.append(movie)
                else:
                    break
        except ValueError:
            # No movies for specified year. Simply return an empty list.
            pass

        return matching_movies

    def get_number_of_movies(self):
        return len(self._movies)

    def get_first_movie(self):
        movie = None

        if len(self._movies) > 0:
            movie = self._movies[0]
        return movie

    def get_last_movie(self):
        movie = None

        if len(self._movies) > 0:
            movie = self._movies[-1]
        return movie

    def get_movies_by_id(self, id_list):
        # Strip out any ids in id_list that don't represent Movie ids in the repository.
        existing_ids = [id for id in id_list if id in self._movies_index]

        # Fetch the Movies.
        movies = [self._movies_index[id] for id in existing_ids]
        return movies

#wtf bro
    def get_movie_ids_for_tag(self, tag_name: str):
        # Linear search, to find the first occurrence of a Tag with the name tag_name.
        tag = next((tag for tag in self._tags if tag.tag_name == tag_name), None)

        # Retrieve the ids of movies associated with the Tag.
        if tag is not None:
            movie_ids = [movie.id for movie in tag.tagged_movies]
        else:
            # No Tag with name tag_name, so return an empty list.
            movie_ids = list()

        return movie_ids

    def get_year_of_previous_movie(self, movie: Movie):
        previous_year = None

        try:
            index = self.movie_index(movie)
            for stored_movie in reversed(self._movies[0:index]):
                if stored_movie.release_year < movie.release_year:
                    previous_year = stored_movie.release_year
                    break
        except ValueError:
            # No earlier movies, so return None.
            pass

        return previous_year

    def get_year_of_next_year(self, movie: Movie):
        next_year = None

        try:
            index = self.movie_index(movie)
            for stored_movie in self._movies[index + 1:len(self._movies)]:
                if stored_movie.release_year > movie.release_year:
                    next_year = stored_movie.release_year
                    break
        except ValueError:
            # No subsequent movies, so return None.
            pass

        return next_year
#wtf bro
    def add_tag(self, tag: Tag):
        self._tags.append(tag)

    def get_tags(self) -> List[Tag]:
        return self._tags

    def add_review(self, review: Review):
        super().add_review(review)
        self._reviews.append(review)

    def get_reviews(self):
        return self._reviews

    # Helper method to return movie index.
    def movie_index(self, movie: Movie):
        index = bisect_left(self._movies, movie)
        if index != len(self._movies) and self._movies[index].release_year == movie.release_year:
            return index
        raise ValueError


def read_csv_file(filename: str):
    with open(filename, encoding='utf-8-sig') as infile:
        reader = csv.reader(infile)

        # Read first line of the the CSV file.
        headers = next(reader)

        # Read remaining rows from the CSV file.
        for row in reader:
            # Strip any leading/trailing white space from data read.
            row = [item.strip() for item in row]
            yield row


def load_movies_and_tags(data_path: str, repo: MemoryRepository):
    tags = dict()

    for data_row in read_csv_file(os.path.join(data_path, 'movies.csv')):

        movie_key = int(data_row[0])
        number_of_tags = len(data_row) - 6
        movie_tags = data_row[-number_of_tags:]

        # Add any new tags; associate the current movie with tags.
        for tag in movie_tags:
            if tag not in tags.keys():
                tags[tag] = list()
            tags[tag].append(movie_key)
        del data_row[-number_of_tags:]

        # Create movie object.
        movie = Movie(
            release_year=release_year.fromisoformat(data_row[6]),
            title=data_row[2],
            description=data_row[3],
            director=data_row[4],
            actors=data_row[5],
            genres=data_row[2],
            id=movie_key
        )

        # Add the movie to the repository.
        repo.add_movie(movie)

    # Create Tag objects, associate them with Movies and add them to the repository.
    for tag_name in tags.keys():
        tag = Tag(tag_name)
        for movie_id in tags[tag_name]:
            movie = repo.get_movie(movie_id)
            make_tag_association(movie, tag)
        repo.add_tag(tag)


def load_users(data_path: str, repo: MemoryRepository):
    users = dict()

    for data_row in read_csv_file(os.path.join(data_path, 'users.csv')):
        user = User(
            user_name=data_row[1],
            password=generate_password_hash(data_row[2])
        )
        repo.add_user(user)
        users[data_row[0]] = user
    return users


def load_reviews(data_path: str, repo: MemoryRepository, users):
    for data_row in read_csv_file(os.path.join(data_path, 'reviews.csv')):
        review = make_review(
            review_text=data_row[3],
            user=users[data_row[1]],
            movie=repo.get_movie(int(data_row[2])),
            timestamp=datetime.fromisoformat(data_row[4])
        )
        repo.add_review(review)


def populate(data_path: str, repo: MemoryRepository):
    # Load movies and tags into the repository.
    load_movies_and_tags(data_path, repo)

    # Load users into the repository.
    users = load_users(data_path, repo)

    # Load reviews into the repository.
    load_reviews(data_path, repo, users)
