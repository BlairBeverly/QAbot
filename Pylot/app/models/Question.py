""" 
    Sample Model File

    A Model should be in charge of communicating with the Database. 
    Define specific model method that query the database for information.
    Then call upon these model method in your controller.

    Create a model using this template.
"""
from system.core.model import Model

class Question(Model):
    def __init__(self):
        super(Question, self).__init__()

    def get_questions(self):
        query = "SELECT id, question, answer, category, point_value "\
                "FROM questions;"
        return self.db.query_db(query)

    def get_question(self, id):
        query = "SELECT id, question, answer, category, point_value "\
                "FROM questions WHERE id = :id"
        data = {'id': id}

        return self.db.get_one(query, data)

    def edit_question(self, id, data):
        errors = []
        query = "UPDATE questions SET question = :question, answer = :answer, " \
                "category = :category, point_value = :point_value WHERE " \
                "id = :id"
        data = {'question': data['question'].strip(),
                'answer' : data['answer'].strip(),
                'category' : data['category'].strip(),
                'point_value' : int(data['point_value']),
                'id' : id}

        if data['point_value'] not in [100,200,300,400,500]:
            errors.append('Point value must be one of 100, 200, 300, 400, or 500 ')
            return {'status': 'not ok', 'errors' : errors}

        else:
            self.db.query_db(query, data)
            return {'status': 'ok'}

    def add_question(self, data):
        errors = []
        query = "INSERT INTO questions (question, answer, category, point_value) "\
                "VALUES (:question, :answer, :category, :point_value)"

        data = {'question': data['question'].strip(),
                'answer' : data['answer'].strip(),
                'category' : data['category'].strip(),
                'point_value' : int(data['point_value'].strip())}

        if data['point_value'] not in [100,200,300,400,500]:
            errors.append('Point value must be one of 100, 200, 300, 400, or 500 ')
            return {'status': 'not ok', 'errors' : errors}

        else:
            self.db.query_db(query, data)
            return {'status': 'ok'}

    def remove_question(self, id):
        query = "DELETE FROM questions WHERE id = :id"
        data = {'id' : id}
        self.db.query_db(query, data)