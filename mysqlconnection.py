from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import database_config


class MySQLConnection(object):
    def __init__(self):
        DATABASE_URI = "mysql+pymysql://{}:{}@{}:{}/{}".format(
            database_config.config['user'], 
            database_config.config['password'], 
            database_config.config['host'],
            database_config.config['port'], 
            database_config.config['database'])

        engine = create_engine(DATABASE_URI, echo=True)

        # create a configured 'Session' class
        Session = sessionmaker(bind=engine)
        self.session = Session()


    def query_db(self, query, data=None):
        result = self.session.execute(text(query), data)
        if query[0:6].lower() == 'select':
            # if the query was a select
            # convert the result to a list of dictionaries
            list_result = [dict(r) for r in result]
            # return the results as a list of dictionaries
            return list_result
        elif query[0:6].lower() == 'insert':
            # if the query was an insert, return the id of the 
            # commit changes
            self.session.commit()
            # row that was inserted
            return result.lastrowid
        else:
            # if the query was an update or delete, return nothing and commit changes
            self.session.commit()


def MySQLConnector():
    return MySQLConnection()
