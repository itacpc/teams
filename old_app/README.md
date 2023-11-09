# ITACPC teams registration

Ensure that:

1. you have Python 3.7 installed.
2. you have [pipenv](https://docs.pipenv.org/en/latest/) installed.
3. you have a PostgreSQL user and database set up in your machine (you can follow [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

Then you can proceed.

## Project setup

You need to do this only the first time:

### Install dependencies

```
pipenv install
```

### Initialize the DB

```
psql databasename < schema.sql
```

### Create a config.py file

Copy the file `config_example.py` file in a file named `config.py`
and edit the required parameters as documented.

## Running the project

You need to do this everytime:

### Access your virtual shell

```
pipenv shell
```

### Run the flask app

```
FLASK_APP=teams.py FLASK_ENV=development flask run --host=0.0.0.0
```
