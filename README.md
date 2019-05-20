# ITACPC teams registration

Firstly, ensure you have Python 3.7 installed.

Secondly, ensure you have [pipenv](https://docs.pipenv.org/en/latest/) installed.

Then you can proceed.

### Initialize the DB

You need to run this only the first time:

```
python -c 'from teams import init_db; init_db()'
```

### Running the flask app

```
FLASK_APP=teams.py FLASK_ENV=development flask run --host=0.0.0.0
```
