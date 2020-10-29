Pierre GIRAUD - Richard DROGO - Cédric GORMOND - Arnaud TAVERNIER - Audric MERLEY


# Project LAB3 TEAM 8

 
## Context

The project is to create a server on an AWS instance and communicate with a client on our computer. The processes that the server can do are:

- Analyse a set of number and send results (mean, min, max , median)
- Image processing with threshold and grey scale on image

In both cases, the server will upload log on a bucket and the modified images for the image processing.

For this project, we try to make it automatic for every step.

The steps are the creation/use of an AWS instance, the installation of the python libraries on the server, the configuration of the AWS-cli on the server and the launching of this server script (called servor\_sqs.py).

We successfully did it except for one thing: when configurating the AWS-cli on the server, the program needs to ask the path of the credentials on the client side.

 
## Requirement

You need to install python3 (check python3 –version) and aws-cli/2. (aws –version)

Libraries needed:

- Pillow (for image processing)
- Boto3 (sqs and bucket handler)
- Paramiko (SSH and SFTP)

&quot;Soft/environment&quot; needed:

- An environment to launch shell script

Once there all installed, you just run the shell script install.sh and watch the server being create automatically (I hope).

  
## Presentation

Presentation video :

  
## Technologies used

We used several technologies:

- Technologies from AWS :
  - EC2 to create instances, security-group and private key
  - Bucket to store logs and modified images
  - SQS to make the communication between the server and the several clients
    - requestQueue for the server to gather data to analyse them
    - responseQueue froe the server to send the answer to the clients
  - AWS-CLI : to retrieve and create data from the AWS service.
- Other technologies:
  - SSH with librairy paramiko to communicate with the instance created. Used mainly to download the different librairies and configure aws-cli on the server side.
  - SFTP with librairy paramiko to transfert files like the server script : **servor\_sqs.py**
  - Image Processing with Pillow

Languages used:

- Python for most of the scipt : server /client
- Shell script for install file
- Batch for small things

  
## Project Architecture

Main files :

| **Name** | **Type** | **Technologies used** | **Description** | **Arguments** | **Automatic** |
| --- | --- | --- | --- | --- | --- |
| **Install.sh** | SHELL | AWS-cli | Use to generate/load an instance on aws. This instance will be used as a servor after that. If security-group key or instance are already made, it will not create a new one | No | Yes |
| **Launcher\_manager.bat** | BAT | None | Will be used to launch config\_environment and Launch\_server.py | 1 : Hostname of the remote instance | yes |
| **Config\_environment.py** | PYTHON3 | SSH, SFTP | Install and configure everything that we need on the remote instance and update credentials on the server side. If it&#39;s already installed, it will just update the credentials. It will used ssh to send command to the server and sftp to transfer servor\_sqs.py to the server | 1: HostnameOf the remote instance | Almost:A question will be asked for the path to your credentials |
| **Launch\_server.py** | PYTHON3 | SSH | Handle server launch on remote instance. Will kill others process and start the server. Will display the output of the server. Will use SSH to get the output and send command to kill processes. | 1:HostnameOf the remote instance | Yes |
| **Servor\_sqs.py** | PYTHON3 | Pillow,boto3 | Will get request through SQS requestQueue, will do some processing and then will send the response back to the client by using the responseQueue and upload to a bucket the logs and modified images. Can do image processing and numbers analyzes. | No | Yes |
| **Client\_sqs.py** | PYTHON3 | Pillow,boto3 | Client that will send a request through requestQueue and will get the answer thanks to responseQueue. Can ask for image Processing or numbers analyzes (means min max median) | You can write directly command to avoid going into the menu like client\_sqs.py -t 25 -s 1 2 3 6 | No |

 
## Instruction: What to do

Steps :

1. Get your account details and copy them to your credentials (C:/User/Nom/.aws)
2. Launch install.sh (with shell console)
    - Install.sh will create everything for making an instance run. If features have already been created, it will have retrieved them.
3. Install.sh will **automatically** launch Launcher\_manager. If at one point you want to launch alone, you can but you need to put one parameter which is the hostname of your AWS instance.
4. Launcher\_manager will **automatically** launch config\_environment.bat. This bat will launch a python with a SSH connection to install and config every libraries and AWS cli needed on the server side. You can launch it alone, but you need to put one parameter which is the hostname of your AWS instance.
    - Warning: A question will be asked: it need the path to your credentials (for doing a transfer)
5. Launcher\_manager will **automatically** launch Launch\_server.bat which will launch and display output of servor\_sqs.py on the remote instance. You can launch it alone, but you need to put one parameter which is the hostname of your AWS instance.
6. Now you launch client\_sqs.py on your side and you can work with the server.
7. If you quit the instance, close the server, or just made a mistake. You can just rerun install.sh. it will only do things that must be done (not downloading a second time the libraries or creating other instances, group-id).
    - Warning: please keep the private key or there will be problem if you delete the repertory without deleting the key pair on the AWS interface. (Will think the key is still the good one).

The figure below is showing the main scripts used and when there are used:


 ![](representation.png)

## Client\_sqs.py

Client is used to send request to the servor thanks to the SQS of Amazon. We can call :

client\_sqs.py [command] [value] [command] [value]…

or

client\_sqs.py
>[command] [value] [command] [value]

>[command] [value] [command] [value]

| Commands | Argument | Description |
| --- | --- | --- |
| -h –help help | None | Display the different command that you can do |
| -t –timeout timeout | 1 : the time in second | To modify the value (second) of the timeout. Used after sending a request. By default: 10 sec |
| -c –clear clear | None | Use to clear responseQueue and requestQueue. Not useful now. Except if there are too many messages stored in the queues (will increase process time) |
| -b –bucket bucket | 1: name of the new bucket | Gove the name of the bucket where images will be stored. Can be used if a distant client is used and doesn&#39;t have access to config.txt. |
| -s –send send | N: (at least 1) set of numbers separated by spaces.-s 1 2 5 6 3 8 25 6 5 | Request the server to make analyzes on the set of numbers. It will display the result (which will be also stored in a log file in a bucket). Be careful, after this command you cannot write another command (will be send as values of the command send) |
| -n –nvg nvg | 2: Source\_path on your computerFile\_name for the modified image on the bucket | Will upload the image on the bucket, then send a request to the server. The server will retrieve the image, made a greyscale on it and upload it on the bucket. It will send the result 1 or 0 to the clients depending if it was a success or not |
| -thl –threshold threshold | 2: Source\_path on your computerFile\_name for the modified image on the bucket | Will upload the image on the bucket, then send a request to the server. The server will retrieve the image, made a threshold on it (for every channel, 0 if \&lt; 125 and 254 if \&gt; 125). Then He will upload it on the bucket. It will send the result 1 or 0 to the clients. |


## Trouble:

One of the biggest troubles was the bucket. When we changed our accounts, the bucket was not working anymore. The solution found was to create a configure.txt file when launching the python Launch\_server who will stock a bucket name generated randomly. This file is then sent to the server. Servor\_sqs and client\_sqs will then used them to get the name of the bucket. If the client is on a remote computer without the good configure.txt file, you can configure it manually with the command -b.

- Another solution was to put a message on the requestQueue, could have worked better and would have been automated (client from another computer could use it)

Another trouble was the configuration of AWS and the python environment on the remote server. It works in local, but I had to use a virtual environment on Linux (we did not know about that).

Last trouble, when an instance is starting, we cannot connect ourselves directly with a SSH connection. We need to wait for at least 10 more seconds.

 
## What we learnt

We learn a lot thanks to this project. That is one of the biggest projects we had in python (even If there is no design pattern). We also learn to use shell and aws-cli in depth. Finally, we think that using SSH, SFTP and SQS was great to understand how services can work with others.
