# ITACPC teams registration

Ensure that:

1. you have Python 3.11 installed.
2. you have [pipenv](https://docs.pipenv.org/en/latest/) installed.

Then you can proceed.

## Project setup

You need to do this only the first time:

### Install dependencies

```
pipenv install
```

### Initialize the DB

```
python3 manage.py migrate
python3 manage.py loaddata universities
python3 manage.py createsuperuser
```

## Running the project

You need to do this everytime:

### Access your virtual shell

```
pipenv shell
```

### Run the development app

```
python3 manage.py runserver
```
