import json
from env import AIDEV3_API
import requests

url = 'https: // centrala.ag3nts.org/data/{AIDEV3_API}/cenzura.txt'
data = requests.get(url)
