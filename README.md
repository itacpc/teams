# ITACPC teams registration

Firstly, ensure you have Python 3.7 installed.

Secondly, ensure you have [pipenv](https://docs.pipenv.org/en/latest/) installed.

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

### Create a secret.py file

With a content similar to: (but not exactly this!)

```
secret = b'qwertyuiop123456789'
```

### Run the flask app

```
FLASK_APP=teams.py FLASK_ENV=development flask run --host=0.0.0.0
```
