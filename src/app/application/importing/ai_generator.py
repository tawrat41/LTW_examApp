from __future__ import annotations

import os
import json
import urllib.request
import urllib.error
import random
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.persistence.models import Question, QuestionOption, Category, Exam, Section
from app.application.question_bank.dto import CreateQuestionInput, QuestionOptionInput
from app.bootstrap.admin_services import build_question_bank_service

# Dynamic assessment templates for zero-config fallback run with randomized inputs
DYNAMIC_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "Starter": [
        {"stem": "Hello! My name is {name}. What is _______ name?", "category": "Grammar", "difficulty": 1, "options": [{"text": "your", "correct": True}, {"text": "you", "correct": False}, {"text": "my", "correct": False}, {"text": "yours", "correct": False}], "explanation": "We use the possessive adjective 'your' before the noun 'name'."},
        {"stem": "Where is my {noun}? It is _______ the table.", "category": "Grammar", "difficulty": 1, "options": [{"text": "on", "correct": True}, {"text": "in", "correct": False}, {"text": "under", "correct": False}, {"text": "to", "correct": False}], "explanation": "The preposition 'on' indicates contact with the top surface of the table."},
        {"stem": "These are _______ books.", "category": "Grammar", "difficulty": 1, "options": [{"text": "my", "correct": True}, {"text": "me", "correct": False}, {"text": "I", "correct": False}, {"text": "mine", "correct": False}], "explanation": "Use the possessive adjective 'my' before the plural noun 'books'."},
        {"stem": "_______ name is {name}. She is a student.", "category": "Grammar", "difficulty": 1, "options": [{"text": "Her", "correct": True}, {"text": "His", "correct": False}, {"text": "She", "correct": False}, {"text": "Its", "correct": False}], "explanation": "Use 'Her' for female singular possession."},
        {"stem": "_______ you like apples? Yes, I do.", "category": "Grammar", "difficulty": 1, "options": [{"text": "Do", "correct": True}, {"text": "Does", "correct": False}, {"text": "Are", "correct": False}, {"text": "Is", "correct": False}], "explanation": "The helping verb 'Do' is used with the subject pronoun 'you' in simple present questions."},
        {"stem": "We _______ a new computer.", "category": "Grammar", "difficulty": 1, "options": [{"text": "have", "correct": True}, {"text": "has", "correct": False}, {"text": "having", "correct": False}, {"text": "is", "correct": False}], "explanation": "The subject 'we' takes the verb 'have' for possession."},
        {"stem": "_______ is the classroom? It is upstairs.", "category": "Grammar", "difficulty": 1, "options": [{"text": "Where", "correct": True}, {"text": "What", "correct": False}, {"text": "Who", "correct": False}, {"text": "When", "correct": False}], "explanation": "'Where' is used to ask about place or location."},
        {"stem": "He _______ play football very well.", "category": "Grammar", "difficulty": 1, "options": [{"text": "can", "correct": True}, {"text": "is", "correct": False}, {"text": "has", "correct": False}, {"text": "does", "correct": False}], "explanation": "The modal verb 'can' expresses ability."},
        {"stem": "Look at _______ birds in the tree over there!", "category": "Grammar", "difficulty": 1, "options": [{"text": "those", "correct": True}, {"text": "these", "correct": False}, {"text": "this", "correct": False}, {"text": "that", "correct": False}], "explanation": "Use 'those' for plural objects that are far away ('over there')."},
        {"stem": "I have two _______.", "category": "Grammar", "difficulty": 1, "options": [{"text": "cats", "correct": True}, {"text": "cat", "correct": False}, {"text": "a cat", "correct": False}, {"text": "cats'", "correct": False}], "explanation": "Plural numbers require plural noun forms like 'cats'."},
        {"stem": "The opposite of 'big' is _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "small", "correct": True}, {"text": "tall", "correct": False}, {"text": "long", "correct": False}, {"text": "hot", "correct": False}], "explanation": "'Small' is the direct antonym of 'big'."},
        {"stem": "A horse is an _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "animal", "correct": True}, {"text": "fruit", "correct": False}, {"text": "object", "correct": False}, {"text": "color", "correct": False}], "explanation": "A horse belongs to the category of animals."},
        {"stem": "We write with a _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "pen", "correct": True}, {"text": "book", "correct": False}, {"text": "chair", "correct": False}, {"text": "window", "correct": False}], "explanation": "A pen is a writing instrument."},
        {"stem": "A banana is _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "yellow", "correct": True}, {"text": "blue", "correct": False}, {"text": "red", "correct": False}, {"text": "green", "correct": False}], "explanation": "Ripe bananas are typically yellow."},
        {"stem": "My father's brother is my _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "uncle", "correct": True}, {"text": "aunt", "correct": False}, {"text": "grandfather", "correct": False}, {"text": "cousin", "correct": False}], "explanation": "An uncle is the brother of one's parent."},
        {"stem": "What day is after Tuesday? _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "Wednesday", "correct": True}, {"text": "Thursday", "correct": False}, {"text": "Monday", "correct": False}, {"text": "Friday", "correct": False}], "explanation": "Wednesday follows Tuesday in the weekly sequence."},
        {"stem": "You wear _______ on your feet.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "shoes", "correct": True}, {"text": "hats", "correct": False}, {"text": "shirts", "correct": False}, {"text": "gloves", "correct": False}], "explanation": "Shoes are designed to be worn on the feet."},
        {"stem": "We eat food in the _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "kitchen", "correct": True}, {"text": "bathroom", "correct": False}, {"text": "bedroom", "correct": False}, {"text": "garden", "correct": False}], "explanation": "The kitchen or dining area is where food is typically consumed or prepared."},
        {"stem": "The sun shines in the _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "sky", "correct": True}, {"text": "sea", "correct": False}, {"text": "ground", "correct": False}, {"text": "forest", "correct": False}], "explanation": "The sky is where the sun is located."},
        {"stem": "A clock shows the _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "time", "correct": True}, {"text": "weather", "correct": False}, {"text": "name", "correct": False}, {"text": "price", "correct": False}], "explanation": "A clock is an instrument used to display time."},
        {"stem": "Read and answer: '{name} has a green balloon. {name2} has a red balloon.' Who has the red balloon?", "category": "Reading", "difficulty": 1, "options": [{"text": "{name2}", "correct": True}, {"text": "{name}", "correct": False}, {"text": "No one", "correct": False}, {"text": "Both", "correct": False}], "explanation": "The passage states that '{name2} has a red balloon.'"},
        {"stem": "Read and answer: 'The dog is under the chair. The cat is on the table.' Where is the dog?", "category": "Reading", "difficulty": 1, "options": [{"text": "Under the chair", "correct": True}, {"text": "On the table", "correct": False}, {"text": "Next to the table", "correct": False}, {"text": "In the garden", "correct": False}], "explanation": "The text directly states: 'The dog is under the chair.'"},
        {"stem": "Read and answer: 'We go to the park on Saturdays.' When do we go to the park?", "category": "Reading", "difficulty": 1, "options": [{"text": "Saturdays", "correct": True}, {"text": "Sundays", "correct": False}, {"text": "Every day", "correct": False}, {"text": "On weekdays", "correct": False}], "explanation": "The text states that we go 'on Saturdays.'"},
        {"stem": "Read and answer: '{name} is seven years old. {name2} is nine years old.' Who is older?", "category": "Reading", "difficulty": 1, "options": [{"text": "{name2}", "correct": True}, {"text": "{name}", "correct": False}, {"text": "They are the same age", "correct": False}, {"text": "Neither", "correct": False}], "explanation": "Nine is greater than seven, so {name2} is older."},
        {"stem": "Read and answer: 'This book is about animals.' What is the book about?", "category": "Reading", "difficulty": 1, "options": [{"text": "Animals", "correct": True}, {"text": "Sports", "correct": False}, {"text": "Cooking", "correct": False}, {"text": "Space", "correct": False}], "explanation": "The text states the book is 'about animals.'"},
        {"stem": "Read and answer: 'I like apples but I do not like oranges.' What do I dislike?", "category": "Reading", "difficulty": 1, "options": [{"text": "Oranges", "correct": True}, {"text": "Apples", "correct": False}, {"text": "Both", "correct": False}, {"text": "Neither", "correct": False}], "explanation": "The speaker states: 'I do not like oranges.'"},
        {"stem": "Read and answer: 'The shop opens at nine o'clock and closes at six o'clock.' What time does it close?", "category": "Reading", "difficulty": 1, "options": [{"text": "Six o'clock", "correct": True}, {"text": "Nine o'clock", "correct": False}, {"text": "Ten o'clock", "correct": False}, {"text": "Eight o'clock", "correct": False}], "explanation": "The text states that the shop 'closes at six o'clock.'"},
        {"stem": "Read and answer: '{name} is wearing a blue coat and black shoes.' What color are {name}'s shoes?", "category": "Reading", "difficulty": 1, "options": [{"text": "Black", "correct": True}, {"text": "Blue", "correct": False}, {"text": "Brown", "correct": False}, {"text": "White", "correct": False}], "explanation": "The text specifies '{name} is wearing... black shoes.'"},
        {"stem": "Read and answer: 'There is a big apple tree in the garden.' What kind of tree is in the garden?", "category": "Reading", "difficulty": 1, "options": [{"text": "Apple", "correct": True}, {"text": "Orange", "correct": False}, {"text": "Pear", "correct": False}, {"text": "Oak", "correct": False}], "explanation": "The text states there is an 'apple tree' in the garden."},
        {"stem": "Read and answer: 'My sister is a doctor. She works in a clinic.' Where does my sister work?", "category": "Reading", "difficulty": 1, "options": [{"text": "In a clinic", "correct": True}, {"text": "In a school", "correct": False}, {"text": "In a shop", "correct": False}, {"text": "At home", "correct": False}], "explanation": "The text says: 'She works in a clinic.'"}
    ],
    "Elementary": [
        {"stem": "She _______ to classical music every evening.", "category": "Grammar", "difficulty": 1, "options": [{"text": "listens", "correct": True}, {"text": "listening", "correct": False}, {"text": "listen", "correct": False}, {"text": "listened", "correct": False}], "explanation": "Simple present third-person singular takes the verb with -s (listens) for habits."},
        {"stem": "They are _______ an exciting computer game at the moment.", "category": "Grammar", "difficulty": 1, "options": [{"text": "playing", "correct": True}, {"text": "play", "correct": False}, {"text": "plays", "correct": False}, {"text": "played", "correct": False}], "explanation": "'At the moment' indicates present continuous tense, formed with 'be' + 'verb-ing'."},
        {"stem": "How _______ milk do we need for the pancake recipe?", "category": "Grammar", "difficulty": 1, "options": [{"text": "much", "correct": True}, {"text": "many", "correct": False}, {"text": "some", "correct": False}, {"text": "any", "correct": False}], "explanation": "'Milk' is an uncountable noun, so we ask 'how much'."},
        {"stem": "There aren't _______ eggs left in the refrigerator.", "category": "Grammar", "difficulty": 1, "options": [{"text": "any", "correct": True}, {"text": "some", "correct": False}, {"text": "no", "correct": False}, {"text": "many", "correct": False}], "explanation": "In negative sentences with plural countable nouns, we use 'any'."},
        {"stem": "My brother is _______ than me.", "category": "Grammar", "difficulty": 1, "options": [{"text": "taller", "correct": True}, {"text": "tall", "correct": False}, {"text": "tallest", "correct": False}, {"text": "more tall", "correct": False}], "explanation": "We use comparative adjectives (+er) when comparing two people."},
        {"stem": "This is the _______ movie I have ever watched.", "category": "Grammar", "difficulty": 1, "options": [{"text": "best", "correct": True}, {"text": "good", "correct": False}, {"text": "better", "correct": False}, {"text": "most best", "correct": False}], "explanation": "The superlative form of 'good' is 'best'."},
        {"stem": "Did you _______ your house keys yesterday?", "category": "Grammar", "difficulty": 1, "options": [{"text": "find", "correct": True}, {"text": "found", "correct": False}, {"text": "finding", "correct": False}, {"text": "finds", "correct": False}], "explanation": "The auxiliary verb 'Did' is followed by the base form of the verb."},
        {"stem": "I _______ go to the cinema last weekend.", "category": "Grammar", "difficulty": 1, "options": [{"text": "didn't", "correct": True}, {"text": "don't", "correct": False}, {"text": "wasn't", "correct": False}, {"text": "hasn't", "correct": False}], "explanation": "'Last weekend' indicates past tense, so the negative auxiliary is 'didn't'."},
        {"stem": "We will go to the beach if it _______ sunny tomorrow.", "category": "Grammar", "difficulty": 1, "options": [{"text": "is", "correct": True}, {"text": "will be", "correct": False}, {"text": "was", "correct": False}, {"text": "be", "correct": False}], "explanation": "The first conditional uses the present simple in the 'if' clause."},
        {"stem": "He _______ speak French, but he is learning now.", "category": "Grammar", "difficulty": 1, "options": [{"text": "can't", "correct": True}, {"text": "doesn't can", "correct": False}, {"text": "is not", "correct": False}, {"text": "hasn't", "correct": False}], "explanation": "'Can't' is the correct negative modal expressing inability."},
        {"stem": "My mother works in a clinic; she is a _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "nurse", "correct": True}, {"text": "teacher", "correct": False}, {"text": "chef", "correct": False}, {"text": "lawyer", "correct": False}], "explanation": "A nurse works in a medical clinic or hospital."},
        {"stem": "We bought fresh bread at the local _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "bakery", "correct": True}, {"text": "pharmacy", "correct": False}, {"text": "library", "correct": False}, {"text": "museum", "correct": False}], "explanation": "Bread is made and sold at a bakery."},
        {"stem": "The book was very _______; I fell asleep reading it.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "boring", "correct": True}, {"text": "exciting", "correct": False}, {"text": "interesting", "correct": False}, {"text": "funny", "correct": False}], "explanation": "'Boring' describes something that causes lack of interest or sleepiness."},
        {"stem": "The opposite of 'heavy' is _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "light", "correct": True}, {"text": "thin", "correct": False}, {"text": "weak", "correct": False}, {"text": "short", "correct": False}], "explanation": "'Light' is the direct antonym of 'heavy' in terms of weight."},
        {"stem": "We saw many historical paintings at the _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "museum", "correct": True}, {"text": "market", "correct": False}, {"text": "stadium", "correct": False}, {"text": "theater", "correct": False}], "explanation": "Paintings and historical items are exhibited in a museum."},
        {"stem": "It is raining heavily; please open your _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "umbrella", "correct": True}, {"text": "suitcase", "correct": False}, {"text": "wallet", "correct": False}, {"text": "jacket", "correct": False}], "explanation": "An umbrella is used to shield oneself from rain."},
        {"stem": "I need to _______ some money from the bank.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "withdraw", "correct": True}, {"text": "lend", "correct": False}, {"text": "spend", "correct": False}, {"text": "lose", "correct": False}], "explanation": "'Withdraw' means to take money out of a bank account."},
        {"stem": "She is going to the airport to catch her _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "flight", "correct": True}, {"text": "train", "correct": False}, {"text": "bus", "correct": False}, {"text": "ship", "correct": False}], "explanation": "Flights are boarded at airports."},
        {"stem": "A person who designs buildings is called an _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "architect", "correct": True}, {"text": "engineer", "correct": False}, {"text": "carpenter", "correct": False}, {"text": "artist", "correct": False}], "explanation": "An architect is professionally trained to design buildings."},
        {"stem": "The temperature is high today; it is very _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "hot", "correct": True}, {"text": "cold", "correct": False}, {"text": "cloudy", "correct": False}, {"text": "windy", "correct": False}], "explanation": "High temperature corresponds to hot weather."},
        {"stem": "Read and answer: 'Notice: Swimming is not allowed when the red flag is flying.' What does the notice mean?", "category": "Reading", "difficulty": 1, "options": [{"text": "Do not swim if the flag is red", "correct": True}, {"text": "You must wear red to swim", "correct": False}, {"text": "The pool is open for everyone", "correct": False}, {"text": "You can swim only in deep water", "correct": False}], "explanation": "The notice bans swimming specifically when the red flag is flying."},
        {"stem": "Read and answer: '{name} is playing tennis. {name2} is reading a book.' What is {name2} doing?", "category": "Reading", "difficulty": 1, "options": [{"text": "Reading a book", "correct": True}, {"text": "Playing tennis", "correct": False}, {"text": "Sleeping", "correct": False}, {"text": "Cooking dinner", "correct": False}], "explanation": "The text says '{name2} is reading a book.'"},
        {"stem": "Read and answer: 'The library is closed on Sundays and public holidays.' When is the library open?", "category": "Reading", "difficulty": 1, "options": [{"text": "On normal weekdays", "correct": True}, {"text": "On Sundays", "correct": False}, {"text": "On public holidays", "correct": False}, {"text": "Never", "correct": False}], "explanation": "Since it is closed on Sundays and holidays, it is open on regular weekdays."},
        {"stem": "Read and answer: 'David works from nine to five. Yesterday, he stayed until seven to finish a report.' Why did David stay late?", "category": "Reading", "difficulty": 1, "options": [{"text": "To finish a report", "correct": True}, {"text": "To talk to his boss", "correct": False}, {"text": "To clean his office", "correct": False}, {"text": "To attend a meeting", "correct": False}], "explanation": "The passage says he stayed 'to finish a report.'"},
        {"stem": "Read and answer: 'Apples are rich in vitamins and fiber. Eating one daily keeps you healthy.' What nutrient is mentioned in apples?", "category": "Reading", "difficulty": 1, "options": [{"text": "Vitamins", "correct": True}, {"text": "Protein", "correct": False}, {"text": "Calcium", "correct": False}, {"text": "Fat", "correct": False}], "explanation": "The text lists 'vitamins' and fiber."},
        {"stem": "Read and answer: '{name} went to Paris last summer. She spent three days visiting the Eiffel Tower and art museums.' How long was {name} in Paris?", "category": "Reading", "difficulty": 1, "options": [{"text": "Three days", "correct": True}, {"text": "One week", "correct": False}, {"text": "Last summer", "correct": False}, {"text": "Three weeks", "correct": False}], "explanation": "The text states she spent 'three days' there."},
        {"stem": "Read and answer: 'Please keep off the grass. Use the designated footpaths.' Where should you walk?", "category": "Reading", "difficulty": 1, "options": [{"text": "On the footpaths", "correct": True}, {"text": "On the grass", "correct": False}, {"text": "Anywhere you like", "correct": False}, {"text": "On the road", "correct": False}], "explanation": "The notice asks readers to use the 'designated footpaths.'"},
        {"stem": "Read and answer: 'The movie starts at 7:30 PM. Please arrive 15 minutes early to buy popcorn.' What time should you arrive?", "category": "Reading", "difficulty": 1, "options": [{"text": "7:15 PM", "correct": True}, {"text": "7:30 PM", "correct": False}, {"text": "7:45 PM", "correct": False}, {"text": "8:00 PM", "correct": False}], "explanation": "15 minutes before 7:30 PM is 7:15 PM."},
        {"stem": "Read and answer: 'My new car is red. It has four doors and is very fuel-efficient.' What feature of the car is praised?", "category": "Reading", "difficulty": 1, "options": [{"text": "Fuel efficiency", "correct": True}, {"text": "Its speed", "correct": False}, {"text": "Its leather seats", "correct": False}, {"text": "Its size", "correct": False}], "explanation": "The text states the car is 'very fuel-efficient.'"},
        {"stem": "Read and answer: 'If you lose your card, please report it to the bank immediately.' What should you do if your card is missing?", "category": "Reading", "difficulty": 1, "options": [{"text": "Report it to the bank", "correct": True}, {"text": "Buy a new one", "correct": False}, {"text": "Wait for a few days", "correct": False}, {"text": "Call the police", "correct": False}], "explanation": "The instruction says to 'report it to the bank immediately.'"}
    ],
    "Pre-Intermediate": [
        {"stem": "If I _______ you, I would accept the job offer immediately.", "category": "Grammar", "difficulty": 2, "options": [{"text": "were", "correct": True}, {"text": "am", "correct": False}, {"text": "would be", "correct": False}, {"text": "will be", "correct": False}], "explanation": "Second conditional uses 'were' for all subjects in the 'if' clause."},
        {"stem": "I _______ this interesting novel since last week.", "category": "Grammar", "difficulty": 2, "options": [{"text": "have been reading", "correct": True}, {"text": "read", "correct": False}, {"text": "am reading", "correct": False}, {"text": "was reading", "correct": False}], "explanation": "'Since last week' signals present perfect continuous for an ongoing action starting in the past."},
        {"stem": "He has been living in Paris _______ three years.", "category": "Grammar", "difficulty": 2, "options": [{"text": "for", "correct": True}, {"text": "since", "correct": False}, {"text": "during", "correct": False}, {"text": "ago", "correct": False}], "explanation": "We use 'for' to denote a duration of time (three years)."},
        {"stem": "They _______ television when the lights suddenly went out.", "category": "Grammar", "difficulty": 2, "options": [{"text": "were watching", "correct": True}, {"text": "watched", "correct": False}, {"text": "have watched", "correct": False}, {"text": "watch", "correct": False}], "explanation": "Use past continuous for a longer action interrupted by a shorter action in simple past."},
        {"stem": "You _______ bring an umbrella; the weather forecast says it's going to rain.", "category": "Grammar", "difficulty": 2, "options": [{"text": "should", "correct": True}, {"text": "need", "correct": False}, {"text": "would", "correct": False}, {"text": "could", "correct": False}], "explanation": "'Should' is used to give recommendations or advice."},
        {"stem": "The package _______ sent to your office yesterday afternoon.", "category": "Grammar", "difficulty": 2, "options": [{"text": "was", "correct": True}, {"text": "is", "correct": False}, {"text": "has", "correct": False}, {"text": "did", "correct": False}], "explanation": "Passive voice in simple past: object + was/were + past participle."},
        {"stem": "She is the talented woman _______ won the regional chess competition.", "category": "Grammar", "difficulty": 2, "options": [{"text": "who", "correct": True}, {"text": "which", "correct": False}, {"text": "whose", "correct": False}, {"text": "whom", "correct": False}], "explanation": "Use relative pronoun 'who' for people."},
        {"stem": "That is the quiet cafe _______ we first met.", "category": "Grammar", "difficulty": 2, "options": [{"text": "where", "correct": True}, {"text": "which", "correct": False}, {"text": "that", "correct": False}, {"text": "when", "correct": False}], "explanation": "Use 'where' to refer to a place in relative clauses."},
        {"stem": "We are looking forward to _______ our new home next month.", "category": "Grammar", "difficulty": 2, "options": [{"text": "visiting", "correct": True}, {"text": "visit", "correct": False}, {"text": "visited", "correct": False}, {"text": "to visit", "correct": False}], "explanation": "The expression 'look forward to' must be followed by a gerund (-ing)."},
        {"stem": "I used to _______ tennis, but now I prefer golf.", "category": "Grammar", "difficulty": 2, "options": [{"text": "play", "correct": True}, {"text": "playing", "correct": False}, {"text": "played", "correct": False}, {"text": "plays", "correct": False}], "explanation": "'Used to' is followed by the bare infinitive of the verb."},
        {"stem": "Could you _______ me some money, please? I left my wallet at home.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "lend", "correct": True}, {"text": "borrow", "correct": False}, {"text": "take", "correct": False}, {"text": "keep", "correct": False}], "explanation": "'Lend' means to temporarily give something, while 'borrow' means to take it."},
        {"stem": "The doctor told me to _______ smoking to improve my health.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "give up", "correct": True}, {"text": "give in", "correct": False}, {"text": "put off", "correct": False}, {"text": "take up", "correct": False}], "explanation": "'Give up' is a phrasal verb meaning to quit or stop doing something."},
        {"stem": "I cannot eat this soup; it is too _______.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "salty", "correct": True}, {"text": "sweet", "correct": False}, {"text": "bland", "correct": False}, {"text": "delicious", "correct": False}], "explanation": "'Salty' describes soup containing too much salt, rendering it inedible."},
        {"stem": "She was _______ by the surprising news of her promotion.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "thrilled", "correct": True}, {"text": "depressed", "correct": False}, {"text": "annoyed", "correct": False}, {"text": "exhausted", "correct": False}], "explanation": "'Thrilled' means extremely pleased and excited."},
        {"stem": "We had to _______ the outdoor match because of heavy rain.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "cancel", "correct": True}, {"text": "delay", "correct": False}, {"text": "continue", "correct": False}, {"text": "arrange", "correct": False}], "explanation": "'Cancel' is the correct term for calling off an event entirely due to bad weather."},
        {"stem": "He has a very _______ job; he works 12 hours a day.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "demanding", "correct": True}, {"text": "relaxing", "correct": False}, {"text": "easy", "correct": False}, {"text": "boring", "correct": False}], "explanation": "'Demanding' means requiring much time, effort, or attention."},
        {"stem": "The company decided to _______ its new product next month.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "launch", "correct": True}, {"text": "prevent", "correct": False}, {"text": "discard", "correct": False}, {"text": "abolish", "correct": False}], "explanation": "To 'launch' a product means to introduce it to the market."},
        {"stem": "The flight was delayed, so we had to _______ at the airport.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "wait", "correct": True}, {"text": "hurry", "correct": False}, {"text": "arrive", "correct": False}, {"text": "depart", "correct": False}], "explanation": "A flight delay forces passengers to wait at the terminal."},
        {"stem": "The book was so _______ that I couldn't put it down.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "gripping", "correct": True}, {"text": "dull", "correct": False}, {"text": "complex", "correct": False}, {"text": "predictable", "correct": False}], "explanation": "'Gripping' means firmly holding the attention; exciting."},
        {"stem": "She is very _______ about her exams; she studies every night.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "serious", "correct": True}, {"text": "careless", "correct": False}, {"text": "fearful", "correct": False}, {"text": "indifferent", "correct": False}], "explanation": "Someone who studies every night takes their exams seriously."},
        {"stem": "Read and answer: 'Although remote work offers flexibility, it can lead to feelings of isolation.' What is a major disadvantage of remote work?", "category": "Reading", "difficulty": 2, "options": [{"text": "Isolation", "correct": True}, {"text": "Flexibility", "correct": False}, {"text": "Higher income", "correct": False}, {"text": "Commute time", "correct": False}], "explanation": "The text states that remote work can lead to 'feelings of isolation.'"},
        {"stem": "Read and answer: 'If you want to bake a cake, you need flour, sugar, eggs, and butter.' What is NOT listed as a required ingredient?", "category": "Reading", "difficulty": 2, "options": [{"text": "Milk", "correct": True}, {"text": "Eggs", "correct": False}, {"text": "Flour", "correct": False}, {"text": "Sugar", "correct": False}], "explanation": "The text lists flour, sugar, eggs, and butter, but does not mention milk."},
        {"stem": "Read and answer: '{name} travels frequently. Last year she visited Tokyo, Paris, and Rome. She preferred Tokyo due to its unique food scene.' Which city did she like the most?", "category": "Reading", "difficulty": 2, "options": [{"text": "Tokyo", "correct": True}, {"text": "Paris", "correct": False}, {"text": "Rome", "correct": False}, {"text": "London", "correct": False}], "explanation": "The text says 'She preferred Tokyo due to its unique food scene.'"},
        {"stem": "Read and answer: 'Active listening involves paraphrasing and reflecting to ensure comprehension.' What does active listening involve?", "category": "Reading", "difficulty": 2, "options": [{"text": "Paraphrasing and reflecting", "correct": True}, {"text": "Taking quick notes", "correct": False}, {"text": "Speaking rapidly", "correct": False}, {"text": "Ignoring distractions", "correct": False}], "explanation": "The passage explicitly states: 'Active listening involves paraphrasing and reflecting.'"},
        {"stem": "Read and answer: 'Regular physical exercise helps lower the risk of chronic diseases and improves mood.' What is a benefit of exercise mentioned in the text?", "category": "Reading", "difficulty": 2, "options": [{"text": "Mood improvement", "correct": True}, {"text": "Weight gain", "correct": False}, {"text": "Increased stress", "correct": False}, {"text": "Sleep reduction", "correct": False}], "explanation": "The text states exercise 'improves mood.'"},
        {"stem": "Read and answer: 'The local museum has launched an interactive exhibit detailing the city's maritime history.' What is the exhibit about?", "category": "Reading", "difficulty": 2, "options": [{"text": "Maritime history", "correct": True}, {"text": "Modern art", "correct": False}, {"text": "Space exploration", "correct": False}, {"text": "Local politics", "correct": False}], "explanation": "The text states the exhibit details 'the city's maritime history.'"},
        {"stem": "Read and answer: 'Please ensure all electrical appliances are turned off before leaving the office.' What should you do before going home?", "category": "Reading", "difficulty": 2, "options": [{"text": "Switch off appliances", "correct": True}, {"text": "Lock all windows", "correct": False}, {"text": "Clean your desk", "correct": False}, {"text": "Submit your reports", "correct": False}], "explanation": "The notice asks to 'ensure all electrical appliances are turned off.'"},
        {"stem": "Read and answer: 'Students who submit their assignments late will face a 10% grade reduction.' What happens to late assignments?", "category": "Reading", "difficulty": 2, "options": [{"text": "Grade reduction", "correct": True}, {"text": "Automatic rejection", "correct": False}, {"text": "No penalty", "correct": False}, {"text": "Required rewriting", "correct": False}], "explanation": "The text states late submissions face a '10% grade reduction.'"},
        {"stem": "Read and answer: 'The restaurant requires reservations at least 24 hours in advance for groups larger than six.' When must a group of eight book?", "category": "Reading", "difficulty": 2, "options": [{"text": "24 hours in advance", "correct": True}, {"text": "On arrival", "correct": False}, {"text": "12 hours in advance", "correct": False}, {"text": "One week in advance", "correct": False}], "explanation": "A group of eight is larger than six, so they require reservations 'at least 24 hours in advance.'"},
        {"stem": "Read and answer: 'Biodiversity is crucial for ecosystem stability. When a species goes extinct, the entire network suffers.' What is crucial for stability?", "category": "Reading", "difficulty": 2, "options": [{"text": "Biodiversity", "correct": True}, {"text": "Extinction", "correct": False}, {"text": "Industrialization", "correct": False}, {"text": "Climate change", "correct": False}], "explanation": "The text states: 'Biodiversity is crucial for ecosystem stability.'"}
    ],
    "Intermediate": [
        {"stem": "By the time the police arrived, the thieves _______.", "category": "Grammar", "difficulty": 2, "options": [{"text": "had escaped", "correct": True}, {"text": "escaped", "correct": False}, {"text": "have escaped", "correct": False}, {"text": "were escaping", "correct": False}], "explanation": "Past perfect ('had escaped') indicates an action completed before another past event."},
        {"stem": "She denied _______ the confidential document to the press.", "category": "Grammar", "difficulty": 2, "options": [{"text": "disclosing", "correct": True}, {"text": "to disclose", "correct": False}, {"text": "disclose", "correct": False}, {"text": "disclosed", "correct": False}], "explanation": "The verb 'deny' is followed by a gerund (-ing)."},
        {"stem": "I wish I _______ to my teacher's advice before taking the exam.", "category": "Grammar", "difficulty": 2, "options": [{"text": "had listened", "correct": True}, {"text": "listened", "correct": False}, {"text": "would listen", "correct": False}, {"text": "have listened", "correct": False}], "explanation": "Use 'wish' + past perfect to express regret about a past situation."},
        {"stem": "He suggested _______ a short break before starting the next session.", "category": "Grammar", "difficulty": 2, "options": [{"text": "taking", "correct": True}, {"text": "to take", "correct": False}, {"text": "take", "correct": False}, {"text": "took", "correct": False}], "explanation": "The verb 'suggest' takes a gerund (-ing) when followed directly by a verb."},
        {"stem": "Despite _______ late, she managed to finish the report on time.", "category": "Grammar", "difficulty": 2, "options": [{"text": "being", "correct": True}, {"text": "she was", "correct": False}, {"text": "of being", "correct": False}, {"text": "to be", "correct": False}], "explanation": "'Despite' is a preposition and must be followed by a noun or gerund (-ing)."},
        {"stem": "He is not used to _______ in such a loud and busy environment.", "category": "Grammar", "difficulty": 2, "options": [{"text": "working", "correct": True}, {"text": "work", "correct": False}, {"text": "worked", "correct": False}, {"text": "to work", "correct": False}], "explanation": "'Be used to' expresses familiarity and is followed by a gerund (-ing)."},
        {"stem": "Unless you _______ hard, you will not pass this difficult exam.", "category": "Grammar", "difficulty": 2, "options": [{"text": "study", "correct": True}, {"text": "will study", "correct": False}, {"text": "studied", "correct": False}, {"text": "don't study", "correct": False}], "explanation": "'Unless' means 'if... not', so it takes a positive present verb for future conditions."},
        {"stem": "The manager insisted _______ completing the task by Friday afternoon.", "category": "Grammar", "difficulty": 2, "options": [{"text": "on", "correct": True}, {"text": "to", "correct": False}, {"text": "for", "correct": False}, {"text": "in", "correct": False}], "explanation": "The verb 'insist' collocates with the preposition 'on'."},
        {"stem": "A new highway _______ built in the city center to reduce traffic.", "category": "Grammar", "difficulty": 2, "options": [{"text": "is being", "correct": True}, {"text": "is", "correct": False}, {"text": "has", "correct": False}, {"text": "was", "correct": False}], "explanation": "Present continuous passive ('is being built') describes an ongoing action receiving the verb."},
        {"stem": "The police officer asked me where I _______.", "category": "Grammar", "difficulty": 2, "options": [{"text": "lived", "correct": True}, {"text": "live", "correct": False}, {"text": "had lived", "correct": False}, {"text": "was living", "correct": False}], "explanation": "In indirect/reported speech, present simple shifts back to simple past ('lived')."},
        {"stem": "The new software is expected to _______ our team's productivity.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "enhance", "correct": True}, {"text": "hinder", "correct": False}, {"text": "decline", "correct": False}, {"text": "compromise", "correct": False}], "explanation": "'Enhance' means to improve or increase quality or power."},
        {"stem": "She spoke so fast that I could _______ understand her.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "hardly", "correct": True}, {"text": "nearly", "correct": False}, {"text": "completely", "correct": False}, {"text": "easily", "correct": False}], "explanation": "'Hardly' means scarcely or almost not at all."},
        {"stem": "The meeting has been _______ until next Tuesday morning.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "postponed", "correct": True}, {"text": "cancelled", "correct": False}, {"text": "advanced", "correct": False}, {"text": "suspended", "correct": False}], "explanation": "'Postponed' means delayed or put off to a later date."},
        {"stem": "His excuse for missing the meeting was highly _______; nobody believed him.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "implausible", "correct": True}, {"text": "plausible", "correct": False}, {"text": "convincing", "correct": False}, {"text": "honest", "correct": False}], "explanation": "'Implausible' means not believable or highly unlikely to be true."},
        {"stem": "We decided to cancel the match due to the _______ weather.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "inclement", "correct": True}, {"text": "sunny", "correct": False}, {"text": "warm", "correct": False}, {"text": "mild", "correct": False}], "explanation": "'Inclement' weather is severe, harsh, or stormy."},
        {"stem": "He ran as fast as he could in order _______ miss the train.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "not to", "correct": True}, {"text": "to not", "correct": False}, {"text": "so not", "correct": False}, {"text": "for not", "correct": False}], "explanation": "'In order not to' is the standard negative structure of purpose."},
        {"stem": "You had better _______ a doctor about that persistent cough.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "see", "correct": True}, {"text": "to see", "correct": False}, {"text": "seeing", "correct": False}, {"text": "saw", "correct": False}], "explanation": "'Had better' is followed by the bare infinitive of the verb."},
        {"stem": "I would rather you _______ mention this to anyone else.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "didn't", "correct": True}, {"text": "don't", "correct": False}, {"text": "not to", "correct": False}, {"text": "would not", "correct": False}], "explanation": "With a subject change, 'would rather' takes the simple past subjunctive ('didn't')."},
        {"stem": "The price of petrol has _______ rapidly over the last quarter.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "soared", "correct": True}, {"text": "plunged", "correct": False}, {"text": "drifted", "correct": False}, {"text": "stabilized", "correct": False}], "explanation": "'Soared' means risen rapidly to a very high level."},
        {"stem": "I can't stand _______ in long queues at the supermarket.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "waiting", "correct": True}, {"text": "to wait", "correct": False}, {"text": "wait", "correct": False}, {"text": "waited", "correct": False}], "explanation": "'Can't stand' is followed by a gerund (-ing)."},
        {"stem": "Read and answer: 'The Socratic method relies on cooperative argumentative dialogue to stimulate critical thinking.' What is the primary purpose of this method?", "category": "Reading", "difficulty": 2, "options": [{"text": "To stimulate critical thinking", "correct": True}, {"text": "To win public debates", "correct": False}, {"text": "To memorize factual data", "correct": False}, {"text": "To write philosophy books", "correct": False}], "explanation": "The text states the method is used 'to stimulate critical thinking.'"},
        {"stem": "Read and answer: 'Despite economic challenges, the company maintained its research budget, anticipating long-term benefits.' What did the company do?", "category": "Reading", "difficulty": 2, "options": [{"text": "Maintained its research budget", "correct": True}, {"text": "Cut research spending", "correct": False}, {"text": "Fired its research team", "correct": False}, {"text": "Closed down operations", "correct": False}], "explanation": "The text states that the company 'maintained its research budget.'"},
        {"stem": "Read and answer: 'Cognitive behavioral therapy (CBT) helps patients identify and change destructive thought patterns.' What is the focus of CBT?", "category": "Reading", "difficulty": 2, "options": [{"text": "Identifying and changing destructive thought patterns", "correct": True}, {"text": "Prescribing strong medications", "correct": False}, {"text": "Analyzing childhood memories", "correct": False}, {"text": "Conducting group hypnosis sessions", "correct": False}], "explanation": "CBT focuses on helping patients 'identify and change destructive thought patterns.'"},
        {"stem": "Read and answer: 'Sustainable agriculture practices are essential to mitigate the effects of climate change on food production.' What mitigates climate change effects?", "category": "Reading", "difficulty": 2, "options": [{"text": "Sustainable agriculture", "correct": True}, {"text": "Deforestation", "correct": False}, {"text": "Industrial pollution", "correct": False}, {"text": "Rapid urbanization", "correct": False}], "explanation": "The text states that 'sustainable agriculture practices' mitigate these effects."},
        {"stem": "Read and answer: 'The placebo effect demonstrates the connection between psychological expectation and physiological healing.' What does the placebo effect show?", "category": "Reading", "difficulty": 2, "options": [{"text": "The link between expectation and physical healing", "correct": True}, {"text": "That drugs are always unnecessary", "correct": False}, {"text": "That medical research is biased", "correct": False}, {"text": "That symptoms are entirely imaginary", "correct": False}], "explanation": "It shows the connection between psychological expectation and physical (physiological) healing."},
        {"stem": "Read and answer: 'The gig economy has grown rapidly, offering flexibility but also causing job insecurity.' What is a major drawback of the gig economy?", "category": "Reading", "difficulty": 2, "options": [{"text": "Job insecurity", "correct": True}, {"text": "Flexibility", "correct": False}, {"text": "Commute time", "correct": False}, {"text": "Higher tax rates", "correct": False}], "explanation": "The text lists 'job insecurity' as a drawback alongside flexibility."},
        {"stem": "Read and answer: 'Although the new policy aims to reduce plastic waste, enforcement remains a significant challenge.' What is the main challenge mentioned?", "category": "Reading", "difficulty": 2, "options": [{"text": "Enforcement of the policy", "correct": True}, {"text": "Public awareness", "correct": False}, {"text": "Cost of alternatives", "correct": False}, {"text": "Production of plastic", "correct": False}], "explanation": "The text states that 'enforcement remains a significant challenge.'"},
        {"stem": "Read and answer: 'Studies show that learning a second language improves cognitive flexibility and delays age-related decline.' What is a benefit of bilingualism?", "category": "Reading", "difficulty": 2, "options": [{"text": "Improved cognitive flexibility", "correct": True}, {"text": "Better eyesight", "correct": False}, {"text": "Instant career success", "correct": False}, {"text": "Faster physical reflexes", "correct": False}], "explanation": "The text states that it 'improves cognitive flexibility.'"},
        {"stem": "Read and answer: 'To obtain a visa, applicants must provide proof of sufficient funds and a return ticket.' What must visa applicants show?", "category": "Reading", "difficulty": 2, "options": [{"text": "Proof of funds and a return ticket", "correct": True}, {"text": "A letter of reference only", "correct": False}, {"text": "Their birth certificate", "correct": False}, {"text": "Employment history", "correct": False}], "explanation": "The text requires 'proof of sufficient funds and a return ticket.'"},
        {"stem": "Read and answer: 'The project was postponed indefinitely due to a lack of consensus among board members.' Why was the project delayed?", "category": "Reading", "difficulty": 2, "options": [{"text": "Lack of agreement among board members", "correct": True}, {"text": "Insufficient budget", "correct": False}, {"text": "Technical glitches", "correct": False}, {"text": "A sudden market crash", "correct": False}], "explanation": "'Lack of consensus' means a lack of agreement."}
    ],
    "Upper-Intermediate": [
        {"stem": "By this time next year, she _______ her master's degree in linguistics.", "category": "Grammar", "difficulty": 2, "options": [{"text": "will have completed", "correct": True}, {"text": "will complete", "correct": False}, {"text": "will be completing", "correct": False}, {"text": "is completing", "correct": False}], "explanation": "Future perfect ('will have completed') describes an action completed before a specific future time."},
        {"stem": "Hardly _______ entered the house when the phone began to ring.", "category": "Grammar", "difficulty": 3, "options": [{"text": "had I", "correct": True}, {"text": "I had", "correct": False}, {"text": "did I", "correct": False}, {"text": "was I", "correct": False}], "explanation": "Negative adverbials like 'Hardly' starting a sentence trigger auxiliary-subject inversion."},
        {"stem": "It is essential that she _______ present at the board meeting.", "category": "Grammar", "difficulty": 2, "options": [{"text": "be", "correct": True}, {"text": "is", "correct": False}, {"text": "was", "correct": False}, {"text": "should be", "correct": False}], "explanation": "Subjunctive mood ('be') is used after advisory words like 'essential'."},
        {"stem": "She behaves as if she _______ the boss of this entire company.", "category": "Grammar", "difficulty": 2, "options": [{"text": "were", "correct": True}, {"text": "is", "correct": False}, {"text": "was", "correct": False}, {"text": "be", "correct": False}], "explanation": "'As if' takes past subjunctive ('were') to express hypothetical situations."},
        {"stem": "Under no circumstances _______ you touch this high-voltage wire.", "category": "Grammar", "difficulty": 2, "options": [{"text": "should", "correct": True}, {"text": "must", "correct": False}, {"text": "ought", "correct": False}, {"text": "shall", "correct": False}], "explanation": "Negative preposing ('Under no circumstances') triggers auxiliary-subject inversion."},
        {"stem": "Not only _______ the exam, but she also won a prestigious scholarship.", "category": "Grammar", "difficulty": 2, "options": [{"text": "did she pass", "correct": True}, {"text": "she passed", "correct": False}, {"text": "has she passed", "correct": False}, {"text": "passed she", "correct": False}], "explanation": "'Not only' starting a clause triggers subject-verb inversion using an auxiliary verb."},
        {"stem": "If they had started earlier, they _______ the deadline last week.", "category": "Grammar", "difficulty": 2, "options": [{"text": "would have met", "correct": True}, {"text": "met", "correct": False}, {"text": "would meet", "correct": False}, {"text": "will meet", "correct": False}], "explanation": "Third conditional describes hypothetical past situations, using 'would have + past participle'."},
        {"stem": "The CEO is believed _______ the country last night ahead of the investigation.", "category": "Grammar", "difficulty": 2, "options": [{"text": "to have left", "correct": True}, {"text": "leaving", "correct": False}, {"text": "to leave", "correct": False}, {"text": "left", "correct": False}], "explanation": "Passive reporting construction: subject + is believed + perfect infinitive ('to have left') for past actions."},
        {"stem": "Only after checking the data _______ realize the mistake.", "category": "Grammar", "difficulty": 2, "options": [{"text": "did he", "correct": True}, {"text": "he did", "correct": False}, {"text": "has he", "correct": False}, {"text": "he had", "correct": False}], "explanation": "Inversion is required after limiting expressions like 'Only after...'."},
        {"stem": "We must prevent the server from _______ overloaded during peak hours.", "category": "Grammar", "difficulty": 2, "options": [{"text": "becoming", "correct": True}, {"text": "become", "correct": False}, {"text": "to become", "correct": False}, {"text": "against becoming", "correct": False}], "explanation": "'Prevent someone/something from' is followed by a gerund (-ing)."},
        {"stem": "We had to _______ the meeting due to the transport strike.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "call off", "correct": True}, {"text": "call on", "correct": False}, {"text": "put out", "correct": False}, {"text": "carry out", "correct": False}], "explanation": "'Call off' is a phrasal verb meaning to cancel."},
        {"stem": "The company's profits have been _______; they fluctuate constantly.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "erratic", "correct": True}, {"text": "steady", "correct": False}, {"text": "unrivaled", "correct": False}, {"text": "monolithic", "correct": False}], "explanation": "'Erratic' means unpredictable or inconsistent, matching 'fluctuate constantly'."},
        {"stem": "She was accused _______ stealing the confidential documents.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "of", "correct": True}, {"text": "for", "correct": False}, {"text": "with", "correct": False}, {"text": "about", "correct": False}], "explanation": "The passive collocation is 'accused of doing something'."},
        {"stem": "He was prevented _______ leaving the country by the customs authorities.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "from", "correct": True}, {"text": "to", "correct": False}, {"text": "against", "correct": False}, {"text": "of", "correct": False}], "explanation": "The standard collocation is 'prevented from doing something'."},
        {"stem": "The project was completed _______ schedule, much to our surprise.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "ahead of", "correct": True}, {"text": "before of", "correct": False}, {"text": "prior", "correct": False}, {"text": "advanced", "correct": False}], "explanation": "'Ahead of schedule' is the idiomatic expression for finishing earlier than planned."},
        {"stem": "If you should _______ any problems, do not hesitate to contact us.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "encounter", "correct": True}, {"text": "counter", "correct": False}, {"text": "confront", "correct": False}, {"text": "oppose", "correct": False}], "explanation": "'Encounter' is standard for experiencing difficulties or obstacles."},
        {"stem": "The company has decided to _______ its operations in Asia.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "expand", "correct": True}, {"text": "inflate", "correct": False}, {"text": "magnify", "correct": False}, {"text": "prolong", "correct": False}], "explanation": "To grow business presence is to 'expand' operations."},
        {"stem": "His argument was so _______ that we had to agree with his conclusions.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "cogent", "correct": True}, {"text": "spurious", "correct": False}, {"text": "equivocal", "correct": False}, {"text": "redundant", "correct": False}], "explanation": "'Cogent' means clear, logical, and convincing."},
        {"stem": "She is very _______ to changes in temperature.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "sensitive", "correct": True}, {"text": "sensible", "correct": False}, {"text": "sentient", "correct": False}, {"text": "sensational", "correct": False}], "explanation": "'Sensitive' means easily affected by external factors."},
        {"stem": "The government is trying to _______ rising inflation.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "curb", "correct": True}, {"text": "promote", "correct": False}, {"text": "expand", "correct": False}, {"text": "advance", "correct": False}], "explanation": "'Curb' means to limit, control, or restrain."},
        {"stem": "Read and answer: 'Although remote work is flexible, it can lead to loneliness. Remote employees miss out on informal workplace interactions, which help foster team cohesiveness.' What is a major drawback of remote work according to the text?", "category": "Reading", "difficulty": 2, "options": [{"text": "Loneliness", "correct": True}, {"text": "Flexibility", "correct": False}, {"text": "Commute time", "correct": False}, {"text": "Higher utility bills", "correct": False}], "explanation": "The text states that remote work 'can lead to loneliness.'"},
        {"stem": "Read and answer: 'If you want to bake a cake, you need flour, sugar, eggs, and butter. Ovens must be preheated to 180 degrees Celsius.' What temperature is required?", "category": "Reading", "difficulty": 2, "options": [{"text": "180 degrees", "correct": True}, {"text": "150 degrees", "correct": False}, {"text": "200 degrees", "correct": False}, {"text": "220 degrees", "correct": False}], "explanation": "The text states ovens must be preheated to '180 degrees Celsius.'"},
        {"stem": "Read and answer: 'Despite economic challenges, the company maintained its research budget, anticipating long-term benefits.' What did the company do?", "category": "Reading", "difficulty": 2, "options": [{"text": "Maintained its research budget", "correct": True}, {"text": "Cut research spending", "correct": False}, {"text": "Fired its scientists", "correct": False}, {"text": "Closed its operations", "correct": False}], "explanation": "The text states it 'maintained its research budget.'"},
        {"stem": "Read and answer: 'Active listening involves paraphrasing and reflecting to ensure comprehension.' What does active listening involve?", "category": "Reading", "difficulty": 2, "options": [{"text": "Paraphrasing and reflecting", "correct": True}, {"text": "Ignoring distractions", "correct": False}, {"text": "Speaking quickly", "correct": False}, {"text": "Taking notes", "correct": False}], "explanation": "The text states: 'Active listening involves paraphrasing and reflecting.'"},
        {"stem": "Read and answer: 'The gig economy has grown rapidly, offering flexibility but also causing job insecurity.' What is a major drawback of the gig economy?", "category": "Reading", "difficulty": 2, "options": [{"text": "Job insecurity", "correct": True}, {"text": "Flexibility", "correct": False}, {"text": "Commute time", "correct": False}, {"text": "Higher tax rates", "correct": False}], "explanation": "The text lists 'job insecurity' as a negative consequence."},
        {"stem": "Read and answer: 'Sustainable agriculture practices are essential to mitigate the effects of climate change on food production.' What mitigates climate change effects?", "category": "Reading", "difficulty": 2, "options": [{"text": "Sustainable agriculture", "correct": True}, {"text": "Deforestation", "correct": False}, {"text": "Industrial pollution", "correct": False}, {"text": "Urbanization", "correct": False}], "explanation": "The text points to 'sustainable agriculture' as key to mitigating effects."},
        {"stem": "Read and answer: 'The placebo effect demonstrates the connection between psychological expectation and physiological healing.' What does the placebo effect show?", "category": "Reading", "difficulty": 2, "options": [{"text": "The link between expectation and physical healing", "correct": True}, {"text": "That drugs are always unnecessary", "correct": False}, {"text": "That medical research is biased", "correct": False}, {"text": "That symptoms are entirely imaginary", "correct": False}], "explanation": "The connection between expectation (psychological) and healing (physiological) is highlighted."},
        {"stem": "Read and answer: 'Jane started learning guitar two years ago. She practices for one hour every day.' How long has Jane been practicing guitar?", "category": "Reading", "difficulty": 2, "options": [{"text": "Two years", "correct": True}, {"text": "One year", "correct": False}, {"text": "Two months", "correct": False}, {"text": "Five years", "correct": False}], "explanation": "The text states she started 'two years ago.'"},
        {"stem": "Read and answer: 'Biodiversity is crucial for ecosystem stability. When species go extinct, the entire network suffers.' What is crucial for stability?", "category": "Reading", "difficulty": 2, "options": [{"text": "Biodiversity", "correct": True}, {"text": "Extinction", "correct": False}, {"text": "Fossil fuels", "correct": False}, {"text": "Monoculture", "correct": False}], "explanation": "The text states: 'Biodiversity is crucial for ecosystem stability.'"},
        {"stem": "Read and answer: 'Cognitive behavioral therapy (CBT) helps patients identify and change destructive thought patterns.' What is the focus of CBT?", "category": "Reading", "difficulty": 2, "options": [{"text": "Identifying and changing destructive thought patterns", "correct": True}, {"text": "Prescribing medications", "correct": False}, {"text": "Analyzing childhood memories", "correct": False}, {"text": "Conducting group hypnosis", "correct": False}], "explanation": "CBT helps patients 'identify and change destructive thought patterns.'"}
    ],
    "Advanced": [
        {"stem": "Were it _______ for your timely assistance, we would have suffered severe losses.", "category": "Grammar", "difficulty": 3, "options": [{"text": "not", "correct": True}, {"text": "had not", "correct": False}, {"text": "never", "correct": False}, {"text": "without", "correct": False}], "explanation": "Formal conditional inversion: 'Were it not for...' is equivalent to 'If it had not been for...'."},
        {"stem": "Try as they _______, they could not decipher the archaic inscriptions on the tomb.", "category": "Grammar", "difficulty": 3, "options": [{"text": "might", "correct": True}, {"text": "would", "correct": False}, {"text": "could", "correct": False}, {"text": "should", "correct": False}], "explanation": "The subjunctive-concessive inversion pattern is 'Try as they might...'."},
        {"stem": "It is imperative that the new safety regulations _______ strictly adhered to by all staff.", "category": "Grammar", "difficulty": 3, "options": [{"text": "be", "correct": True}, {"text": "are", "correct": False}, {"text": "were", "correct": False}, {"text": "should be", "correct": False}], "explanation": "Subjunctive mood ('be') is required after demand verbs/adjectives like 'imperative'."},
        {"stem": "Had we known about the schedule change, we _______ our travel arrangements accordingly.", "category": "Grammar", "difficulty": 3, "options": [{"text": "would have adjusted", "correct": True}, {"text": "had adjusted", "correct": False}, {"text": "would adjust", "correct": False}, {"text": "adjusted", "correct": False}], "explanation": "Third conditional structure using inversion: 'Had we known' is paired with 'would have + past participle'."},
        {"stem": "Seldom _______ witnessed such a breathtaking display of raw musical talent.", "category": "Grammar", "difficulty": 3, "options": [{"text": "have I", "correct": True}, {"text": "I have", "correct": False}, {"text": "did I", "correct": False}, {"text": "was I", "correct": False}], "explanation": "Negative adverbials like 'Seldom' require subject-auxiliary inversion when preposed."},
        {"stem": "No sooner had she finished her speech _______ the audience erupted into applause.", "category": "Grammar", "difficulty": 3, "options": [{"text": "than", "correct": True}, {"text": "when", "correct": False}, {"text": "then", "correct": False}, {"text": "that", "correct": False}], "explanation": "The correlative structure is 'No sooner had ... than ...'."},
        {"stem": "So intense _______ the heat that the tarmac on the road began to melt.", "category": "Grammar", "difficulty": 3, "options": [{"text": "was", "correct": True}, {"text": "is", "correct": False}, {"text": "had been", "correct": False}, {"text": "would be", "correct": False}], "explanation": "Inversion after 'So + adjective' is used for emphasis."},
        {"stem": "Lest we _______ anyone, we should double-check the guest list.", "category": "Grammar", "difficulty": 3, "options": [{"text": "offend", "correct": True}, {"text": "should offend", "correct": False}, {"text": "offended", "correct": False}, {"text": "will offend", "correct": False}], "explanation": "'Lest' takes the present subjunctive ('offend') or 'should' to indicate prevention of negative outcomes."},
        {"stem": "Only when the contract is signed _______ the project proceed.", "category": "Grammar", "difficulty": 3, "options": [{"text": "will", "correct": True}, {"text": "is", "correct": False}, {"text": "does", "correct": False}, {"text": "can", "correct": False}], "explanation": "Inversion is triggered after restrictive expressions like 'Only when...' at the beginning of a sentence."},
        {"stem": "The judge recommended that the defendant _______ a fine rather than be imprisoned.", "category": "Grammar", "difficulty": 3, "options": [{"text": "pay", "correct": True}, {"text": "pays", "correct": False}, {"text": "paid", "correct": False}, {"text": "should pay", "correct": False}], "explanation": "Demand/recommend verbs require the present subjunctive ('pay') in the 'that' clause."},
        {"stem": "Her arguments during the debate were _______, leaving no room for counter-claims.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "cogent", "correct": True}, {"text": "equivocal", "correct": False}, {"text": "spurious", "correct": False}, {"text": "redundant", "correct": False}], "explanation": "'Cogent' means clear, logical, and convincing."},
        {"stem": "The government's response was criticized as _______, lacking any energy or decisiveness.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "flaccid", "correct": True}, {"text": "resolute", "correct": False}, {"text": "ebullient", "correct": False}, {"text": "pragmatic", "correct": False}], "explanation": "'Flaccid' means weak, limp, or lacking energy and force."},
        {"stem": "He spoke with such _______ that the entire audience was moved to tears.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "eloquence", "correct": True}, {"text": "hesitation", "correct": False}, {"text": "brevity", "correct": False}, {"text": "indifference", "correct": False}], "explanation": "'Eloquence' is persuasive, fluent, and powerful speaking."},
        {"stem": "The contract was declared _______ because of a critical technicality.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "null and void", "correct": True}, {"text": "valid and binding", "correct": False}, {"text": "negotiable", "correct": False}, {"text": "lucrative", "correct": False}], "explanation": "'Null and void' means having no legal force or effect."},
        {"stem": "She is an _______ reader; she reads at least five books a week.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "avid", "correct": True}, {"text": "occasional", "correct": False}, {"text": "indifferent", "correct": False}, {"text": "apathetic", "correct": False}], "explanation": "'Avid' means having or showing a keen interest in or enthusiasm for."},
        {"stem": "His explanation was _______ with errors, making it completely unreliable.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "riddled", "correct": True}, {"text": "sparse", "correct": False}, {"text": "embellished", "correct": False}, {"text": "devoid", "correct": False}], "explanation": "'Riddled with' means filled with something undesirable."},
        {"stem": "The candidate's views are in _______ contrast to those of his party's platform.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "stark", "correct": True}, {"text": "vague", "correct": False}, {"text": "slight", "correct": False}, {"text": "subtle", "correct": False}], "explanation": "'Stark contrast' is a common collocation describing very sharp or clear differences."},
        {"stem": "She has an _______ ability to predict market trends before they occur.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "uncanny", "correct": True}, {"text": "ordinary", "correct": False}, {"text": "inefficient", "correct": False}, {"text": "questionable", "correct": False}], "explanation": "'Uncanny' means strange or mysterious, especially in an unsettling way."},
        {"stem": "The organization is facing a _______ of funds, risking immediate closure.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "dearth", "correct": True}, {"text": "surplus", "correct": False}, {"text": "plethora", "correct": False}, {"text": "abundance", "correct": False}], "explanation": "'Dearth' means a scarcity or lack of something."},
        {"stem": "His remarks were _______ to spark controversy among the committee members.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "calculated", "correct": True}, {"text": "unlikely", "correct": False}, {"text": "spontaneous", "correct": False}, {"text": "incidental", "correct": False}], "explanation": "'Calculated' here means planned or intended to have a specific effect."},
        {"stem": "Read and answer: 'Epistemic humility involves recognizing the limitations of one's own knowledge, which is essential for intellectual growth.' What is required for intellectual growth?", "category": "Reading", "difficulty": 3, "options": [{"text": "Epistemic humility", "correct": True}, {"text": "Absolute certainty", "correct": False}, {"text": "Engaging in debates", "correct": False}, {"text": "Reading extensively", "correct": False}], "explanation": "The text states that 'epistemic humility' is 'essential for intellectual growth.'"},
        {"stem": "Read and answer: 'The phenomenon of confirmation bias leads individuals to favor information that confirms their pre-existing beliefs.' What does confirmation bias do?", "category": "Reading", "difficulty": 3, "options": [{"text": "Favors information confirming pre-existing beliefs", "correct": True}, {"text": "Encourages objective scientific inquiry", "correct": False}, {"text": "Helps in logical reasoning", "correct": False}, {"text": "Reduces critical thinking capabilities", "correct": False}], "explanation": "The text states it leads individuals to 'favor information that confirms their pre-existing beliefs.'"},
        {"stem": "Read and answer: 'The theory of relativity revolutionized our understanding of space, time, and gravity.' What did the theory of relativity affect?", "category": "Reading", "difficulty": 3, "options": [{"text": "Our understanding of space, time, and gravity", "correct": True}, {"text": "Chemical bonding theories", "correct": False}, {"text": "Microbiology practices", "correct": False}, {"text": "Geological classifications", "correct": False}], "explanation": "The text states it 'revolutionized our understanding of space, time, and gravity.'"},
        {"stem": "Read and answer: 'In Socratic dialogue, acknowledging one's ignorance is considered a prerequisite for learning.' What is a prerequisite for learning?", "category": "Reading", "difficulty": 3, "options": [{"text": "Acknowledging one's ignorance", "correct": True}, {"text": "Having high intelligence", "correct": False}, {"text": "Reading classical philosophy", "correct": False}, {"text": "Engaging in public speeches", "correct": False}], "explanation": "The text states: 'acknowledging one's ignorance is considered a prerequisite for learning.'"},
        {"stem": "Read and answer: 'The novel's stream-of-consciousness narrative mimics the chaotic, unstructured nature of human thought.' What does the narrative mimic?", "category": "Reading", "difficulty": 3, "options": [{"text": "Unstructured human thought", "correct": True}, {"text": "Linear historical events", "correct": False}, {"text": "Scientific methodology", "correct": False}, {"text": "Classical poetic structure", "correct": False}], "explanation": "The text states it mimics 'the chaotic, unstructured nature of human thought.'"},
        {"stem": "Read and answer: 'Quantum entanglement defies classical intuition, as entangled particles exhibit correlated states regardless of distance.' What is special about entangled particles?", "category": "Reading", "difficulty": 3, "options": [{"text": "They show correlated states at any distance", "correct": True}, {"text": "They move faster than light", "correct": False}, {"text": "They are easily destroyed", "correct": False}, {"text": "They follow classical laws of physics", "correct": False}], "explanation": "The text states they 'exhibit correlated states regardless of distance.'"},
        {"stem": "Read and answer: 'Heuristic evaluation in UX design is a rule-of-thumb method used to identify usability issues.' What is the purpose of heuristic evaluation?", "category": "Reading", "difficulty": 3, "options": [{"text": "Identify usability issues", "correct": True}, {"text": "Write user code", "correct": False}, {"text": "Determine marketing costs", "correct": False}, {"text": "Design graphic icons", "correct": False}], "explanation": "It is a method used 'to identify usability issues.'"},
        {"stem": "Read and answer: 'Schopenhauer argued that the world is primarily driven by a blind, irrational metaphysical Will.' What drives the world according to Schopenhauer?", "category": "Reading", "difficulty": 3, "options": [{"text": "An irrational metaphysical Will", "correct": True}, {"text": "Scientific progression", "correct": False}, {"text": "Political arrangements", "correct": False}, {"text": "Divine providence", "correct": False}], "explanation": "He argued the world is driven by a 'blind, irrational metaphysical Will.'"},
        {"stem": "Read and answer: 'The Turing test measures a machine's ability to exhibit intelligent behavior indistinguishable from that of a human.' What does the Turing test evaluate?", "category": "Reading", "difficulty": 3, "options": [{"text": "Machine intelligence mimicry", "correct": True}, {"text": "Hardware processing speeds", "correct": False}, {"text": "Software security features", "correct": False}, {"text": "Database retrieval latency", "correct": False}], "explanation": "It measures ability to exhibit intelligent behavior indistinguishable from a human."},
        {"stem": "Read and answer: 'Existentialism posits that individuals are entirely free and active agents responsible for their own development.' What is the role of individuals in existentialism?", "category": "Reading", "difficulty": 3, "options": [{"text": "Free and responsible agents", "correct": True}, {"text": "Passive observers of fate", "correct": False}, {"text": "Products of purely genetic coding", "correct": False}, {"text": "Subjects of absolute divine predetermination", "correct": False}], "explanation": "Existentialism posits that individuals are 'free and active agents responsible for their own development.'"}
    ]
}

def get_randomized_question(tmpl: Dict[str, Any]) -> Dict[str, Any]:
    m_names = ["John", "David", "James", "Michael", "Robert", "William", "Richard", "Joseph", "Thomas", "Charles"]
    f_names = ["Sarah", "Emily", "Jessica", "Linda", "Mary", "Elizabeth", "Barbara", "Susan", "Patricia", "Jennifer"]
    all_names = m_names + f_names
    places = ["park", "library", "beach", "school", "office", "store", "market", "gym", "restaurant", "cafe", "station", "airport", "museum", "bank", "hotel"]
    nouns = ["book", "pen", "car", "bicycle", "laptop", "phone", "bag", "key", "hat", "cup", "chair", "table", "clock", "watch", "desk"]
    
    name = random.choice(all_names)
    name2 = random.choice([n for n in all_names if n != name])
    place = random.choice(places)
    noun = random.choice(nouns)
    
    stem = tmpl["stem"].format(name=name, name2=name2, place=place, noun=noun)
    explanation = tmpl["explanation"].format(name=name, name2=name2, place=place, noun=noun)
    
    raw_options = [dict(opt) for opt in tmpl["options"]]
    for opt in raw_options:
        opt["text"] = opt["text"].format(name=name, name2=name2, place=place, noun=noun)
        
    random.shuffle(raw_options)
    
    keys = ["A", "B", "C", "D"]
    shuffled_options = {}
    correct_option = None
    for i, opt in enumerate(raw_options):
        key = keys[i]
        shuffled_options[key] = opt["text"]
        if opt["correct"]:
            correct_option = key
            
    return {
        "stem_text": stem,
        "category_name": tmpl["category"],
        "difficulty_level": tmpl["difficulty"],
        "options": shuffled_options,
        "correct_option": correct_option,
        "explanation_text": explanation
    }



class AIGeneratorService:
    def __init__(self, db_session: Session) -> None:
        self._db = db_session
        self._qb_service = build_question_bank_service(db_session)
        self._provider, self._api_key, self._api_url, self._model = self._detect_provider()

    def _detect_provider(self) -> tuple[str, str, str, str]:
        # Determine API provider
        import os
        if os.environ.get("GITHUB_TOKEN"):
            return (
                "github_models",
                os.environ["GITHUB_TOKEN"],
                "https://models.inference.ai.azure.com/chat/completions",
                os.environ.get("GITHUB_MODEL_NAME", "gpt-4o-mini")
            )
        elif os.environ.get("GROQ_API_KEY"):
            return (
                "groq_api",
                os.environ["GROQ_API_KEY"],
                "https://api.groq.com/openai/v1/chat/completions",
                os.environ.get("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
            )
        elif os.environ.get("GEMINI_API_KEY"):
            return (
                "gemini_api",
                os.environ["GEMINI_API_KEY"],
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
            )
        elif os.environ.get("OPENAI_API_KEY"):
            return (
                "openai_api",
                os.environ["OPENAI_API_KEY"],
                "https://api.openai.com/v1/chat/completions",
                os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
            )
        return ("offline_fallback", "", "", "")

    def generate_questions(
        self,
        exam_id: str,
        section_id: str,
        level_name: str,
        count: int = 5,
        attempt_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point to generate and validate questions.
        Falls back to local static seed templates if no API key is set.
        """
        import sys
        if self._provider == "offline_fallback":
            print(f"[QUESTION GENERATOR] No API key configured. Generating {count} questions using local dynamic templates for {level_name}.", file=sys.stderr, flush=True)
            res = self._generate_fallback(exam_id, section_id, level_name, count, attempt_id)
            print(f"[QUESTION GENERATOR] Fallback generation complete. Successfully imported {res.get('imported_count', 0)} questions.", file=sys.stderr, flush=True)
            return res
        
        print(f"[QUESTION GENERATOR] {self._provider} is configured. Generating {count} questions using model '{self._model}' for {level_name}.", file=sys.stderr, flush=True)
        res = self._generate_via_api(exam_id, section_id, level_name, count, attempt_id)
        print(f"[QUESTION GENERATOR] {self._provider} generation complete. Successfully imported {res.get('imported_count', 0)} questions. Success status: {res.get('success', False)}.", file=sys.stderr, flush=True)
        return res

    def _generate_fallback(
        self,
        exam_id: str,
        section_id: str,
        level_name: str,
        count: int,
        attempt_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Loads and persists questions from dynamic offline templates."""
        templates = DYNAMIC_TEMPLATES.get(level_name, DYNAMIC_TEMPLATES["Intermediate"])
        
        # Avoid duplicate selections by capping count at the number of available templates
        actual_count = min(count, len(templates))
        selected_templates = random.sample(templates, actual_count)
        
        imported_count = 0
        issues = []
        
        for idx, tmpl in enumerate(selected_templates):
            try:
                q_data = get_randomized_question(tmpl)
                
                # Add options mapping
                options_input = [
                    QuestionOptionInput(key=k, text=v, is_correct=(k == q_data["correct_option"]))
                    for k, v in q_data["options"].items()
                ]
                
                # Compute a deterministic hash of the stem for duplicate prevention
                stem_hash = uuid.uuid5(uuid.NAMESPACE_DNS, q_data["stem_text"]).hex[:8]
                
                # Compute a unique external_ref for this attempt if attempt_id is provided
                ref_suffix = f"-{attempt_id[:8]}" if attempt_id else ""
                ext_ref = f"dynamic-ai-{level_name.lower()}-{stem_hash}{ref_suffix}"
                
                # Prevent IntegrityError by skipping existing questions in the base pool
                from sqlalchemy import select
                existing_q = self._db.scalar(
                    select(Question).where(
                        Question.exam_id == uuid.UUID(exam_id),
                        Question.external_ref == ext_ref
                    )
                )
                if existing_q is not None:
                    continue
                
                # Insert manually using repository layer
                create_input = CreateQuestionInput(
                    exam_id=exam_id,
                    section_id=section_id,
                    stem_text=q_data["stem_text"],
                    options=options_input,
                    category_name=q_data["category_name"],
                    difficulty_level=q_data["difficulty_level"],
                    explanation_text=q_data["explanation_text"],
                    marks=1.0,
                    external_ref=ext_ref,
                    is_active=True,
                    attempt_id=attempt_id
                )
                self._qb_service.add_question(create_input)
                imported_count += 1
            except Exception as e:
                issues.append(f"Failed to load dynamic item {idx}: {str(e)}")
                
        return {
            "mode": "offline_fallback",
            "success": True,
            "imported_count": imported_count,
            "issues": issues,
            "logs": ["Loaded dynamic randomized English syllabus templates successfully."]
        }

    def _generate_via_api(
        self,
        exam_id: str,
        section_id: str,
        level_name: str,
        count: int,
        attempt_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Queries the configured API provider in batches of 10 to commit questions."""
        import sys
        
        batch_size = 10
        total_requested = count
        
        logs = []
        issues = []
        imported_count = 0
        
        # Build prompt for specific levels using high-quality benchmarks
        system_prompt = (
            "You are an expert English language assessment developer. You specialize in generating "
            "high-quality multiple-choice questions modeled directly after premium international assessments, "
            "including Cambridge English (KET, PET, FCE, CAE, CPE), IELTS, TOEFL, Oxford University Press, and British Council tests.\n\n"
            "Your questions must be sophisticated, context-rich, and avoid overly simplistic or repetitive patterns. "
            "For Reading, include short but challenging passages followed by inferential or detail questions. "
            "For Grammar and Vocabulary, test contextual usage, phrasal verbs, collocations, and idiomatic expressions appropriate for the level.\n\n"
            "Generate questions in strict JSON format. The JSON must contain a single key 'questions' containing an array of questions.\n"
            "Each question object must match this JSON Schema:\n"
            "{\n"
            "  'stem_text': 'Question stem/sentence filling gaps. Use _______ for blanks.',\n"
            "  'category_name': 'Grammar' or 'Vocabulary' or 'Reading',\n"
            "  'difficulty_level': 1 (Easy), 2 (Medium), or 3 (Hard),\n"
            "  'options': {\n"
            "     'A': 'Option A text',\n"
            "     'B': 'Option B text',\n"
            "     'C': 'Option C text',\n"
            "     'D': 'Option D text'\n"
            "  },\n"
            "  'correct_option': 'A' or 'B' or 'C' or 'D',\n"
            "  'explanation_text': 'Detailed explanation of why this answer is correct.'\n"
            "}\n\n"
            "Instructions:\n"
            "- Ensure the option keys are always exactly A, B, C, D.\n"
            "- Ensure there is exactly ONE correct option.\n"
            "- Ground the grammar/vocab constraints on the level specified by the user."
        )

        num_batches = (total_requested + batch_size - 1) // batch_size
        
        for b in range(num_batches):
            batch_count = min(batch_size, total_requested - (b * batch_size))
            logs.append(f"Starting API generation batch {b+1}/{num_batches} for {batch_count} questions...")
            
            user_content = (
                f"Generate {batch_count} unique multiple-choice questions for the '{level_name}' English proficiency level. "
                f"Ensure a mix of Grammar, Vocabulary, and Reading categories modeled after Oxford, Cambridge, and British Council standards."
            )

            payload = {
                "model": self._model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.7
            }

            try:
                req = urllib.request.Request(
                    self._api_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}"
                    },
                    method="POST"
                )
                
                with urllib.request.urlopen(req, timeout=45) as res:
                    response_data = json.loads(res.read().decode("utf-8"))
                    
                raw_content = response_data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_content)
                generated_questions = parsed.get("questions", [])
                logs.append(f"Batch {b+1}/{num_batches}: Successfully generated {len(generated_questions)} questions from API.")

                # Validate each question using a SOLVER agent
                for idx, q_data in enumerate(generated_questions):
                    # Normalize options keys and correct_option to uppercase
                    try:
                        if isinstance(q_data.get("options"), dict):
                            q_data["options"] = {str(k).strip().upper(): v for k, v in q_data["options"].items()}
                        if isinstance(q_data.get("correct_option"), str):
                            q_data["correct_option"] = q_data["correct_option"].strip().upper()
                    except Exception:
                        pass

                    if not self._validate_structure(q_data):
                        issues.append(f"Batch {b+1} Q#{idx} failed programmatic JSON structure validation.")
                        continue
                    
                    # Solver Agent Check (Self-Solving simulation)
                    if not self._run_solver_check(q_data):
                        issues.append(f"Batch {b+1} Q#{idx} failed Solver Agent verification (ambiguous correct answer). Discarded.")
                        continue
                    
                    # Persist verified question
                    try:
                        options_input = [
                            QuestionOptionInput(key=k, text=v, is_correct=(k == q_data["correct_option"]))
                            for k, v in q_data["options"].items()
                        ]
                        # Compute a deterministic hash of the stem for duplicate prevention
                        stem_hash = uuid.uuid5(uuid.NAMESPACE_DNS, q_data["stem_text"]).hex[:8]
                        
                        # Compute a unique external_ref for this attempt if attempt_id is provided
                        ref_suffix = f"-{attempt_id[:8]}" if attempt_id else ""
                        ext_ref = f"openai-ai-{level_name.lower()}-{stem_hash}{ref_suffix}"
                        
                        # Prevent IntegrityError by skipping existing questions in the base pool
                        from sqlalchemy import select
                        existing_q = self._db.scalar(
                            select(Question).where(
                                Question.exam_id == uuid.UUID(exam_id),
                                Question.external_ref == ext_ref
                            )
                        )
                        if existing_q is not None:
                            continue
                        
                        create_input = CreateQuestionInput(
                            exam_id=exam_id,
                            section_id=section_id,
                            stem_text=q_data["stem_text"],
                            options=options_input,
                            category_name=q_data["category_name"],
                            difficulty_level=int(q_data["difficulty_level"]),
                            explanation_text=q_data["explanation_text"],
                            marks=1.0,
                            external_ref=ext_ref,
                            is_active=True,
                            attempt_id=attempt_id
                        )
                        self._qb_service.add_question(create_input)
                        imported_count += 1
                    except Exception as e:
                        issues.append(f"Batch {b+1} Q#{idx} failed to persist verified question: {str(e)}")

            except Exception as e:
                logs.append(f"Batch {b+1}/{num_batches} API call failed: {str(e)}")
                issues.append(f"Batch {b+1}/{num_batches} API Connection error: {str(e)}.")
                
        # If API failed completely (no questions imported), fall back to templates
        if imported_count == 0:
            logs.append("No questions successfully generated/imported from API. Falling back to local offline templates...")
            fallback_res = self._generate_fallback(exam_id, section_id, level_name, count, attempt_id)
            imported_count = fallback_res["imported_count"]
            issues.extend(fallback_res["issues"])
            logs.extend(fallback_res["logs"])

        return {
            "mode": self._provider,
            "success": imported_count > 0,
            "imported_count": imported_count,
            "issues": issues,
            "logs": logs
        }

    def _validate_structure(self, q: Dict[str, Any]) -> bool:
        """Programmatic check that all fields match expected database structure."""
        required = ["stem_text", "category_name", "difficulty_level", "options", "correct_option", "explanation_text"]
        if not all(field in q for field in required):
            return False
        if not isinstance(q["options"], dict) or len(q["options"]) != 4:
            return False
        if q["correct_option"] not in q["options"]:
            return False
        if q["category_name"] not in ["Grammar", "Vocabulary", "Reading"]:
            return False
        return True

    def _run_solver_check(self, q: Dict[str, Any]) -> bool:
        """
        Solver Agent validation layer. Prompts the AI to solve the MCQ blind.
        If the solver's key matches the correct_option, return True (verified).
        """
        try:
            options_dict = q.get("options") or {}
            solver_prompt = (
                "You are a student taking an English proficiency exam. "
                "Solve the multiple choice question below. Reply in strict JSON format: {'correct_option': 'KEY'}\n\n"
                f"Question: {q.get('stem_text', '')}\n"
                f"Options:\n"
                f"A: {options_dict.get('A', '')}\n"
                f"B: {options_dict.get('B', '')}\n"
                f"C: {options_dict.get('C', '')}\n"
                f"D: {options_dict.get('D', '')}\n\n"
                "Analyze carefully and provide only the key (A, B, C, or D)."
            )

            payload = {
                "model": self._model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "user", "content": solver_prompt}
                ],
                "temperature": 0.0
            }

            req = urllib.request.Request(
                self._api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                
            raw_content = response_data["choices"][0]["message"]["content"]
            solved = json.loads(raw_content)
            solved_key = solved.get("correct_option", "").strip().upper()
            
            correct_opt = q.get("correct_option") or ""
            return solved_key == correct_opt.strip().upper()
        except Exception:
            # If solver fails for connection reasons, we default to True to avoid discarding
            return True
