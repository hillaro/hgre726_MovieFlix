from flask import Blueprint, request, render_template, redirect, url_for, session

import movieflix.adapters.repository as repo
import movieflix.utilities.services as services


# Configure Blueprint.
utilities_blueprint = Blueprint(
    'utilities_bp', __name__)

# wtf bro


def get_tags_and_urls():
    tag_names = services.get_tag_names(repo.repo_instance)
    tag_urls = dict()
    for tag_name in tag_names:
        tag_urls[tag_name] = url_for('news_bp.articles_by_tag', tag=tag_name)

    return tag_urls


def get_selected_movies(quantity=3):
    movies = services.get_random_movies(quantity, repo.repo_instance)

    for movie in movies:
        movie['hyperlink'] = url_for('movies_bp.movies_by_date', date=movie['date'].isoformat())
    return movies
