#!/usr/bin/python
import argparse
import logging
import time
import sys
import operator
from collections import Counter
from custom_exceptions import GeneralPogoException

from api import PokeAuthSession
from location import Location

from pokedex import pokedex
from inventory import items

def setupLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

## Mass remove pokemon. It first displays the "Safe" numbers of pokemon that can be released, then makes sure you want to release them
def massRemove(session):
	party = session.checkInventory().party
	myParty = []
	
	# Get the stats for all the pokemon in the party. Easier to store and nicer to display.
	for pokemon in party:
		IvPercent = ((pokemon.individual_attack + pokemon.individual_defense + pokemon.individual_stamina)*100)/45
		L = [pokedex[pokemon.pokemon_id],pokemon.cp,pokemon.individual_attack,pokemon.individual_defense,pokemon.individual_stamina,IvPercent,pokemon]
		myParty.append(L)
	
	# Sort the list by name and then IV percent
	myParty.sort(key = operator.itemgetter(0, 5))
	
	safeIV = int(raw_input('\nWhat is your IV cut off? (Pokemon above this will be safe from transfer): '))
	safeCP = int(raw_input('What is your CP cut off? (Pokemon above this will be safe from transfer): '))
	
	# Create a "safe" party by removing good IVs and high CPs
	safeParty = [item for item in myParty if item[5] < safeIV and item[1] < safeCP]
	
	# Ask user which pokemon they want. This must be CAPITALS.
	userPokemon = raw_input("\nWhich pokemon do you want to transfer?: ")
	
	# Show user all the "safe to remove" pokemon
	refinedMonsters = []
	print '\n'
	for monster in safeParty:
		if monster[0] == userPokemon:
			if monster[5] > 74:
				logging.info('\033[1;32;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
			elif monster[5] > 49:
				logging.info('\033[1;33;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
			else:
				logging.info('\033[1;37;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
			refinedMonsters.append(monster)
	
	# If they can't "safely" remove any pokemon, then send them to the main menu again
	if len(refinedMonsters) < 1:
		print "\nCannot safely transfer any Pokemon of this type. IVs or CP are too high."
		mainMenu(session)
	
	logging.info('\nCan safely remove %s of this Pokemon',len(refinedMonsters))
	
	# Ask how many they want to remove
	userNumber = int(raw_input("How many do you want to remove?: "))
	
	if userNumber == 0:
		mainMenu(session)
	
	# Show the pokemon that are going to be removed to confirm to user
	print '\n'
	i = 0
	monstersToRelease = []
	for monster in refinedMonsters:
		if monster[0] == userPokemon and i < int(userNumber):
			i = i + 1
			if monster[5] > 74:
				logging.info('\033[1;32;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
			elif monster[5] > 49:
				logging.info('\033[1;33;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
			else:
				logging.info('\033[1;37;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
			monstersToRelease.append(monster)
	
	# Double check they are okay to remove
	if int(userNumber) > len(refinedMonsters):
		logging.info('\nThis will transfer %s of this Pokemon',len(refinedMonsters))
	else:
		logging.info('\nThis will transfer %s of this Pokemon',userNumber)
	okayToProceed = raw_input('Do you want to transfer these Pokemon? (y/n): ')
	
	# Remove the pokemon!
	if okayToProceed == 'y':
		for monster in monstersToRelease:
			session.releasePokemon(monster[6])
			time.sleep(1)
	
	# Go back to the main menu
	mainMenu(session)
	
def viewPokemon(session):
	party = session.checkInventory().party
	myParty = []
	
	# Get the party and put it into a nicer list
	for pokemon in party:
		IvPercent = ((pokemon.individual_attack + pokemon.individual_defense + pokemon.individual_stamina)*100)/45
		L = [pokedex[pokemon.pokemon_id],pokemon.cp,pokemon.individual_attack,pokemon.individual_defense,pokemon.individual_stamina,IvPercent,pokemon]
		myParty.append(L)
	
	# Sort party by name and then IV percentage	
	myParty.sort(key = operator.itemgetter(0, 5))
	
	# Display the pokemon, with color coding for IVs and separation between types of pokemon
	i = 0
	for monster in myParty:
		if i > 0:
			if myParty[i][0] != myParty[i-1][0]:
				print '---------------- | ----- | --- | --- | --- | ----'
		if monster[5] > 74:
			logging.info('\033[1;32;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
		elif monster[5] > 49:
			logging.info('\033[1;33;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
		else:
			logging.info('\033[1;37;40m %-15s | %-5s | %-3s | %-3s | %-3s | %-3s \033[0m',monster[0],monster[1],monster[2],monster[3],monster[4],monster[5])
		i = i+1

	mainMenu(session)
	
def mainMenu(session):
	print '\n\n'
	print '1: View Pokemon'
	print '2: Transfer Pokemon'
	print '3: Exit'
	
	menuChoice = int(raw_input("\nEnter choice: "))
	if menuChoice == 1: viewPokemon(session)
	elif menuChoice == 2: massRemove(session)
	elif menuChoice == 3: quit()
	else: quit()
		
		
# Entry point
# Start off authentication and demo
if __name__ == '__main__':
    setupLogger()
    logging.debug('Logger set up')

    # Read in args
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", help="Auth Service", required=True)
    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)
    parser.add_argument("-l", "--location", help="Location", required=True)
    parser.add_argument("-g", "--geo_key", help="GEO API Secret")
    args = parser.parse_args()

    # Check service
    if args.auth not in ['ptc', 'google']:
        logging.error('Invalid auth service {}'.format(args.auth))
        sys.exit(-1)

    # Create PokoAuthObject
    poko_session = PokeAuthSession(
        args.username,
        args.password,
        args.auth,
        geo_key=args.geo_key
    )

    # Authenticate with a given location
    # Location is not inherent in authentication
    # But is important to session
    session = poko_session.authenticate(args.location)

    # Time to show off what we can do
    if session:
	
		mainMenu(session)

    else:
        logging.critical('Session not created successfully')