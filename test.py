from wowlogs import WoWLogs
import time

# Load client ID and token
keys = None
with open(".keys", "r") as file:
	keys = file.readlines()

running = True
while running:
	character_name = input("Enter character name: ")
	region_name = input("Enter region: ")
	realm_name = input("Enter realm: ")

	now = time.time()

	# Create API
	api = WoWLogs(keys[0], keys[1])
	character_info = api.get_character_info(character_name, region_name, realm_name)
	print(character_info)

	elapsed = time.time() - now
	print("Took {}s to fetch character data.".format(elapsed))

	running = input("Run again? (y)es/(N)O\n") == "y"
