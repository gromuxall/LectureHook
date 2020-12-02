#!/bin/bash

cd LectureHook/app
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
deactivate

chmod 755 lhook_app.py

exec 3<> run.sh

echo "#!/bin/bash" >&3
echo "" >&3
echo "source ${PWD}/env/bin/activate " >&3
echo "python3 ${PWD}/lhook_app.py" >&3
echo "deactivate" >&3

exec 3>&-

chmod 755 run.sh

echo "alias lecturehook='${PWD}/run.sh'" >> ~/.bashrc
