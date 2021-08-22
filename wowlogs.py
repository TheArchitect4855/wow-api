import requests
import time

WARCRAFT_TOKEN = "https://www.warcraftlogs.com/oauth/token"
WARCRAFT_API = "https://www.warcraftlogs.com/api/v2/client"

REGION_IDS = {
	"US": 1,
	"EU": 2,
	"KR": 3,
	"TW": 4,
	"CN": 5
}

class CharacterInfo:
	def __init__(self, name, class_name, realm, guilds, region, best_perf_avg, median_perf_avg):
		self.name = name
		self.class_name = class_name
		self.realm = realm
		self.guilds = guilds
		self.region = region
		self.best_perf_avg = best_perf_avg
		self.median_perf_avg = median_perf_avg

	def __str__(self):
		return """
{}, {} - {}
Best Performance Average: {}%
Median Performance Average: {}%
Guilds:
{}
Region: {}
		""".format(self.name, self.class_name, self.realm, round(self.best_perf_avg), round(self.median_perf_avg), self.guilds, self.region).strip()

class WoWLogs:
	def __init__(self, client_id: str, client_token: str):
		self.client_id = client_id.strip()
		self.client_token = client_token.strip()
		self.expiry = 0

	def authenticate(self) -> bool:
		payload = { "grant_type": "client_credentials" }
		res = requests.post(WARCRAFT_TOKEN, data = payload, auth = (self.client_id, self.client_token))

		if res.status_code == 200: #OK
			info = res.json()
			self.expiry = int(time.time()) + info["expires_in"]
			
			access_token = info["access_token"]
			self.auth_headers = { "Authorization": "Bearer {}".format(access_token) }

			return True
		else:
			self.expiry = 0
			print("Authentication failed.")
			return False
			
	def query(self, q: str) -> dict:
		if time.time() > self.expiry:
			if not self.authenticate():
				return None

		payload = {
			"query": q
		}

		res = requests.post(WARCRAFT_API, data = payload, headers = self.auth_headers)

		if res.status_code == 200: #OK
			json = res.json()
			data = json.get("data", None)
			if data == None or "errors" in json.keys():
				print(json)
			return data
		else:
			print("Query returned status {}".format(res.status_code))
			return None
	
	def get_character_info(self, character_name: str, region: str, realm: str) -> CharacterInfo:
		region_id = self.get_region_id(region)
		if region_id == None:
			print("Failed to get region ID.")
			return None

		server_slug = self.get_server_slug(region_id, realm)
		if server_slug == None:
			return None

		character_stats = self.get_character_stats(character_name, region, server_slug)
		if character_stats == None:
			return None

		class_name = self.get_class_name(character_stats["class_id"])
		if class_name == None:
			return None

		return CharacterInfo(character_name, class_name, realm, character_stats["guild_names"], region, character_stats["best_perf_avg"], character_stats["median_perf_avg"])

	def get_region_id(self, slug: str) -> int:
		return REGION_IDS.get(slug.strip(), None)
	
	def get_server_slug(self, region_id: int, server_name: str, page: int = 1) -> str:
		q = """
			{
				worldData {
					region(id: %d) {
						servers(page: %d) {
							data {
								name,
								slug
							}
						}
					}
				}
			}
		""" % (region_id, page)
		res = self.query(q)
		
		if res == None:
			return None
		
		servers = res["worldData"]["region"]["servers"]["data"]

		if len(servers) == 0:
			print("Server not found.")
			return None

		for server in servers:
			if server["name"] == server_name.strip():
				print("Found server slug on page {}".format(page))
				return server["slug"]
		
		return self.get_server_slug(region_id, server_name, page + 1)
	
	def get_character_stats(self, character_name: str, region_slug: str, server_slug: str) -> dict:
		q = """
			{
				characterData {
					character(name: "%s", serverRegion: "%s", serverSlug: "%s") {
						classID,
						guilds {
							name
						},
						zoneRankings
					}
				}
			}
		""" % (character_name.strip(), region_slug.strip(), server_slug.strip())
		res = self.query(q)

		if res == None:
			return None
		
		character = res["characterData"]["character"]
		if character == None:
			return None

		class_id = character["classID"]

		guild_names = []
		for guild in character["guilds"]:
			guild_names.append(guild["name"])
		
		zone_rankings = character["zoneRankings"]
		best_perf_average = zone_rankings["bestPerformanceAverage"]
		median_perf_average = zone_rankings["medianPerformanceAverage"]

		return {
			"class_id": class_id,
			"guild_names": guild_names,
			"best_perf_avg": best_perf_average,
			"median_perf_avg": median_perf_average
		}
	
	def get_class_name(self, class_id: int) -> str:
		q = """
			{
				gameData {
					class(id: %d) {
						name
					}
				}
			}
		""" % class_id
		res = self.query(q)

		if res == None:
			return None
		else:
			return res["gameData"]["class"]["name"]
