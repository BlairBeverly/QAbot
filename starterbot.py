import os
import time
import random
from mysqlconnection import MySQLConnector
from slackclient import SlackClient

mysql = MySQLConnector()

# constants
BOT_ID = os.environ.get("BOT_ID") # starterbot's ID as an environment variable
BOT_NAME = "starterbot"
AT_BOT = "<@" + BOT_ID + ">"
CATEGORIES_COMMAND = "categories" 
ASK_COMMAND = "I'll take"
ANSWER_COMMAND = "answer"

class QuestionAnswerBot(object):
    def __init__(self):
        self.question = ''
        self.answer = ''
        self.default_response = "I'm ready to play a game! Say *@{} {}* to "\
            "see a list of available question categories and their point "\
            "values.".format(BOT_NAME, CATEGORIES_COMMAND)

        # instantiate Slack client
        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

    def get_categories_response(self):
        """
        Returns a string detailing the list of available questions and 
        how much each question is worth
        """
        query_result = mysql.query_db("SELECT category, point_value FROM "
            "questions GROUP BY 1,2 ORDER BY point_value ASC")
        response = "Here are the avaialble question categories and point "\
                   "values:\n'"

        for row in query_result:
            response += "{}: {} points\n".format(
                row['category'], row['point_value'])

        response += ("\nUse the *{}* command followed by the category "\
            "and point value to a question. For example, '@{} I'll take "\
            "Python 100'".format(ASK_COMMAND, BOT_NAME))
        
        return response


    def set_question_answer(self, category, point_value):
        """
        Queries the database to set the bot's question and answer.
        """

        question_list = mysql.query_db(
            "SELECT question, answer FROM questions WHERE category = '{}' "\
            "AND point_value = {}".format(category, point_value))

        # Choose a random row to get a question & answer
        random_choice = random.choice(range(0,len(question_list)))
        
        self.question = question_list[random_choice]['question']
        self.answer = question_list[random_choice]['answer']


    def handle_command(self, command, channel):
        """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
        """
        print "user command:", command

        response = self.default_response

        if command.lower().startswith(ASK_COMMAND.lower()):
            if self.question:
                response = "I've already asked a question. Answer that one "\
                           "first and then I can give you another."
            else:
                # Assuming command looks something like: 'I'll take Python 100'
                try:
                    category, point_value = command[9:].split()
                except ValueError:
                    response = "Give me a command that looks something like: "\
                    "'I'll take Python 100'"

                self.set_question_answer(category, point_value)
                response = self.question

        elif command.lower().startswith(ANSWER_COMMAND.lower()):
            answer = command.split(":")[1].strip().lower()
            print "user answer:", answer

            if self.question:
                expected_answer = self.answer.lower()
                print "bot answer:", expected_answer

                if answer.find(expected_answer) > -1:
                    response = "That's right! Great job."
                    self.question = ''
                    self.answer = ''
                else:
                    response = "Sorry, that's not the right answer."
            else:
                response = "I didn't ask a question!"

        elif command.lower().startswith(CATEGORIES_COMMAND.lower()):
            response = self.get_categories_response()

        self.slack_client.api_call("chat.postMessage", channel=channel,
                              text=response, as_user=True)

                
    def parse_slack_output(self, slack_rtm_output):
        """The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(AT_BOT)[1].strip().lower(), \
                           output['channel']
        return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose

    bot = QuestionAnswerBot()

    if bot.slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = bot.parse_slack_output(bot.slack_client.rtm_read())
            if command and channel:
                bot.handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")































