# Steps for deployment

1. Create droplet on Digitalocean, specifying to use your SSH key at creation time (so it gets added in the root account automatically).
2. Open the console (via browser) logged in as root:
    1. `useradd itacpc`
    2. `adduser itacpc sudo`
    3. Copy the right key from `/root/.ssh/authorized_keys` into `/home/itacpc/.ssh/authorized_keys`
3. Close the browser console
4. Create a section in your laptop's `~.ssh/config` file such as the following
    ```
    Host teams
      User itacpc
      Hostname IP_ADDRESS_OR_DOMAIN_HERE
      IdentityFile ~/.ssh/your_chosen_key_rsa
    ```
5. Log in from a normal terminal with `ssh teams`
6. Update ubuntu `sudo apt update && sudo apt upgrade`
7. Run `sudo apt install pipenv git nginx certbot`
8. Clone this repository `git clone git@github.com:itacpc/teams.git`
9. Enter the repository and create the pipenv `pipenv install`
10. Copy the nginx configuration `sudo cp nginx/itacpc /etc/nginx/sites-available/`
11. Enable the nginx configuration `sudo ln -s /etc/nginx/sites-available/itacpc /etc/nginx/sites-enabled/itacpc`
12. Update the systemd configuration in `systemd/gunicorn.service` with the correct Python virtual environment path.
13. Copy the systemd configuration `sudo cp systemd/* /etc/systemd/system/`
14. Enable the systemd configuration `sudo systemctl enable gunicorn --now`
15. Run certbot to fix HTTPS stuff: `sudo certbot`
