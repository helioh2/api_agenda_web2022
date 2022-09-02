# EXECUTAR SOMENTE NO GIT BASH OU TERMINAL DO LINUX

export FLASK_APP=index
export FLASK_ENV=development
export DB_HOST=localhost
export DB_USER=postgres
export DB_PASSWORD=root
export DB_PORT=5432
export DB_NAME=agenda
flask db migrate
flask db upgrade
