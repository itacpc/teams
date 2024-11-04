bind = "unix:/run/gunicorn.sock"
workers = 3

accesslog = "gunicorn.access.log"
errorlog = "gunicorn.error.log"

# Whether to send Django output to the error log 
capture_output = True
# How verbose the Gunicorn error logs should be (debug, info, warning, error, critical)
loglevel = "info"
