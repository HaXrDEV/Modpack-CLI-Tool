@echo off
pip install gitpython
python ./run.py

cd ./Modpack-CLI-Tool
python -m venv env
source ./env/bin/activate
pip install -r ./requirements.txt
python ./Modpack-Export.py
pause