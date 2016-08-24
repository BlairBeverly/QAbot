"""
    Sample Controller File

    A Controller should be in charge of responding to a request.
    Load models to interact with the database and load views to render them to the client.

    Create a controller using this template
"""
from system.core.controller import *


class Questions(Controller):
    def __init__(self, action):
        super(Questions, self).__init__(action)
        """
            This is an example of loading a model.
            Every controller has access to the load_model method.
        """
        self.load_model('Question')
        self.db = self._app.db

        """
        
        This is an example of a controller method that will load a view for the client 

        """
   
    def index(self):
        if 'user' in session:
            questions = self.models['Question'].get_questions()
            return self.load_view('questions/index.html', questions=questions)
        else:
            return self.load_view('questions/login.html')

    def login(self):
        username = request.form['username']
        password = request.form['password']

        if username != '' and password != '':
            session['user'] = username

        else:
            flash("Wrong username and/or password")
        
        return redirect('/')

    def add(self):
        if 'user' in session:
            data = request.form
            response = self.models['Question'].add_question(data)

            if response['status'] == 'ok':
                return redirect('/')

            else:
                for error in response['errors']:
                    flash(error)
                    return redirect('/questions/show_add')
        else:
            return redirect('/')

    def edit(self, id):
        if 'user' in session:
            data = request.form
            response = self.models['Question'].edit_question(id, data)

            if response['status'] == 'ok':
                return redirect('/')

            else:
                for error in response['errors']:
                    flash(error)
                    return redirect('/questions/show_edit/' + id)
        else:
            return redirect('/')


    def delete(self, id):
        if 'user' in session:
            self.models['Question'].remove_question(id)
        return redirect('/')

    def show_add(self):
        if 'user' in session:
            return self.load_view('questions/add.html')
        else:
            return redirect('/')

    def show_edit(self, id):
        if 'user' in session:
            question = self.models['Question'].get_question(id)
            return self.load_view('questions/edit.html', question=question)
        else:
            return redirect('/')




