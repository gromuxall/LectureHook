#!/bin/bash

cd LectureHook/app
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
deactivate

chmod 755 run.sh
chmod 755 lhook_app.py

echo "alias lecturehook='${PWD}/run.sh'" >> ~/.bashrc
