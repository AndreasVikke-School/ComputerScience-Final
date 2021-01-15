import os
import sys
import shutil
import json
from ruamel.yaml import YAML

os.chdir("sls")

name = sys.argv[1]
functions = sys.argv[2].split(',')
step = True == (sys.argv[3] if len(sys.argv) == 4 else True)

packages = {
    'serverless-plugin-ifelse',
    'serverless-python-requirements',
    'serverless-step-functions'
}

if os.path.isfile('package.json'):
    with open('package.json') as package:
        installed = json.load(package)['devDependencies']
        print('Installed packages:', installed)

        for package in packages:
            if package not in installed:
                print('Installing', package)
                os.system("sls plugin install -n {0}".format(package))
else:
    os.system("sls plugin install -n serverless-plugin-ifelse")
    os.system("sls plugin install -n serverless-python-requirements")
    os.system("sls plugin install -n serverless-step-functions")

if os.path.isdir("target"):
    shutil.rmtree('target')

yaml = YAML()
yaml.preserve_quotes = True

with open("serverless.yaml", 'r') as stream:
    data_loaded = yaml.load(stream)
    if step:
        data_loaded.pop('stepFunctions')

    delete = []
    for function in data_loaded['functions']:
        if function not in functions:
            delete.append(function)

    for d in delete:
        data_loaded['functions'].pop(d)

    shutil.copyfile('serverless.yaml', 'serverless-old.yaml')

    with open('serverless.yaml', 'w') as stream:
        yaml.dump(data_loaded, stream)

os.system("sls package --stage {0} --package target/{0} -v -r eu-central-1".format(name))
os.system("sls deploy --stage {0} --package target/{0} -v -r eu-central-1".format(name))

os.remove('serverless.yaml')
shutil.copyfile('serverless-old.yaml', 'serverless.yaml')
os.remove('serverless-old.yaml')
