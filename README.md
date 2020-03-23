# cs50_final-project
My final project for Harvard's CS50 course.

The project is a web application for playing Sudoku games. The front-end of the project is the place where a user can create and play sudoku puzzles. I also used this project as an opportunity to build out the back-end server that runs the project on my home network. I will include a document with some references to the various projects I used but starting from the ground up, here are the technologies that I am utilizing for this project:

- Proxmox (linux distro for managing cluster nodes and virtual machines)
- Ubuntu server (operating system where the app is run from)
- SSH (for communicating with the server)
- Git and Github (for source-control)
- Apache (web server application for displaying the content)
- sqlite3 (database)
- php (required by phpliteadmin)
- phpliteadmin (web based management of the sqlite database)
- Python (language the app is written in)
- Pip (managing Python dependencies)
- Flask (Framework for building python applications)
- Sudoku library (a collection of functions for generating and checking sudoku puzzles)
- Bootstrap (for managing the design of the front-end)

The way the app works from the users point-of-view is that they first need to register an account. With an account registered the user can login. The homepage offers a list of pages for what the user might want to do. The first thing they should do is create a new puzzle to play. There are several difficulty levels to choose from. They can then start filling out the puzzle. Changes to the puzzle can be saved by submitting with a button below the puzzle. Whenever a puzzle is submitted it is also checked for completion. When a puzzle has been solved, the user will be notified and the finish time will be saved. Any number of puzzles can be created and worked on. All puzzles can be viewed in a historical list.

The base of the progect is the same as the CS50 Finance application. I stripped out all the finance code that I no longer wished to use and created new pages for the app I wished to make.
