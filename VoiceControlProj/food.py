#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo of the Google Assistant GRPC recognizer."""

'''
This class instantiates foodProcessor to get foods, allergens, and nutrients from the user's text. 
It then uses foodLog to log the information onto the Google Spreadsheet. 
'''

import foodProcessor
import foodLog
import logging
import json
import aiy.assistant.grpc
import aiy.audio
import aiy.voicehat
from datetime import datetime
from pytz import timezone
import httplib2
import urllib.parse
import urllib.request
import oauth2client
from oauth2client.file import Storage
from googleapiclient.discovery import build
import sys
import requests

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


def main():

    '''
    "id" and "key" are used to make requests to the Edamam Food API
    and they are obtained by registering for an account from Edamam.
    '''
    id = '5ce56395'
    key = 'da9676a9e9fefcbb46be59b59f20bf80'
    
    assistant = aiy.assistant.grpc.get_assistant()
    with aiy.audio.get_recorder():
         aiy.audio.say('What food did you eat today?', lang="en-US")
         print('Listening...')
         text, audio = assistant.recognize()
         if text:
             # find date and time
             cupertino = timezone('US/Pacific')
             now = datetime.now(cupertino)
             date = now.strftime("%B %d, %Y")
             time = now.strftime("%I:%M %p")
             text2 = text.replace("I", "You") + ' on ' + date + ' at ' + time
             aiy.audio.say(text2, lang="en-US")

             rawText = text

             # Instantiate foodProcessor
             processor = foodProcessor.foodProcessor(key,id)

             '''
             Get list of foods, foodURIs, and measureURIs for each food.
             foodURIs and measureURIs are used to get the nutrients of each food.
             '''
             foods, foodURIs, measureURIs = processor.getFoodList(rawText)
             
             # Get allergens and nutrients from all foods
             details = processor.getFoodDetails(foodURIs, measureURIs)
             
             # Instantiate foodLog
             flog = foodLog.foodLog()

             allergens = []
             nutrientsToLog = ["Energy", "Fat", "Carbs", "Fiber", "Sugars", "Protein", "Sodium", "Calcium", "Magnesium", "Potassium", "Iron", "Vitamin C", "Vitamin E", "Vitamin K"]
             
             # nutrients contains the values for each nutrient
             nutrients = {"Energy": [], "Fat": [], "Carbs": [], "Fiber": [], "Sugars": [], "Protein": [], "Sodium": [], "Calcium": [], "Magnesium": [], "Potassium": [], "Iron": [], "Vitamin C": [], "Vitamin E": [], "Vitamin K": []}

             for food in details:
                 allergens.append(food["allergens"])
                 for nutrient in nutrients:
                    nutrients[nutrient].append(food["nutrients"][nutrient])

             algs = formatAllergens(allergens)

             credentials = flog.sheet_oauth()

             toLog = ["date", "time", "text", "food", "allergens_log", "nutrients"]
             # input stores the information that must be logged
             input = {"date": date, "time": time, "text": rawText, "food": foods, "allergens_log": algs, "nutrients": nutrients}
             
             # ip contains the final values that will be appended onto the Google Spreadsheet
             ip = []
             for key in toLog:
                if key == "date" or key == "time" or key == "text" or key == "allergens_log":
                   ip.append(input[key])
                elif key == "food":
                   foos = []
                   for foo in input["food"]:
                      foos.append(foo)
                   ip.append('\n'.join(foos))
                else:
                   for nutrient in nutrientsToLog:
                      quantities = []
                        
                      # find total values for each nutrient
                      total = 0
                      for quantity in nutrients[nutrient]:
                         total += float(quantity)
                         quantities.append(str(quantity))
                      tot = "Total: " + str(total)
                      quantities.append(tot)
                      ip.append('\n'.join(quantities))

             payload = {"values": [ip]}
             flog.write_to_sheet(credentials, '1GxFpWhwISzni7DWviFzH500k9eFONpSGQ8uJ0-kBKY4', payload)

def formatAllergens(allergens):
    '''
    Insert new line between each food’s allergens.
	Return formatted allergens.
    '''
    algs = ''
    for i in range(len(allergens)):
        for j in range(len(allergens[i])):
            if j == len(allergens[i]) - 1:
                algs += allergens[i][j]
            else:
                algs += allergens[i][j]
                algs += ', '
        algs += '\n'
    return algs

if __name__ == '__main__':
    main()
