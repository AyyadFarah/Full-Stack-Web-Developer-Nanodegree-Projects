import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    Set up CORS. Allow '*' for origins.
    Delete the sample route after completing the TODOs
    '''
    CORS(app, resources={r"*": {"origins": "*"}})
    '''
    the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, DELETE, OPTIONS')
        return response

    '''
    an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]
        return jsonify(
            {
                'success': True,
                'categories': formatted_categories
            })

    '''
    an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom
    of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route('/questions')
    def retrieve_questions():
        questions = Question.query.order_by(Question.id).all()
        wanted_questions = paginate_questions(request, questions)

        if len(wanted_questions) == 0:
            abort(404)

        categories = {question['category'] for question in wanted_questions}
        return jsonify({
            'success': True,
            'questions': wanted_questions,
            'totalQuestions': len(questions),
            'categories': list(categories)
        })

    def paginate_questions(request, questions):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        formatted_questions = [question.format() for question in questions]
        return formatted_questions[start:end]

    '''
    an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed.
    This removal will persist in the database and
    when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted':  question.id,
                'questions': current_questions,
                'totalQuestions': len(selection)
            })
        except Exception:
            abort(422)

    '''
    an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question
    will appear at the end of the last page
    of the questions list in the "List" tab.
    '''
    @app.route('/questions', methods=['POST'])
    def create_or_search_question():
        body = request.get_json()

        question = body.get('question', None)
        answer = body.get('answer', None)
        difficulty = body.get('difficulty', None)
        category = body.get('category', None)
        search_term = body.get('searchTerm', None)
        if search_term is None:
            return create_question(
                request, question, answer, difficulty, category)
        else:
            return search_questions(search_term)

    def create_question(request, question, answer, difficulty, category):
        try:
            question = Question(question, answer, category, difficulty)
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'totalQuestions': len(selection)
            })

        except Exception:
            abort(422)

    '''
    a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    def search_questions(search_term):
        current_questions = Question.query.filter(
            Question.question.ilike('%'+search_term+'%')).all()

        if len(current_questions) == 0:
            abort(404)

        formmated_current_questions = [
            question.format() for question in current_questions]
        return jsonify({
            'success': True,
            'questions': formmated_current_questions,
            'totalQuestions': len(current_questions)
        })

    '''
    a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route('/categories/<category_id>/questions')
    def retrieve_category_questions(category_id):
        questions = Question.query.filter(
            Question.category == category_id).order_by(Question.id).all()
        wanted_questions = paginate_questions(request, questions)

        if len(wanted_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': wanted_questions,
            'totalQuestions': len(questions)
        })

    '''
    a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
    @app.route('/quizzes', methods=['POST'])
    def random_question():
        body = request.get_json()
        quiz_category = body.get('quiz_category')
        previous_questions = body.get('previous_questions', [])
        try:
            questions = Question.query.filter(
                Question.category == quiz_category,
                Question.category.notin_(previous_questions)).all()
            index = random.randint(0, len(questions)-1)
            formatted_question = questions[index].format()
            return jsonify({
                'success': True,
                'question': formatted_question
            })
        except Exception:
            abort(404)

    '''
    error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    return app
