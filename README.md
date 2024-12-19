﻿# packto.ai

Instructions:
Make an account for docker and download docker desktop and wireshark
Docker Desktop: https://www.docker.com/products/docker-desktop/
Wireshark: https://www.wireshark.org/download.html

Go to your terminal (cmd, powershell, or VSCode, bash, whatever you prefer), use cd to go to whatever directory you want this project to live and type this command if you have an ssh key:
git clone https://github.com/TAJ-32/packto.ai.git

This should create a folder called packto.ai on your computer. Open it up by typing cd packto.ai.

Type ls. It should show all the files from the project directory on github. If it does, do the following:

Open Docker Desktop (sometimes this can be slow so restart your computer if it isn't working)
in the terminal where you have packto.ai open, type:
docker-compose up --build

YOU ONLY HAVE TO DO THIS COMMAND THE FIRST TIME YOU START UP THE APP


Open up the app in your web browser at localhost:8009

When you want to close the app, type ctrl + C into your terminal and then type docker-compose down.

When you want to open it again, type docker-compose up and open that app at localhost:8009

If you have any questions, please post them on our discord!

