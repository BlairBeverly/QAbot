import os
import time
import random
from mysqlconnection import MySQLConnector
from slackclient import SlackClient
import re
import slackapitoken

mysql = MySQLConnector()

# constants
BOT_ID = slackapitoken.BOT_ID
BOT_NAME = slackapitoken.BOT_NAME
BOT_TOKEN = slackapitoken.BOT_TOKEN
AT_BOT = "<@" + BOT_ID + ">"
QUESTIONS_COMMAND = "questions" 
ASK_COMMAND = "I'll take"
ANSWER_COMMAND = "answer"
SCOREBOARD_COMMAND = "scoreboard"
NUM_QUESTIONS = 4
RESET_COMMAND = "reset"
SPLIT_REGEX_PATTERN = r":?\s*"
NEXT_COMMAND = "next"

class QuizBot(object):
    def __init__(self):
        self.current_question = ''
        self.current_answer = ''
        self.current_point_value = 0
        self.scoreboard = {}
        self.default_response = "I'm ready to play a game! Say *@{} {}* to "\
            "see a list of available questions and their point values." \
            .format(BOT_NAME, QUESTIONS_COMMAND)

        self.available_questions = random.sample(
            self.get_all_questions(), NUM_QUESTIONS)

        print self.available_questions

        # instantiate Slack client
        self.slack_client = SlackClient(BOT_TOKEN)

    def get_all_questions(self):
        all_questions = mysql.query_db("SELECT question, answer, category, "\
                                       "point_value FROM questions")
        return all_questions


    def get_questions_response(self, name):
        """
        Returns a string detailing the list of available questions and 
        how much each question is worth.
        """
        response = "Here are the avaialble question categories and point "\
                   "values, {}:\n".format(name)

        for question in self.available_questions:
            response += "{}: {} points\n".format(
                question['category'], question['point_value'])

        response += ("\nUse the *{}* command followed by the category "\
            "and point value to a question. For example, '@{} I'll take "\
            "Python 100'".format(ASK_COMMAND, BOT_NAME))
        
        return response


    def set_question_answer(self, category, point_value):
        """
        Set the bot's question and answer.
        """
        print category
        print point_value

        # Choose a question with the given category and point value
        for index, question in enumerate(self.available_questions):
            print question
            if question['category'].lower() == category and question['point_value'] \
            == point_value:
                print "match"
                self.current_question = "For {} points: {}".format(
                    point_value, question['question'])
                self.current_answer = question['answer']
                self.current_point_value = question['point_value']
                del self.available_questions[index]
                return 'ok'


    def handle_command(self, command, channel, user):
        """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
        """

        api_call = self.slack_client.api_call("users.info", user=user)
        if api_call.get('ok'):
            name = api_call.get("user")['profile']['first_name']

        print "user command:", command

        response = self.default_response

        if command.lower().startswith(RESET_COMMAND.lower()):
            self.available_questions = random.sample(
                self.get_all_questions(), NUM_QUESTIONS)
            self.scoreboard = {}

            response = "Questions and scores are reset! Tell me '{}' to see the "\
                       "available questions and their point values"\
                       .format(QUESTIONS_COMMAND)

        elif command.lower().startswith(ASK_COMMAND.lower()):
            if self.current_question:
                response = "I've already asked a question, {}. Answer that one "\
                           "first and then I can ask another.".format(name)
            else:
                # Assuming command looks something like: 'I'll take Python 100'
                if len(self.available_questions) == 0:
                    response = "There are no more questions! Tell me 'reset' "\
                               "to play another game."

                else:
                    try:
                        category, point_value = re.split(
                            SPLIT_REGEX_PATTERN, command[len(ASK_COMMAND):].strip())

                        response_status = self.set_question_answer(
                            category.strip(), int(point_value.strip()))
                        
                        if response_status == 'ok':
                            response = self.current_question + "\n (Type "\
                            "'@{} answer:<your answer>' to answer the question)".format(
                                BOT_NAME)
                        else:
                            response = self.get_questions_response(name)
                    
                    except ValueError:
                        response = "{}, give me a command that looks something like: "\
                        "'I'll take Python 100'".format(name)

        elif command.lower().startswith(NEXT_COMMAND.lower()):
            pass


        elif command.lower().startswith(ANSWER_COMMAND.lower()):
            answer = re.split(SPLIT_REGEX_PATTERN, command)[1].strip().lower()
            print "user answer:", answer

            if self.current_question:
                expected_answer = self.current_answer.lower()
                print "bot answer:", expected_answer

                if answer.find(expected_answer) > -1:
                    if name not in self.scoreboard:
                        self.scoreboard[name] = int(self.current_point_value)
                    else:
                        self.scoreboard[name] += int(self.current_point_value)
                    self.current_question = ''
                    self.current_answer = ''
                    self.current_point_value = 0

                    if len(self.available_questions) == 0:
                        winner = self.scoreboard.iterkeys().next()
                        for player in self.scoreboard:
                            if self.scoreboard[winner] < self.scoreboard[player]:
                                winner = player

                        response = "That's right, {}! Great job. You answered "\
                        " the last available question. Congrats to {} for winning "\
                        "the game!\n Tell me 'reset' to start another game".format(name, winner)

                    else:
                        response = "That's right, {}! Great job.\n\n Tell me 'scoreboard'"\
                        " to see who's in the lead!\n\n Use the *I'll take* command to "\
                        " choose another question with a point value. Or you can" \
                        " just tell me 'next' to get the next question in the same" \
                        " same category as the last question.".format(name)
                else:
                    response = "Sorry, {}. {} isn't the right answer.".format(name, answer)
            else:
                response = "I didn't ask a question, {}!".format(name)

        elif command.lower().startswith(QUESTIONS_COMMAND.lower()):
            response = self.get_questions_response(name)

        elif command.lower().startswith(SCOREBOARD_COMMAND.lower()):
            scores = ''
            for player, score in self.scoreboard.iteritems():
                scores += "{}: {} points\n".format(player, score)

            if scores == '':
                response = "No one has answered any questions correctly yet."
            else:
                response = "Here are the current scores:\n" + scores

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
                           output['channel'], output['user']
        return None, None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose

    bot = QuizBot()

    if bot.slack_client.rtm_connect():
        print("QuizBot connected and running!")
        while True:
            command, channel, user = bot.parse_slack_output(bot.slack_client.rtm_read())
            if command and channel and user:
                bot.handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
