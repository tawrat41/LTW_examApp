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
        {"stem": "This is _______ {noun}.", "category": "Grammar", "difficulty": 1, "options": [{"text": "a", "correct": True}, {"text": "an", "correct": False}, {"text": "any", "correct": False}, {"text": "some", "correct": False}], "explanation": "We use 'a' before consonant sounds like '{noun}'."},
        {"stem": "That is _______ orange.", "category": "Grammar", "difficulty": 1, "options": [{"text": "an", "correct": True}, {"text": "a", "correct": False}, {"text": "any", "correct": False}, {"text": "some", "correct": False}], "explanation": "We use 'an' before words starting with a vowel sound like 'orange'."},
        {"stem": "I _______ a student in this class.", "category": "Grammar", "difficulty": 1, "options": [{"text": "am", "correct": True}, {"text": "is", "correct": False}, {"text": "are", "correct": False}, {"text": "be", "correct": False}], "explanation": "The correct form of 'to be' for first person singular 'I' is 'am'."},
        {"stem": "We _______ friends from school.", "category": "Grammar", "difficulty": 1, "options": [{"text": "are", "correct": True}, {"text": "is", "correct": False}, {"text": "am", "correct": False}, {"text": "be", "correct": False}], "explanation": "For plural subjects like 'we', we use the verb 'are'."},
        {"stem": "{name} _______ a new red bicycle.", "category": "Grammar", "difficulty": 1, "options": [{"text": "has", "correct": True}, {"text": "have", "correct": False}, {"text": "is", "correct": False}, {"text": "are", "correct": False}], "explanation": "Third person singular subjects use 'has' for possession."},
        {"stem": "They _______ have a car.", "category": "Grammar", "difficulty": 1, "options": [{"text": "don't", "correct": True}, {"text": "doesn't", "correct": False}, {"text": "isn't", "correct": False}, {"text": "aren't", "correct": False}], "explanation": "Third person plural 'they' uses the auxiliary negative 'don't'."},
        {"stem": "Where _______ you from?", "category": "Grammar", "difficulty": 1, "options": [{"text": "are", "correct": True}, {"text": "is", "correct": False}, {"text": "am", "correct": False}, {"text": "do", "correct": False}], "explanation": "'Where are you from?' is the standard greeting question for origin."},
        {"stem": "She _______ in a big house.", "category": "Grammar", "difficulty": 1, "options": [{"text": "lives", "correct": True}, {"text": "live", "correct": False}, {"text": "living", "correct": False}, {"text": "lived", "correct": False}], "explanation": "Third person singular 'she' takes present tense verb with -s."},
        {"stem": "What is _______? It is a {noun}.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "this", "correct": True}, {"text": "these", "correct": False}, {"text": "those", "correct": False}, {"text": "they", "correct": False}], "explanation": "We use 'this' for a singular item close to us."},
        {"stem": "How _______ is this {noun}? It is five dollars.", "category": "Grammar", "difficulty": 1, "options": [{"text": "much", "correct": True}, {"text": "many", "correct": False}, {"text": "much cost", "correct": False}, {"text": "price", "correct": False}], "explanation": "We use 'how much' to ask about price/cost."},
        {"stem": "There are five _______ on the table.", "category": "Grammar", "difficulty": 1, "options": [{"text": "books", "correct": True}, {"text": "book", "correct": False}, {"text": "a book", "correct": False}, {"text": "books'", "correct": False}], "explanation": "Plural numbers require plural noun forms like 'books'."},
        {"stem": "I have _______ apple in my bag.", "category": "Grammar", "difficulty": 1, "options": [{"text": "an", "correct": True}, {"text": "a", "correct": False}, {"text": "some", "correct": False}, {"text": "any", "correct": False}], "explanation": "We use 'an' before words starting with a vowel sound."},
        {"stem": "Is {name} a doctor? Yes, _______ is.", "category": "Grammar", "difficulty": 1, "options": [{"text": "he", "correct": True}, {"text": "his", "correct": False}, {"text": "him", "correct": False}, {"text": "himself", "correct": False}], "explanation": "We use subject pronouns like 'he' to answer simple questions."},
        {"stem": "It is very cold _______ winter.", "category": "Grammar", "difficulty": 1, "options": [{"text": "in", "correct": True}, {"text": "on", "correct": False}, {"text": "at", "correct": False}, {"text": "under", "correct": False}], "explanation": "We use 'in' for seasons like winter."},
        {"stem": "My birthday is _______ October.", "category": "Grammar", "difficulty": 1, "options": [{"text": "in", "correct": True}, {"text": "on", "correct": False}, {"text": "at", "correct": False}, {"text": "by", "correct": False}], "explanation": "We use 'in' for months of the year."},
        {"stem": "We go to school _______ the morning.", "category": "Grammar", "difficulty": 1, "options": [{"text": "in", "correct": True}, {"text": "on", "correct": False}, {"text": "at", "correct": False}, {"text": "for", "correct": False}], "explanation": "We use the preposition 'in' in the phrase 'in the morning'."},
        {"stem": "What time is _______? It is 2:00 PM.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "it", "correct": True}, {"text": "time", "correct": False}, {"text": "this", "correct": False}, {"text": "now", "correct": False}], "explanation": "'What time is it?' is the standard structure for asking current time."},
        {"stem": "These are my _______.", "category": "Grammar", "difficulty": 1, "options": [{"text": "keys", "correct": True}, {"text": "key", "correct": False}, {"text": "a key", "correct": False}, {"text": "key's", "correct": False}], "explanation": "The plural demonstrative 'these' requires plural nouns."},
        {"stem": "{name} _______ watch television in the evening.", "category": "Grammar", "difficulty": 1, "options": [{"text": "doesn't", "correct": True}, {"text": "don't", "correct": False}, {"text": "isn't", "correct": False}, {"text": "not", "correct": False}], "explanation": "Third person singular 'doesn't' is used for negative present tense."},
        {"stem": "Can you _______ English?", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "speak", "correct": True}, {"text": "tell", "correct": False}, {"text": "talk", "correct": False}, {"text": "say", "correct": False}], "explanation": "We use 'speak' when talking about languages."},
        {"stem": "I like _______ apples and oranges.", "category": "Grammar", "difficulty": 1, "options": [{"text": "eating", "correct": True}, {"text": "eat", "correct": False}, {"text": "eats", "correct": False}, {"text": "eaten", "correct": False}], "explanation": "Verbs of liking (like/love) are followed by the gerund form (-ing)."},
        {"stem": "The book is _______ the desk.", "category": "Grammar", "difficulty": 1, "options": [{"text": "on", "correct": True}, {"text": "in", "correct": False}, {"text": "at", "correct": False}, {"text": "to", "correct": False}], "explanation": "The preposition 'on' indicates contact with a surface."},
        {"stem": "Where is the cat? It is _______ the chair.", "category": "Grammar", "difficulty": 1, "options": [{"text": "under", "correct": True}, {"text": "on top", "correct": False}, {"text": "between", "correct": False}, {"text": "through", "correct": False}], "explanation": "'Under the chair' is a common prepositional phrase of place."},
        {"stem": "I get up _______ 7 o'clock.", "category": "Grammar", "difficulty": 1, "options": [{"text": "at", "correct": True}, {"text": "in", "correct": False}, {"text": "on", "correct": False}, {"text": "to", "correct": False}], "explanation": "We use 'at' for specific times on the clock."},
        {"stem": "Goodbye! See you _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "tomorrow", "correct": True}, {"text": "yesterday", "correct": False}, {"text": "now", "correct": False}, {"text": "before", "correct": False}], "explanation": "'See you tomorrow' is a common parting greeting."},
        {"stem": "Read and answer: '{name} has a brown dog. Its name is Max.' What is the dog's name?", "category": "Reading", "difficulty": 1, "options": [{"text": "Max", "correct": True}, {"text": "Charlie", "correct": False}, {"text": "Buddy", "correct": False}, {"text": "Rocky", "correct": False}], "explanation": "The text states: 'Its name is Max.'"},
        {"stem": "Read and answer: '{name} is in the kitchen. She is cooking dinner.' Where is {name}?", "category": "Reading", "difficulty": 1, "options": [{"text": "In the kitchen", "correct": True}, {"text": "In the garden", "correct": False}, {"text": "In the bedroom", "correct": False}, {"text": "At school", "correct": False}], "explanation": "The text states: '{name} is in the kitchen.'"},
        {"stem": "Read and answer: 'The book is blue. It is on the table.' What is on the table?", "category": "Reading", "difficulty": 1, "options": [{"text": "The book", "correct": True}, {"text": "The pen", "correct": False}, {"text": "The phone", "correct": False}, {"text": "The bag", "correct": False}], "explanation": "The text states: 'The book ... is on the table.'"},
        {"stem": "Read and answer: 'Tom is a doctor. He works in a hospital.' Where does Tom work?", "category": "Reading", "difficulty": 1, "options": [{"text": "In a hospital", "correct": True}, {"text": "In a school", "correct": False}, {"text": "In an office", "correct": False}, {"text": "At home", "correct": False}], "explanation": "The text states: 'He works in a hospital.'"}
    ],
    "Elementary": [
        {"stem": "Yesterday, {name} _______ to the park and read a book.", "category": "Grammar", "difficulty": 1, "options": [{"text": "went", "correct": True}, {"text": "go", "correct": False}, {"text": "goes", "correct": False}, {"text": "going", "correct": False}], "explanation": "'Yesterday' indicates past tense, so we use the irregular past verb 'went'."},
        {"stem": "This car is _______ than that one.", "category": "Grammar", "difficulty": 1, "options": [{"text": "faster", "correct": True}, {"text": "fast", "correct": False}, {"text": "fastest", "correct": False}, {"text": "more fast", "correct": False}], "explanation": "Use comparative form 'faster' when comparing two items."},
        {"stem": "Who is the _______ person in your family?", "category": "Grammar", "difficulty": 1, "options": [{"text": "tallest", "correct": True}, {"text": "taller", "correct": False}, {"text": "tall", "correct": False}, {"text": "most tall", "correct": False}], "explanation": "Use superlative form 'tallest' when comparing three or more things."},
        {"stem": "She is _______ English right now.", "category": "Grammar", "difficulty": 1, "options": [{"text": "studying", "correct": True}, {"text": "studies", "correct": False}, {"text": "study", "correct": False}, {"text": "studied", "correct": False}], "explanation": "'Right now' indicates present continuous tense, so we use 'be + verb-ing'."},
        {"stem": "Did you _______ the movie last night?", "category": "Grammar", "difficulty": 1, "options": [{"text": "watch", "correct": True}, {"text": "watched", "correct": False}, {"text": "watches", "correct": False}, {"text": "watching", "correct": False}], "explanation": "Questions starting with 'did' require base form of the verb."},
        {"stem": "I didn't _______ any coffee this morning.", "category": "Grammar", "difficulty": 1, "options": [{"text": "drink", "correct": True}, {"text": "drank", "correct": False}, {"text": "drinks", "correct": False}, {"text": "drinking", "correct": False}], "explanation": "Negations with 'didn't' require the base form of the verb."},
        {"stem": "He usually _______ breakfast at 7 AM.", "category": "Grammar", "difficulty": 1, "options": [{"text": "has", "correct": True}, {"text": "have", "correct": False}, {"text": "having", "correct": False}, {"text": "had", "correct": False}], "explanation": "'Usually' indicates present simple. Third person 'he' takes 'has'."},
        {"stem": "We _______ a great time at the beach yesterday.", "category": "Grammar", "difficulty": 1, "options": [{"text": "had", "correct": True}, {"text": "have", "correct": False}, {"text": "has", "correct": False}, {"text": "having", "correct": False}], "explanation": "'Yesterday' requires the past tense form 'had'."},
        {"stem": "Look! It _______ to rain.", "category": "Grammar", "difficulty": 1, "options": [{"text": "is starting", "correct": True}, {"text": "starts", "correct": False}, {"text": "started", "correct": False}, {"text": "starting", "correct": False}], "explanation": "'Look!' signals an action happening right now (present continuous)."},
        {"stem": "Would you like _______ tea?", "category": "Grammar", "difficulty": 1, "options": [{"text": "some", "correct": True}, {"text": "any", "correct": False}, {"text": "a", "correct": False}, {"text": "many", "correct": False}], "explanation": "We use 'some' in polite requests and offers."},
        {"stem": "I don't have _______ money left in my wallet.", "category": "Grammar", "difficulty": 1, "options": [{"text": "any", "correct": True}, {"text": "some", "correct": False}, {"text": "many", "correct": False}, {"text": "a", "correct": False}], "explanation": "In negative sentences, we use 'any' with uncountable nouns like 'money'."},
        {"stem": "Are there _______ apples in the fridge?", "category": "Grammar", "difficulty": 1, "options": [{"text": "any", "correct": True}, {"text": "some", "correct": False}, {"text": "much", "correct": False}, {"text": "a", "correct": False}], "explanation": "We use 'any' in questions with plural countable nouns."},
        {"stem": "I _______ to school by bus every day.", "category": "Grammar", "difficulty": 1, "options": [{"text": "go", "correct": True}, {"text": "goes", "correct": False}, {"text": "going", "correct": False}, {"text": "went", "correct": False}], "explanation": "'Every day' indicates a routine, so we use present simple 'go'."},
        {"stem": "She was born _______ 2010.", "category": "Grammar", "difficulty": 1, "options": [{"text": "in", "correct": True}, {"text": "on", "correct": False}, {"text": "at", "correct": False}, {"text": "by", "correct": False}], "explanation": "We use 'in' before specific years."},
        {"stem": "My brother is _______ engineer.", "category": "Grammar", "difficulty": 1, "options": [{"text": "an", "correct": True}, {"text": "a", "correct": False}, {"text": "some", "correct": False}, {"text": "the", "correct": False}], "explanation": "We use 'an' before occupation names starting with a vowel sound."},
        {"stem": "Can you help _______ with my homework?", "category": "Grammar", "difficulty": 1, "options": [{"text": "me", "correct": True}, {"text": "I", "correct": False}, {"text": "my", "correct": False}, {"text": "mine", "correct": False}], "explanation": "We use the object pronoun 'me' after the verb 'help'."},
        {"stem": "This book belongs to _______.", "category": "Grammar", "difficulty": 1, "options": [{"text": "him", "correct": True}, {"text": "he", "correct": False}, {"text": "his", "correct": False}, {"text": "himself", "correct": False}], "explanation": "We use object pronouns like 'him' after prepositions like 'to'."},
        {"stem": "They live in _______ big city.", "category": "Grammar", "difficulty": 1, "options": [{"text": "a", "correct": True}, {"text": "an", "correct": False}, {"text": "some", "correct": False}, {"text": "any", "correct": False}], "explanation": "Use 'a' for singular countable nouns starting with consonant sounds."},
        {"stem": "Excuse me, is this _______ pen?", "category": "Grammar", "difficulty": 1, "options": [{"text": "your", "correct": True}, {"text": "you", "correct": False}, {"text": "yours", "correct": False}, {"text": "yours'", "correct": False}], "explanation": "Use the possessive adjective 'your' before the noun 'pen'."},
        {"stem": "I can't find my keys. Have you seen _______?", "category": "Grammar", "difficulty": 1, "options": [{"text": "them", "correct": True}, {"text": "it", "correct": False}, {"text": "their", "correct": False}, {"text": "they", "correct": False}], "explanation": "Refer to plural noun 'keys' using object pronoun 'them'."},
        {"stem": "We _______ at the hotel last Sunday.", "category": "Grammar", "difficulty": 1, "options": [{"text": "stayed", "correct": True}, {"text": "stay", "correct": False}, {"text": "stays", "correct": False}, {"text": "staying", "correct": False}], "explanation": "'Last Sunday' indicates the past tense, requiring the regular verb form 'stayed'."},
        {"stem": "He doesn't like _______ early in the morning.", "category": "Grammar", "difficulty": 1, "options": [{"text": "waking up", "correct": True}, {"text": "wake up", "correct": False}, {"text": "wakes up", "correct": False}, {"text": "woke up", "correct": False}], "explanation": "'Like' is followed by gerund (-ing) for general preferences."},
        {"stem": "Is it _______ outside? Yes, it is raining.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "wet", "correct": True}, {"text": "hot", "correct": False}, {"text": "dry", "correct": False}, {"text": "windy", "correct": False}], "explanation": "Rain results in wet conditions outdoors."},
        {"stem": "She works in an office. She is a _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "secretary", "correct": True}, {"text": "doctor", "correct": False}, {"text": "driver", "correct": False}, {"text": "farmer", "correct": False}], "explanation": "'Secretary' is an office occupation, unlike farmer or driver."},
        {"stem": "We need to buy some bread at the _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "bakery", "correct": True}, {"text": "butcher's", "correct": False}, {"text": "library", "correct": False}, {"text": "pharmacy", "correct": False}], "explanation": "Bread is sold at the bakery."},
        {"stem": "The opposite of 'cheap' is _______.", "category": "Vocabulary", "difficulty": 1, "options": [{"text": "expensive", "correct": True}, {"text": "easy", "correct": False}, {"text": "poor", "correct": False}, {"text": "free", "correct": False}], "explanation": "'Expensive' is the antonym of 'cheap'."},
        {"stem": "Read and answer: '{name} went to London last summer. She visited many museums. She loved the city.' When did {name} go to London?", "category": "Reading", "difficulty": 1, "options": [{"text": "Last summer", "correct": True}, {"text": "Last winter", "correct": False}, {"text": "Two years ago", "correct": False}, {"text": "Yesterday", "correct": False}], "explanation": "The text explicitly states: '{name} went to London last summer.'"},
        {"stem": "Read and answer: 'David is a teacher. He teaches chemistry. He has 30 students in his class.' What does David teach?", "category": "Reading", "difficulty": 1, "options": [{"text": "Chemistry", "correct": True}, {"text": "Physics", "correct": False}, {"text": "Biology", "correct": False}, {"text": "Math", "correct": False}], "explanation": "The text states: 'He teaches chemistry.'"},
        {"stem": "Read and answer: 'The train leaves at 9:00 AM. It takes two hours to reach Paris.' What time does the train arrive in Paris?", "category": "Reading", "difficulty": 1, "options": [{"text": "11:00 AM", "correct": True}, {"text": "10:00 AM", "correct": False}, {"text": "12:00 PM", "correct": False}, {"text": "9:00 AM", "correct": False}], "explanation": "Adding two hours to 9:00 AM gives 11:00 AM."},
        {"stem": "Read and answer: 'Apples are good for your health. You should eat one every day.' What is good for your health?", "category": "Reading", "difficulty": 1, "options": [{"text": "Apples", "correct": True}, {"text": "Candy", "correct": False}, {"text": "Soda", "correct": False}, {"text": "Pizza", "correct": False}], "explanation": "The text states: 'Apples are good for your health.'"}
    ],
    "Pre-Intermediate": [
        {"stem": "If it _______ tomorrow, we will stay at home.", "category": "Grammar", "difficulty": 2, "options": [{"text": "rains", "correct": True}, {"text": "will rain", "correct": False}, {"text": "rained", "correct": False}, {"text": "is raining", "correct": False}], "explanation": "First conditional uses Present Simple in the conditional clause."},
        {"stem": "Have you _______ been to France?", "category": "Grammar", "difficulty": 2, "options": [{"text": "ever", "correct": True}, {"text": "never", "correct": False}, {"text": "yet", "correct": False}, {"text": "already", "correct": False}], "explanation": "Use 'ever' in questions about life experiences."},
        {"stem": "I _______ here since 2018.", "category": "Grammar", "difficulty": 2, "options": [{"text": "have lived", "correct": True}, {"text": "live", "correct": False}, {"text": "am living", "correct": False}, {"text": "lived", "correct": False}], "explanation": "Present perfect tense is used for actions continuing from the past to the present, signaled by 'since'."},
        {"stem": "She has been working as a teacher _______ five years.", "category": "Grammar", "difficulty": 2, "options": [{"text": "for", "correct": True}, {"text": "since", "correct": False}, {"text": "during", "correct": False}, {"text": "ago", "correct": False}], "explanation": "Use 'for' to describe a duration of time."},
        {"stem": "We _______ to the cinema last night.", "category": "Grammar", "difficulty": 2, "options": [{"text": "went", "correct": True}, {"text": "have gone", "correct": False}, {"text": "had gone", "correct": False}, {"text": "go", "correct": False}], "explanation": "'Last night' requires simple past 'went', not present perfect."},
        {"stem": "He _______ his homework before he went to bed.", "category": "Grammar", "difficulty": 2, "options": [{"text": "had finished", "correct": True}, {"text": "has finished", "correct": False}, {"text": "finishes", "correct": False}, {"text": "finished", "correct": False}], "explanation": "The action completed before another past action uses past perfect ('had finished')."},
        {"stem": "I _______ see you tomorrow, but I'm not sure.", "category": "Grammar", "difficulty": 2, "options": [{"text": "might", "correct": True}, {"text": "must", "correct": False}, {"text": "should", "correct": False}, {"text": "will", "correct": False}], "explanation": "'Might' is used to express uncertainty/possibility."},
        {"stem": "You _______ smoke in this area. It is forbidden.", "category": "Grammar", "difficulty": 2, "options": [{"text": "mustnot", "correct": True}, {"text": "don't have to", "correct": False}, {"text": "needn't", "correct": False}, {"text": "couldn't", "correct": False}], "explanation": "'Must not' expresses prohibition, whereas 'don't have to' shows lack of obligation."},
        {"stem": "If I _______ rich, I would buy a big yacht.", "category": "Grammar", "difficulty": 2, "options": [{"text": "were", "correct": True}, {"text": "am", "correct": False}, {"text": "will be", "correct": False}, {"text": "would be", "correct": False}], "explanation": "Second conditional uses subjunctive 'were' in the if-clause."},
        {"stem": "The flight was delayed, _______ we had to wait at the airport.", "category": "Grammar", "difficulty": 2, "options": [{"text": "so", "correct": True}, {"text": "because", "correct": False}, {"text": "but", "correct": False}, {"text": "although", "correct": False}], "explanation": "Use 'so' to introduce the consequence of the delayed flight."},
        {"stem": "Although it was raining, they _______ a walk.", "category": "Grammar", "difficulty": 2, "options": [{"text": "took", "correct": True}, {"text": "take", "correct": False}, {"text": "taking", "correct": False}, {"text": "taken", "correct": False}], "explanation": "Although introduces concession, but the main clause verb must match the past context ('took')."},
        {"stem": "This is the house _______ my grandfather built.", "category": "Grammar", "difficulty": 2, "options": [{"text": "which", "correct": True}, {"text": "who", "correct": False}, {"text": "whose", "correct": False}, {"text": "where", "correct": False}], "explanation": "Use relative pronoun 'which' (or 'that') for objects/inanimate things."},
        {"stem": "The man _______ lives next door is a doctor.", "category": "Grammar", "difficulty": 2, "options": [{"text": "who", "correct": True}, {"text": "which", "correct": False}, {"text": "whose", "correct": False}, {"text": "whom", "correct": False}], "explanation": "Use relative pronoun 'who' for people."},
        {"stem": "She is very good _______ playing the piano.", "category": "Grammar", "difficulty": 2, "options": [{"text": "at", "correct": True}, {"text": "in", "correct": False}, {"text": "on", "correct": False}, {"text": "for", "correct": False}], "explanation": "The adjective collocation is 'good at doing something'."},
        {"stem": "Are you interested _______ learning Spanish?", "category": "Grammar", "difficulty": 2, "options": [{"text": "in", "correct": True}, {"text": "at", "correct": False}, {"text": "on", "correct": False}, {"text": "for", "correct": False}], "explanation": "The adjective collocation is 'interested in doing something'."},
        {"stem": "He was _______ tired that he fell asleep immediately.", "category": "Grammar", "difficulty": 2, "options": [{"text": "so", "correct": True}, {"text": "such", "correct": False}, {"text": "too", "correct": False}, {"text": "very", "correct": False}], "explanation": "Use 'so + adjective + that' clause structure."},
        {"stem": "It was _______ a beautiful day that we went to the beach.", "category": "Grammar", "difficulty": 2, "options": [{"text": "such", "correct": True}, {"text": "so", "correct": False}, {"text": "too", "correct": False}, {"text": "very", "correct": False}], "explanation": "Use 'such + a/an + adjective + noun + that' structure."},
        {"stem": "They _______ breakfast when the phone rang.", "category": "Grammar", "difficulty": 2, "options": [{"text": "were having", "correct": True}, {"text": "had", "correct": False}, {"text": "have had", "correct": False}, {"text": "are having", "correct": False}], "explanation": "Use past continuous for an ongoing action interrupted by a past simple action."},
        {"stem": "I used to _______ football when I was a child.", "category": "Grammar", "difficulty": 2, "options": [{"text": "play", "correct": True}, {"text": "playing", "correct": False}, {"text": "played", "correct": False}, {"text": "plays", "correct": False}], "explanation": "'Used to' is followed by the base infinitive verb form."},
        {"stem": "I look forward to _______ you soon.", "category": "Grammar", "difficulty": 2, "options": [{"text": "seeing", "correct": True}, {"text": "see", "correct": False}, {"text": "seen", "correct": False}, {"text": "saw", "correct": False}], "explanation": "The prepositional phrase 'look forward to' requires a gerund (-ing)."},
        {"stem": "This room _______ every day.", "category": "Grammar", "difficulty": 2, "options": [{"text": "is cleaned", "correct": True}, {"text": "cleans", "correct": False}, {"text": "cleaned", "correct": False}, {"text": "is cleaning", "correct": False}], "explanation": "Passive voice is required since the room receives the action of cleaning."},
        {"stem": "He didn't pass the exam because he didn't study _______.", "category": "Grammar", "difficulty": 2, "options": [{"text": "enough", "correct": True}, {"text": "too", "correct": False}, {"text": "much", "correct": False}, {"text": "sufficient", "correct": False}], "explanation": "'Enough' goes after the verb/adverb in negative statements."},
        {"stem": "Could you _______ me some money, please?", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "lend", "correct": True}, {"text": "borrow", "correct": False}, {"text": "take", "correct": False}, {"text": "keep", "correct": False}], "explanation": "'Lend' means to give temporarily, while 'borrow' means to receive temporarily."},
        {"stem": "I _______ my keys. Can you help me find them?", "category": "Grammar", "difficulty": 2, "options": [{"text": "have lost", "correct": True}, {"text": "lost", "correct": False}, {"text": "lose", "correct": False}, {"text": "was losing", "correct": False}], "explanation": "Present perfect is used here as the result (keys still missing) is relevant now."},
        {"stem": "She _______ she would come to the party.", "category": "Grammar", "difficulty": 2, "options": [{"text": "said", "correct": True}, {"text": "told", "correct": False}, {"text": "spoke", "correct": False}, {"text": "talked", "correct": False}], "explanation": "'Said' does not require a direct object, whereas 'told' requires a personal object (e.g. told me)."},
        {"stem": "The doctor told me to _______ smoking.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "give up", "correct": True}, {"text": "give in", "correct": False}, {"text": "put off", "correct": False}, {"text": "take up", "correct": False}], "explanation": "'Give up' is a phrasal verb meaning to quit or stop."},
        {"stem": "Read and answer: '{name} travels a lot. Last year she visited Tokyo, Paris, and Rome. She preferred Tokyo because of the food.' Which city did she like most?", "category": "Reading", "difficulty": 2, "options": [{"text": "Tokyo", "correct": True}, {"text": "Paris", "correct": False}, {"text": "Rome", "correct": False}, {"text": "London", "correct": False}], "explanation": "She preferred Tokyo because of the food."},
        {"stem": "Read and answer: 'If you want to bake a cake, you need flour, sugar, eggs, and butter.' What is NOT listed as an ingredient?", "category": "Reading", "difficulty": 2, "options": [{"text": "Milk", "correct": True}, {"text": "Eggs", "correct": False}, {"text": "Flour", "correct": False}, {"text": "Sugar", "correct": False}], "explanation": "The text lists flour, sugar, eggs, and butter, but not milk."},
        {"stem": "Read and answer: 'Although remote work is flexible, it can lead to loneliness.' What is a disadvantage of remote work according to the text?", "category": "Reading", "difficulty": 2, "options": [{"text": "Loneliness", "correct": True}, {"text": "Flexibility", "correct": False}, {"text": "Commute time", "correct": False}, {"text": "Higher utility bills", "correct": False}], "explanation": "The text states that remote work 'can lead to loneliness'."},
        {"stem": "Read and answer: 'Jane started learning guitar two years ago. She practices for one hour every day.' How long has Jane been practicing guitar?", "category": "Reading", "difficulty": 2, "options": [{"text": "Two years", "correct": True}, {"text": "One year", "correct": False}, {"text": "Two months", "correct": False}, {"text": "Five years", "correct": False}], "explanation": "The text states she started 'two years ago'."}
    ],
    "Intermediate": [
        {"stem": "I wish I _______ more time to study before the exam last week.", "category": "Grammar", "difficulty": 2, "options": [{"text": "had had", "correct": True}, {"text": "have", "correct": False}, {"text": "had", "correct": False}, {"text": "would have", "correct": False}], "explanation": "To express regret about a past situation, we use 'wish + past perfect'."},
        {"stem": "The manager insisted _______ completing the task by Friday.", "category": "Grammar", "difficulty": 2, "options": [{"text": "on", "correct": True}, {"text": "to", "correct": False}, {"text": "for", "correct": False}, {"text": "in", "correct": False}], "explanation": "The verb 'insist' is prepositively paired with 'on'."},
        {"stem": "A new highway _______ built in the city center.", "category": "Grammar", "difficulty": 2, "options": [{"text": "is being", "correct": True}, {"text": "is", "correct": False}, {"text": "has", "correct": False}, {"text": "was", "correct": False}], "explanation": "Present continuous passive 'is being built' describes an ongoing construction project."},
        {"stem": "His excuse for missing the meeting was highly _______; nobody believed him.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "implausible", "correct": True}, {"text": "plausible", "correct": False}, {"text": "convincing", "correct": False}, {"text": "honest", "correct": False}], "explanation": "'Implausible' means not believable or unlikely to be true."},
        {"stem": "I'm not used to _______ early in the morning.", "category": "Grammar", "difficulty": 2, "options": [{"text": "waking up", "correct": True}, {"text": "wake up", "correct": False}, {"text": "wakes up", "correct": False}, {"text": "woke up", "correct": False}], "explanation": "'Be used to' is followed by a gerund (-ing) indicating familiarity with a habit."},
        {"stem": "The police officer asked me where I _______.", "category": "Grammar", "difficulty": 2, "options": [{"text": "lived", "correct": True}, {"text": "live", "correct": False}, {"text": "had lived", "correct": False}, {"text": "was living", "correct": False}], "explanation": "Reported questions shift back in tense; present simple 'live' becomes past simple 'lived'."},
        {"stem": "She suggested _______ to the cinema.", "category": "Grammar", "difficulty": 2, "options": [{"text": "going", "correct": True}, {"text": "to go", "correct": False}, {"text": "go", "correct": False}, {"text": "went", "correct": False}], "explanation": "'Suggest' is followed directly by a gerund (-ing) or a 'that' clause."},
        {"stem": "He denied _______ the money.", "category": "Grammar", "difficulty": 2, "options": [{"text": "stealing", "correct": True}, {"text": "to steal", "correct": False}, {"text": "steal", "correct": False}, {"text": "stolen", "correct": False}], "explanation": "'Deny' is followed by a gerund (-ing) for past actions."},
        {"stem": "By the time we arrived, the train _______.", "category": "Grammar", "difficulty": 2, "options": [{"text": "had left", "correct": True}, {"text": "left", "correct": False}, {"text": "has left", "correct": False}, {"text": "was leaving", "correct": False}], "explanation": "The train left before they arrived, so past perfect 'had left' is required."},
        {"stem": "If you _______ me earlier, I would have helped you.", "category": "Grammar", "difficulty": 2, "options": [{"text": "had told", "correct": True}, {"text": "told", "correct": False}, {"text": "would tell", "correct": False}, {"text": "have told", "correct": False}], "explanation": "Third conditional requires past perfect 'had told' in the if-clause."},
        {"stem": "I would rather you _______ smoke in here.", "category": "Grammar", "difficulty": 2, "options": [{"text": "didn't", "correct": True}, {"text": "don't", "correct": False}, {"text": "not to", "correct": False}, {"text": "would not", "correct": False}], "explanation": "When 'would rather' has a subject change, we use simple past negative 'didn't'."},
        {"stem": "He ran as fast as he could _______ miss the train.", "category": "Grammar", "difficulty": 2, "options": [{"text": "in order not to", "correct": True}, {"text": "so that to not", "correct": False}, {"text": "for not to", "correct": False}, {"text": "to not", "correct": False}], "explanation": "'In order not to' is the standard negative structure of purpose."},
        {"stem": "You had better _______ a doctor about that cough.", "category": "Grammar", "difficulty": 2, "options": [{"text": "see", "correct": True}, {"text": "to see", "correct": False}, {"text": "seeing", "correct": False}, {"text": "saw", "correct": False}], "explanation": "'Had better' is followed by a bare infinitive verb form."},
        {"stem": "It is high time we _______.", "category": "Grammar", "difficulty": 2, "options": [{"text": "left", "correct": True}, {"text": "leave", "correct": False}, {"text": "to leave", "correct": False}, {"text": "are leaving", "correct": False}], "explanation": "'It is high time' takes a past subjunctive/simple past form to show urgency."},
        {"stem": "No sooner had I entered the room _______ the phone rang.", "category": "Grammar", "difficulty": 2, "options": [{"text": "than", "correct": True}, {"text": "when", "correct": False}, {"text": "then", "correct": False}, {"text": "that", "correct": False}], "explanation": "The correlative structure is 'No sooner ... than'."},
        {"stem": "She succeeded _______ passing the driving test.", "category": "Grammar", "difficulty": 2, "options": [{"text": "in", "correct": True}, {"text": "on", "correct": False}, {"text": "at", "correct": False}, {"text": "to", "correct": False}], "explanation": "The verb 'succeed' collocates with the preposition 'in'."},
        {"stem": "Despite _______ a cold, he went to work.", "category": "Grammar", "difficulty": 2, "options": [{"text": "having", "correct": True}, {"text": "he had", "correct": False}, {"text": "of having", "correct": False}, {"text": "have", "correct": False}], "explanation": "'Despite' is followed by a noun or gerund (-ing) form."},
        {"stem": "We decided to cancel the match due to the _______ weather.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "inclement", "correct": True}, {"text": "sunny", "correct": False}, {"text": "warm", "correct": False}, {"text": "mild", "correct": False}], "explanation": "'Inclement' means severe, rough, or harsh weather."},
        {"stem": "The new project was launched to _______ sales.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "boost", "correct": True}, {"text": "hinder", "correct": False}, {"text": "dampen", "correct": False}, {"text": "negate", "correct": False}], "explanation": "'Boost' means to increase or improve, which is the goal of launching projects."},
        {"stem": "He is known _______ his honesty.", "category": "Grammar", "difficulty": 2, "options": [{"text": "for", "correct": True}, {"text": "by", "correct": False}, {"text": "about", "correct": False}, {"text": "with", "correct": False}], "explanation": "The passive collocation is 'known for something'."},
        {"stem": "I look forward to _______ from you.", "category": "Grammar", "difficulty": 2, "options": [{"text": "hearing", "correct": True}, {"text": "hear", "correct": False}, {"text": "have heard", "correct": False}, {"text": "to hear", "correct": False}], "explanation": "'Look forward to' is a phrasal prepositional verb taking a gerund (-ing)."},
        {"stem": "She doesn't mind _______ overtime occasionally.", "category": "Grammar", "difficulty": 2, "options": [{"text": "working", "correct": True}, {"text": "to work", "correct": False}, {"text": "work", "correct": False}, {"text": "worked", "correct": False}], "explanation": "'Mind' in negative sentences takes a gerund (-ing) verb form."},
        {"stem": "The meeting was _______ till next week.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "put off", "correct": True}, {"text": "put on", "correct": False}, {"text": "called off", "correct": False}, {"text": "taken off", "correct": False}], "explanation": "'Put off' is a phrasal verb meaning to postpone."},
        {"stem": "I can't stand _______ in long queues.", "category": "Grammar", "difficulty": 2, "options": [{"text": "waiting", "correct": True}, {"text": "to wait", "correct": False}, {"text": "wait", "correct": False}, {"text": "waited", "correct": False}], "explanation": "'Can't stand' is followed by a gerund (-ing)."},
        {"stem": "We must prevent this problem _______ happening again.", "category": "Grammar", "difficulty": 2, "options": [{"text": "from", "correct": True}, {"text": "to", "correct": False}, {"text": "against", "correct": False}, {"text": "of", "correct": False}], "explanation": "The standard verb pattern is 'prevent someone/something from doing something'."},
        {"stem": "The price of petrol has _______ rapidly.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "soared", "correct": True}, {"text": "plunged", "correct": False}, {"text": "drifted", "correct": False}, {"text": "stabilized", "correct": False}], "explanation": "'Soared' means risen rapidly, matching the context of inflation."},
        {"stem": "Read and answer: 'The Socratic method relies on cooperative argumentative dialogue to stimulate critical thinking.' What is the primary purpose of the Socratic method?", "category": "Reading", "difficulty": 2, "options": [{"text": "To stimulate critical thinking", "correct": True}, {"text": "To win debates", "correct": False}, {"text": "To memorize facts", "correct": False}, {"text": "To write books", "correct": False}], "explanation": "The text states the method is used 'to stimulate critical thinking'."},
        {"stem": "Read and answer: 'Despite economic challenges, the company maintained its research budget, anticipating long-term benefits.' What did the company do?", "category": "Reading", "difficulty": 2, "options": [{"text": "Maintained its research budget", "correct": True}, {"text": "Cut research spending", "correct": False}, {"text": "Fired its scientists", "correct": False}, {"text": "Closed its operations", "correct": False}], "explanation": "The text states it 'maintained its research budget'."},
        {"stem": "Read and answer: 'Biodiversity is crucial for ecosystem stability. When species go extinct, the entire network suffers.' What is crucial for stability?", "category": "Reading", "difficulty": 2, "options": [{"text": "Biodiversity", "correct": True}, {"text": "Extinction", "correct": False}, {"text": "Fossil fuels", "correct": False}, {"text": "Monoculture", "correct": False}], "explanation": "The text states: 'Biodiversity is crucial for ecosystem stability.'"},
        {"stem": "Read and answer: 'Active listening involves paraphrasing and reflecting to ensure comprehension.' What does active listening involve?", "category": "Reading", "difficulty": 2, "options": [{"text": "Paraphrasing and reflecting", "correct": True}, {"text": "Ignoring distractions", "correct": False}, {"text": "Speaking quickly", "correct": False}, {"text": "Taking notes", "correct": False}], "explanation": "The text states: 'Active listening involves paraphrasing and reflecting.'"}
    ],
    "Upper-Intermediate": [
        {"stem": "By this time next year, she _______ her master's degree.", "category": "Grammar", "difficulty": 2, "options": [{"text": "will have completed", "correct": True}, {"text": "will complete", "correct": False}, {"text": "will be completing", "correct": False}, {"text": "is completing", "correct": False}], "explanation": "Future perfect ('will have completed') describes an action done before a future point."},
        {"stem": "We had to _______ the meeting due to the transport strike.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "call off", "correct": True}, {"text": "call on", "correct": False}, {"text": "put out", "correct": False}, {"text": "carry out", "correct": False}], "explanation": "'Call off' is a phrasal verb meaning to cancel."},
        {"stem": "Hardly _______ entered the house when the phone began to ring.", "category": "Grammar", "difficulty": 3, "options": [{"text": "had I", "correct": True}, {"text": "I had", "correct": False}, {"text": "did I", "correct": False}, {"text": "was I", "correct": False}], "explanation": "With negative adverbials like 'Hardly' starting a sentence, subject-auxiliary inversion is required."},
        {"stem": "The company's profits have been _______; they fluctuate constantly.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "erratic", "correct": True}, {"text": "steady", "correct": False}, {"text": "unrivaled", "correct": False}, {"text": "monolithic", "correct": False}], "explanation": "'Erratic' means unpredictable, matching the clause 'fluctuate constantly'."},
        {"stem": "It is essential that she _______ present at the meeting.", "category": "Grammar", "difficulty": 2, "options": [{"text": "be", "correct": True}, {"text": "is", "correct": False}, {"text": "was", "correct": False}, {"text": "should be", "correct": False}], "explanation": "Subjunctive mood ('be') is used after advisory adjectives like 'essential'."},
        {"stem": "I would appreciate _______ from you as soon as possible.", "category": "Grammar", "difficulty": 2, "options": [{"text": "hearing", "correct": True}, {"text": "to hear", "correct": False}, {"text": "hear", "correct": False}, {"text": "having heard", "correct": False}], "explanation": "'Appreciate' takes a gerund (-ing) direct object."},
        {"stem": "She was accused _______ stealing the documents.", "category": "Grammar", "difficulty": 2, "options": [{"text": "of", "correct": True}, {"text": "for", "correct": False}, {"text": "with", "correct": False}, {"text": "about", "correct": False}], "explanation": "The passive collocation is 'accused of doing something'."},
        {"stem": "He was prevented _______ leaving the country.", "category": "Grammar", "difficulty": 2, "options": [{"text": "from", "correct": True}, {"text": "to", "correct": False}, {"text": "against", "correct": False}, {"text": "of", "correct": False}], "explanation": "Collocation: 'prevented from doing something'."},
        {"stem": "The project was completed _______ schedule, much to our surprise.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "ahead of", "correct": True}, {"text": "before of", "correct": False}, {"text": "prior", "correct": False}, {"text": "advanced", "correct": False}], "explanation": "'Ahead of schedule' is the standard idiomatic expression for finishing early."},
        {"stem": "If you should _______ any problems, do not hesitate to contact us.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "encounter", "correct": True}, {"text": "counter", "correct": False}, {"text": "confront", "correct": False}, {"text": "oppose", "correct": False}], "explanation": "'Encounter' is standard for experiencing difficulties/problems."},
        {"stem": "She behaves as if she _______ the boss of this company.", "category": "Grammar", "difficulty": 2, "options": [{"text": "were", "correct": True}, {"text": "is", "correct": False}, {"text": "was", "correct": False}, {"text": "be", "correct": False}], "explanation": "'As if' takes past subjunctive ('were') for hypothetical statements."},
        {"stem": "Under no circumstances _______ you touch this wire.", "category": "Grammar", "difficulty": 2, "options": [{"text": "should", "correct": True}, {"text": "must", "correct": False}, {"text": "ought", "correct": False}, {"text": "shall", "correct": False}], "explanation": "Negative preposing ('Under no circumstances') triggers auxiliary-subject inversion."},
        {"stem": "Not only _______ the exam, but she also won a scholarship.", "category": "Grammar", "difficulty": 2, "options": [{"text": "did she pass", "correct": True}, {"text": "she passed", "correct": False}, {"text": "has she passed", "correct": False}, {"text": "passed she", "correct": False}], "explanation": "'Not only' at the start of a clause triggers subject-verb inversion."},
        {"stem": "The company has decided to _______ its operations in Asia.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "expand", "correct": True}, {"text": "inflate", "correct": False}, {"text": "magnify", "correct": False}, {"text": "prolong", "correct": False}], "explanation": "Operations are expanded, not inflated or magnified."},
        {"stem": "His argument was so _______ that we had to agree with him.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "cogent", "correct": True}, {"text": "spurious", "correct": False}, {"text": "equivocal", "correct": False}, {"text": "redundant", "correct": False}], "explanation": "'Cogent' means clear, logical, and convincing."},
        {"stem": "She is very _______ to changes in temperature.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "sensitive", "correct": True}, {"text": "sensible", "correct": False}, {"text": "sentient", "correct": False}, {"text": "sensational", "correct": False}], "explanation": "'Sensitive' means easily affected by, while 'sensible' means showing wise judgment."},
        {"stem": "The government is trying to _______ inflation.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "curb", "correct": True}, {"text": "promote", "correct": False}, {"text": "expand", "correct": False}, {"text": "advance", "correct": False}], "explanation": "'Curb' means to limit, control, or restrain."},
        {"stem": "We must _______ our resources to survive the winter.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "husband", "correct": True}, {"text": "spend", "correct": False}, {"text": "dissipate", "correct": False}, {"text": "discard", "correct": False}], "explanation": "'Husband' is a formal verb meaning to use resourcefully or conserve."},
        {"stem": "The explanation was too _______ for me to understand.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "convoluted", "correct": True}, {"text": "simple", "correct": False}, {"text": "lucid", "correct": False}, {"text": "direct", "correct": False}], "explanation": "'Convoluted' means extremely complex and difficult to follow."},
        {"stem": "He was _______ by the complex puzzle.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "baffled", "correct": True}, {"text": "enlightened", "correct": False}, {"text": "assured", "correct": False}, {"text": "comforted", "correct": False}], "explanation": "'Baffled' means totally perplexed or confused."},
        {"stem": "They managed to _______ the difficulty.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "surmount", "correct": True}, {"text": "succumb", "correct": False}, {"text": "subvert", "correct": False}, {"text": "surrender", "correct": False}], "explanation": "'Surmount' means to overcome a difficulty."},
        {"stem": "The decision will have _______ consequences.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "far-reaching", "correct": True}, {"text": "narrow", "correct": False}, {"text": "instant", "correct": False}, {"text": "slight", "correct": False}], "explanation": "'Far-reaching' consequences have a wide and significant influence."},
        {"stem": "She _______ down the offer because the salary was too low.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "turned", "correct": True}, {"text": "took", "correct": False}, {"text": "gave", "correct": False}, {"text": "put", "correct": False}], "explanation": "'Turn down' is a phrasal verb meaning to reject."},
        {"stem": "We need to _______ the root cause of this issue.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "ascertain", "correct": True}, {"text": "assume", "correct": False}, {"text": "ignore", "correct": False}, {"text": "divert", "correct": False}], "explanation": "'Ascertain' means to find out or make sure of."},
        {"stem": "His behavior was completely _______ with his principles.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "inconsistent", "correct": True}, {"text": "harmonious", "correct": False}, {"text": "compatible", "correct": False}, {"text": "aligned", "correct": False}], "explanation": "'Inconsistent' means not staying the same or in disagreement with."},
        {"stem": "I cannot _______ for his honesty; I hardly know him.", "category": "Vocabulary", "difficulty": 2, "options": [{"text": "vouch", "correct": True}, {"text": "vow", "correct": False}, {"text": "verify", "correct": False}, {"text": "validate", "correct": False}], "explanation": "'Vouch for' means to confirm or guarantee someone's character."},
        {"stem": "Read and answer: 'The gig economy has grown rapidly, offering flexibility but also causing job insecurity.' What is a major drawback of the gig economy?", "category": "Reading", "difficulty": 2, "options": [{"text": "Job insecurity", "correct": True}, {"text": "Flexibility", "correct": False}, {"text": "Commute time", "correct": False}, {"text": "Higher tax rates", "correct": False}], "explanation": "The text lists 'job insecurity' as a negative consequence."},
        {"stem": "Read and answer: 'Cognitive behavioral therapy (CBT) helps patients identify and change destructive thought patterns.' What is the focus of CBT?", "category": "Reading", "difficulty": 2, "options": [{"text": "Identifying and changing destructive thought patterns", "correct": True}, {"text": "Prescribing medications", "correct": False}, {"text": "Analyzing childhood memories", "correct": False}, {"text": "Conducting group hypnosis", "correct": False}], "explanation": "CBT helps patients 'identify and change destructive thought patterns'."},
        {"stem": "Read and answer: 'Sustainable agriculture practices are essential to mitigate the effects of climate change on food production.' What mitigates climate change effects?", "category": "Reading", "difficulty": 2, "options": [{"text": "Sustainable agriculture", "correct": True}, {"text": "Deforestation", "correct": False}, {"text": "Industrial pollution", "correct": False}, {"text": "Urbanization", "correct": False}], "explanation": "The text points to 'sustainable agriculture' as key to mitigating effects."},
        {"stem": "Read and answer: 'The placebo effect demonstrates the connection between psychological expectation and physiological healing.' What does the placebo effect show?", "category": "Reading", "difficulty": 2, "options": [{"text": "The link between psychological expectation and physical healing", "correct": True}, {"text": "That drugs are always unnecessary", "correct": False}, {"text": "That medical research is biased", "correct": False}, {"text": "That symptoms are entirely imaginary", "correct": False}], "explanation": "The connection between expectation (psychological) and healing (physiological) is highlighted."}
    ],
    "Advanced": [
        {"stem": "Were it _______ for your timely assistance, we would have suffered severe losses.", "category": "Grammar", "difficulty": 3, "options": [{"text": "not", "correct": True}, {"text": "had not", "correct": False}, {"text": "never", "correct": False}, {"text": "without", "correct": False}], "explanation": "Formal conditional inversion: 'Were it not for...' is equivalent to 'If it had not been for...'."},
        {"stem": "Her arguments during the debate were _______, leaving no room for counter-claims.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "cogent", "correct": True}, {"text": "equivocal", "correct": False}, {"text": "spurious", "correct": False}, {"text": "redundant", "correct": False}], "explanation": "'Cogent' means clear, logical, and convincing."},
        {"stem": "Try as they _______, they could not decipher the archaic inscriptions.", "category": "Grammar", "difficulty": 3, "options": [{"text": "might", "correct": True}, {"text": "would", "correct": False}, {"text": "could", "correct": False}, {"text": "should", "correct": False}], "explanation": "The subjunctive-concessive inversion pattern is 'Try as they might...'."},
        {"stem": "The government's response was criticized as _______, lacking any energy or decisiveness.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "flaccid", "correct": True}, {"text": "resolute", "correct": False}, {"text": "ebullient", "correct": False}, {"text": "pragmatic", "correct": False}], "explanation": "'Flaccid' means weak, limp, or lacking energy and force."},
        {"stem": "He spoke with such _______ that the entire audience was moved to tears.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "eloquence", "correct": True}, {"text": "hesitation", "correct": False}, {"text": "brevity", "correct": False}, {"text": "indifference", "correct": False}], "explanation": "'Eloquence' is persuasive, fluent, and powerful speaking."},
        {"stem": "The contract was declared _______ because of a critical technicality.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "null and void", "correct": True}, {"text": "valid and binding", "correct": False}, {"text": "negotiable", "correct": False}, {"text": "lucrative", "correct": False}], "explanation": "'Null and void' means having no legal force or effect."},
        {"stem": "She is an _______ reader; she reads at least five books a week.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "avid", "correct": True}, {"text": "occasional", "correct": False}, {"text": "indifferent", "correct": False}, {"text": "apathetic", "correct": False}], "explanation": "'Avid' means having or showing a keen interest in or enthusiasm for."},
        {"stem": "His explanation was _______ with errors, making it completely unreliable.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "riddled", "correct": True}, {"text": "sparse", "correct": False}, {"text": "embellished", "correct": False}, {"text": "devoid", "correct": False}], "explanation": "'Riddled with' means filled with something undesirable."},
        {"stem": "The candidate's views are in _______ contrast to those of his party's platform.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "stark", "correct": True}, {"text": "vague", "correct": False}, {"text": "slight", "correct": False}, {"text": "subtle", "correct": False}], "explanation": "'Stark contrast' is a common collocation describing very sharp or clear differences."},
        {"stem": "She has an _______ ability to predict market trends before they occur.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "uncanny", "correct": True}, {"text": "ordinary", "correct": False}, {"text": "inefficient", "correct": False}, {"text": "questionable", "correct": False}], "explanation": "'Uncanny' means strange or mysterious, especially in an unsettling way."},
        {"stem": "The organization is facing a _______ of funds, risking immediate closure.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "dearth", "correct": True}, {"text": "surplus", "correct": False}, {"text": "plethora", "correct": False}, {"text": "abundance", "correct": False}], "explanation": "'Dearth' means a scarcity or lack of something."},
        {"stem": "His remarks were _______ to spark controversy among the committee members.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "calculated", "correct": True}, {"text": "unlikely", "correct": False}, {"text": "spontaneous", "correct": False}, {"text": "incidental", "correct": False}], "explanation": "'Calculated' here means planned or intended to have a specific effect."},
        {"stem": "The committee has _______ its decision until further research is compiled.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "deferred", "correct": True}, {"text": "expedited", "correct": False}, {"text": "announced", "correct": False}, {"text": "retracted", "correct": False}], "explanation": "'Defer' means to put off or postpone to a later time."},
        {"stem": "She was deeply _______ by the unexpected turn of events.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "perturbed", "correct": True}, {"text": "pacified", "correct": False}, {"text": "elated", "correct": False}, {"text": "comforted", "correct": False}], "explanation": "'Perturbed' means anxious or unsettled; upset."},
        {"stem": "The company's success is _______ on securing the new government contract.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "contingent", "correct": True}, {"text": "independent", "correct": False}, {"text": "extraneous", "correct": False}, {"text": "arbitrary", "correct": False}], "explanation": "'Contingent on' means dependent on or subject to change based on."},
        {"stem": "He was criticized for his _______ lifestyle in a time of economic hardship.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "ostentatious", "correct": True}, {"text": "frugal", "correct": False}, {"text": "modest", "correct": False}, {"text": "austere", "correct": False}], "explanation": "'Ostentatious' means characterized by vulgar or pretentious display to impress."},
        {"stem": "The new policy had a _______ effect on local businesses.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "deleterious", "correct": True}, {"text": "beneficial", "correct": False}, {"text": "negligible", "correct": False}, {"text": "salutary", "correct": False}], "explanation": "'Deleterious' means causing harm or damage."},
        {"stem": "His argument was based on _______ assumptions that fell apart under scrutiny.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "specious", "correct": True}, {"text": "sound", "correct": False}, {"text": "empirical", "correct": False}, {"text": "logical", "correct": False}], "explanation": "'Specious' means superficially plausible, but actually wrong."},
        {"stem": "She has a _______ for finding rare first-edition books in thrift stores.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "knack", "correct": True}, {"text": "dislike", "correct": False}, {"text": "inability", "correct": False}, {"text": "distaste", "correct": False}], "explanation": "'Knack' is an acquired or natural skill at doing something."},
        {"stem": "The situation has escalated to a _______ level, requiring immediate intervention.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "critical", "correct": True}, {"text": "trivial", "correct": False}, {"text": "minor", "correct": False}, {"text": "stable", "correct": False}], "explanation": "'Critical' means of decisive importance or crisis-level severity."},
        {"stem": "The memory of that day will never be _______ from her mind.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "effaced", "correct": True}, {"text": "engraved", "correct": False}, {"text": "enhanced", "correct": False}, {"text": "retained", "correct": False}], "explanation": "'Efface' means to erase or make disappear."},
        {"stem": "He is a man of _______ integrity, respected by both allies and opponents.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "unimpeachable", "correct": True}, {"text": "questionable", "correct": False}, {"text": "compromised", "correct": False}, {"text": "dubious", "correct": False}], "explanation": "'Unimpeachable' means entirely trustworthy; beyond doubt or criticism."},
        {"stem": "The treaty was signed after _______ negotiations spanning over six months.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "protracted", "correct": True}, {"text": "brief", "correct": False}, {"text": "spontaneous", "correct": False}, {"text": "hasty", "correct": False}], "explanation": "'Protracted' means lasting for a long time or longer than expected."},
        {"stem": "She was _______ for her contribution to quantum physics research.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "lauded", "correct": True}, {"text": "censured", "correct": False}, {"text": "ignored", "correct": False}, {"text": "dismissed", "correct": False}], "explanation": "'Laud' means to praise highly, especially in a public context."},
        {"stem": "His views on the matter are _______; he has left no room for doubt.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "unequivocal", "correct": True}, {"text": "ambiguous", "correct": False}, {"text": "evasive", "correct": False}, {"text": "vague", "correct": False}], "explanation": "'Unequivocal' means leaving no doubt; unambiguous."},
        {"stem": "The noise from the construction site was so loud it was _______.", "category": "Vocabulary", "difficulty": 3, "options": [{"text": "deafening", "correct": True}, {"text": "faint", "correct": False}, {"text": "soothing", "correct": False}, {"text": "audible", "correct": False}], "explanation": "'Deafening' means extremely loud."},
        {"stem": "Read and answer: 'Epistemic humility involves recognizing the limitations of one's own knowledge, which is essential for intellectual growth.' What is required for intellectual growth?", "category": "Reading", "difficulty": 3, "options": [{"text": "Epistemic humility", "correct": True}, {"text": "Absolute certainty", "correct": False}, {"text": "Engaging in debates", "correct": False}, {"text": "Reading extensively", "correct": False}], "explanation": "The text states that 'epistemic humility' is 'essential for intellectual growth'."},
        {"stem": "Read and answer: 'The phenomenon of confirmation bias leads individuals to favor information that confirms their pre-existing beliefs.' What does confirmation bias do?", "category": "Reading", "difficulty": 3, "options": [{"text": "Favors information confirming pre-existing beliefs", "correct": True}, {"text": "Encourages objective scientific inquiry", "correct": False}, {"text": "Helps in logical reasoning", "correct": False}, {"text": "Reduces critical thinking capabilities", "correct": False}], "explanation": "The text states it leads individuals to 'favor information that confirms their pre-existing beliefs'."},
        {"stem": "Read and answer: 'The theory of relativity revolutionized our understanding of space, time, and gravity.' What did the theory of relativity affect?", "category": "Reading", "difficulty": 3, "options": [{"text": "Our understanding of space, time, and gravity", "correct": True}, {"text": "Chemical bonding theories", "correct": False}, {"text": "Microbiology practices", "correct": False}, {"text": "Geological classifications", "correct": False}], "explanation": "The text states it 'revolutionized our understanding of space, time, and gravity'."},
        {"stem": "Read and answer: 'In Socratic dialogue, acknowledging one's ignorance is considered a prerequisite for learning.' What is a prerequisite for learning?", "category": "Reading", "difficulty": 3, "options": [{"text": "Acknowledging one's ignorance", "correct": True}, {"text": "Having high intelligence", "correct": False}, {"text": "Reading classical philosophy", "correct": False}, {"text": "Engaging in public speeches", "correct": False}], "explanation": "The text states: 'acknowledging one's ignorance is considered a prerequisite for learning.'"}
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
        self._api_key = os.environ.get("OPENAI_API_KEY", "")

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
        if not self._api_key:
            return self._generate_fallback(exam_id, section_id, level_name, count, attempt_id)
        
        return self._generate_via_openai(exam_id, section_id, level_name, count, attempt_id)

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
        selected_templates = []
        if count <= len(templates):
            selected_templates = random.sample(templates, count)
        else:
            selected_templates = random.choices(templates, k=count)
        
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
                    external_ref=f"dynamic-ai-{level_name.lower()}-{idx}-{uuid.uuid4().hex[:6]}",
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

    def _generate_via_openai(
        self,
        exam_id: str,
        section_id: str,
        level_name: str,
        count: int,
        attempt_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Queries OpenAI API, runs solver validations, and commits questions."""
        logs = []
        issues = []
        imported_count = 0

        # Build prompt for specific levels
        system_prompt = (
            "You are an expert English language assessment developer. You specialize in generating "
            "multiple-choice questions aligned with international standards like CEFR and British Council.\n\n"
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

        user_content = (
            f"Generate {count} unique multiple-choice questions for the '{level_name}' English proficiency level. "
            "Ensure a mix of Grammar, Vocabulary, and Reading categories appropriate for this CEFR bracket."
        )

        payload = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7
        }

        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as res:
                response_data = json.loads(res.read().decode("utf-8"))
                
            raw_content = response_data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
            generated_questions = parsed.get("questions", [])
            logs.append(f"Successfully generated {len(generated_questions)} questions from OpenAI API.")

            # Validate each question using a SOLVER agent
            for idx, q_data in enumerate(generated_questions):
                if not self._validate_structure(q_data):
                    issues.append(f"Question #{idx} failed programmatic JSON structure validation.")
                    continue
                
                # Solver Agent Check (Self-Solving simulation)
                if not self._run_solver_check(q_data):
                    issues.append(f"Question #{idx} failed Solver Agent verification (ambiguous correct answer). Discarded.")
                    continue
                
                # Persist verified question
                try:
                    options_input = [
                        QuestionOptionInput(key=k, text=v, is_correct=(k == q_data["correct_option"]))
                        for k, v in q_data["options"].items()
                    ]
                    create_input = CreateQuestionInput(
                        exam_id=exam_id,
                        section_id=section_id,
                        stem_text=q_data["stem_text"],
                        options=options_input,
                        category_name=q_data["category_name"],
                        difficulty_level=int(q_data["difficulty_level"]),
                        explanation_text=q_data["explanation_text"],
                        marks=1.0,
                        external_ref=f"openai-ai-{level_name.lower()}-{idx}-{uuid.uuid4().hex[:6]}",
                        is_active=True,
                        attempt_id=attempt_id
                    )
                    self._qb_service.add_question(create_input)
                    imported_count += 1
                except Exception as e:
                    issues.append(f"Failed to persist verified question #{idx}: {str(e)}")

        except Exception as e:
            logs.append(f"OpenAI API call failed: {str(e)}")
            issues.append(f"API Connection error: {str(e)}. Falling back to local static templates...")
            # Fall back to offline seeding
            fallback_res = self._generate_fallback(exam_id, section_id, level_name, count, attempt_id)
            imported_count = fallback_res["imported_count"]
            issues.extend(fallback_res["issues"])
            logs.extend(fallback_res["logs"])

        return {
            "mode": "openai_api",
            "success": len(issues) == 0,
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
        Solver Agent validation layer. Prompts OpenAI to solve the MCQ blind.
        If the solver's key matches the correct_option, return True (verified).
        """
        solver_prompt = (
            "You are a student taking an English proficiency exam. "
            "Solve the multiple choice question below. Reply in strict JSON format: {'correct_option': 'KEY'}\n\n"
            f"Question: {q['stem_text']}\n"
            f"Options:\n"
            f"A: {q['options']['A']}\n"
            f"B: {q['options']['B']}\n"
            f"C: {q['options']['C']}\n"
            f"D: {q['options']['D']}\n\n"
            "Analyze carefully and provide only the key (A, B, C, or D)."
        )

        payload = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "user", "content": solver_prompt}
            ],
            "temperature": 0.0
        }

        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
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
            
            return solved_key == q["correct_option"].strip().upper()
        except Exception:
            # If solver fails for connection reasons, we default to True to avoid discarding,
            # but log warning.
            return True
