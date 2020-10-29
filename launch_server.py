from paramiko import *
import sys
import string
import random

# used to generate a random name for the bucket
def generate_random_bucket():
    bucket_name ="bucketlog"+''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(20))
    with open("configure.txt","w") as myFile:
        myFile.write(bucket_name)
    return str(bucket_name)

# cancel other instance
def kill_all_instances():
    stdin, stdout, stderr = ssh_client.exec_command("pgrep -f servor_sqs")
    for line in stdout.readlines():
        ssh_client.exec_command("sudo kill -9 "+line)


username = "ec2-user"
password = ""
port = 22
hostname = ""
if(len(sys.argv) > 1) :
    # need the hostname to connect with SSH
    hostname = sys.argv[1]
    ssh_client = SSHClient()
    key = RSAKey.from_private_key_file("lab3KeyPair.pem")
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.connect(hostname,port=port,username=username,password=password,pkey=key)
    print("ssh connection")
    kill_all_instances()
    ssh_client.exec_command("echo \""+str(generate_random_bucket())+"\" > configure.txt")
    stdin, stdout, stderr = ssh_client.exec_command("cat configure.txt")
    print(str(stdout.read()))
    # Launch servor_sqs
    stdin, stdout, stderr = ssh_client.exec_command("python3 servor_sqs.py",get_pty=True)
    while True:
        # print output of the servor in real time
        print(stdout.readline())
        if stdout.channel.exit_status_ready():
            break
    
else:
    print("Error need one argument (hostname)")
    