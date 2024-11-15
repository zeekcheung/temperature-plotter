MAIN_SCRIPT := main.py
MOCK_SCRIPT := mock.py

PYTHON := python3

PYINSTALLER := pyinstaller
PYINSTALLER_OPTS := --onefile --distpath . --hidden-import=PIL._tkinter_finder

PROGRAM_NAME := 可控温度变化监控系统.exe

all: backup package clean compress

run:
	$(PYTHON) $(MAIN_SCRIPT)

mock:
	$(PYTHON) $(MOCK_SCRIPT)

package:
	$(PYINSTALLER) $(PYINSTALLER_OPTS) --name $(PROGRAM_NAME) $(MAIN_SCRIPT)

clean:
	rm -rf build dist $(PROGRAM_NAME).spec .git .gitignore

backup:
	cp -r $$(pwd) $$(pwd).bak

compress:
	zip -r $$(pwd).zip $$(pwd)
