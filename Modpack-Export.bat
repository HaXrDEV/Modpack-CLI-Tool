@echo off
python -m venv env
source ./env/bin/activate

pip install -r requirements.txt

python ./Modpack-Export.py
pause