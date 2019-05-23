# ITACPC teams registration

Firstly, ensure you have Python 3.7 installed.

Secondly, ensure you have [pipenv](https://docs.pipenv.org/en/latest/) installed.

Thirdly, ensure you have a PostgreSQL user and database set up in your machine (you can follow [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

Then you can proceed.

### Install dependencies

```
pipenv install
```

### Access your virtual shell

```
pipenv shell
```

### Initialize the DB

You need to run this only the first time:

```
psql databasename < schema.sql
```

### Create a config.py file

Copy the file `config_example.py` file in a file named `config.py` 
and edit the required parameters as documented. 

### Run the flask app

```
FLASK_APP=teams.py FLASK_ENV=development flask run --host=0.0.0.0
```
