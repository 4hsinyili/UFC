import configparser
from Crawlers import utils


config = configparser.ConfigParser()

config.read('crawler.conf')
print(config['Food_Panda_Api_Url']['list_url'])

headers = utils.read_json('headers_ue.json')

print(type(headers))


print((0 > False))
