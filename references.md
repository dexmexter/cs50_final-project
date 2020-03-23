# References

Here is a list of references and code that I used to help build this app. This is primarily for places where I used code snippets, I am not including links that helped me answer small problems.

- This github repo is where I got the code for the [sudoku puzzle logic](https://github.com/JoeKarlsson/puthon-sudoku-generator-solver)
    - I stripped out everything except for the main sudoku.py file. I edited a few of the functions and added two additional functions to convert puzzles to strings and back
- This stackoverflow answer provided the css I used to [display puzzles](https://stackoverflow.com/questions/19697033/styling-a-sudoku-grid)


### Server Setup
I decided to configure my own server to host the app inside my local network. I installed [ubuntu server](https://ubuntu.com/download/server) in a VM on [proxmox virtual environment](https://proxmox.com/en/). To configure the server I had to set up the following:

- [Static IP](https://linuxize.com/post/how-to-configure-static-ip-address-on-ubuntu-18-04/) and [SSH keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804) for ease of access and so that I can log onto the server to edit the code
- [Apache and PHP](https://www.digitalocean.com/community/tutorials/hot-to-install-linux-apache-mysql-php-lamp-stack-ubuntu-18-04) for serving the files
- [Python venv](https://docs.python.org/3/library/venv.html) for managing python projects following best practices.
