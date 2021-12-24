import yaml

constants = {}

with open('config.yml', 'r') as config:
    data = yaml.full_load(config)
    for header in data.items():
        for key, value in header[1].items():
            constants[key] = value

host = constants['host']
user = constants['user']
password = constants['password']
root = constants['root']
directory = constants['directory']
timeout = constants['timeout']
flag = constants['flag']