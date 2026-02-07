@echo off
cd /d %~dp0
py utils\print_banner.py
echo.
if not exist venv\Scripts\activate (
	echo -> Virtualenv not found. Creating venv... 1/4
	python -m venv venv
	echo -> Ativando virtualenv e instalando dependências... 2/4
	call venv\Scripts\activate
	if exist requirements.txt (
		echo Atualizando pip... 3/4
		python -m pip install --upgrade pip
		echo Installing requirements... 4/4
		pip install -r requirements.txt
	)
	echo -> Virtualenv criado.
) else (
	echo -> Virtualenv encontrado.
)
cls 
py utils\print_banner.py
echo.
start "Cookie Monster API" cmd /k "call venv\Scripts\activate && python app.py"
pause
