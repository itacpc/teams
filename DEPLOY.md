# Steps for deployment

1. Create droplet on Digitalocean, specifying to use your SSH key at creation time (so it gets added in the root account automatically).
1. Update the `teams` DNS record on Cloudflare so that `teams.itacpc.it` points to the IP address of the newly created droplet.
1. Create a new CNAME record for the year-specific subdomain (e.g. `teamsXX`) which points to `teams.itacpc.it`.
1. Delete the CNAME record for the previous year.
1. Open the console (via browser) logged in as root:
    1. `useradd itacpc`.
    1. `adduser itacpc sudo`.
    1. Copy the right key from `/root/.ssh/authorized_keys` into `/home/itacpc/.ssh/authorized_keys`.
1. Close the browser console.
1. Create a section in your laptop's `~.ssh/config` file such as the following:
    ```
    Host teams
      User itacpc
      Hostname teamsXX.itacpc.it
      IdentityFile ~/.ssh/your_chosen_key_rsa
    ```
1. Log in from a normal terminal with `ssh teams`.
1. Update ubuntu `sudo apt update && sudo apt upgrade`.
1. Run `sudo apt install pipenv git postgresql nginx certbot`.
1. Clone this repository `git clone git@github.com:itacpc/teams.git`.
1. Enter the repository and create the pipenv `pipenv install`.
1. Log in as `postgres` by running `sudo su - postgres`, then:
    1. Create DB user `itacpc`, with password `itacpc`, by running: `createuser -P itacpc` and passing `itacpc` in the password field.
    1. Create DB `itacpc` owned by user `itacpc`, by running: `createdb itacpc -O itacpc`.
    1. Exit back to the previous shell.
1. TODO: add production `.env` file, initialize universities, create superuser.
1. Update the systemd configuration in `systemd/gunicorn.service` with the correct Python virtual environment path.
1. Copy the systemd configuration `sudo cp systemd/* /etc/systemd/system/`.
1. Enable the systemd configuration `sudo systemctl enable gunicorn --now`.
1. Copy the nginx configuration `sudo cp nginx/itacpc /etc/nginx/sites-available/`.
1. Disable the default nginx configuration `sudo rm /etc/nginx/sites-enabled/default`.
1. Enable the new nginx configuration `sudo ln -s /etc/nginx/sites-available/itacpc /etc/nginx/sites-enabled/itacpc`.
1. Run certbot to fix HTTPS stuff: `sudo certbot`.
