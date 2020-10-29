import sys
from paramiko import *
import os
# Connection by ssh to the vm
class ConfigManager: 
    def __init__(self):
        self.username = "ec2-user"
        self.password = ""
        self.port = 22
        self.hostname = "ec2-3-87-64-160.compute-1.amazonaws.com"
        self.ssh_client = None
    
    def ssh_connection(self):
        key = RSAKey.from_private_key_file("lab3KeyPair.pem")
        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh_client.connect(self.hostname,port=self.port,username=self.username,password=self.password,pkey=key)
 
    def send_cmd(self,cmd,output = False):
        if(self.ssh_client is None):
            self.ssh_connection()
        print('Command to send : '+cmd)
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        st = str(stdout.readlines())
        ste = str(stderr.readlines())
        if(output):
            return st
        else :
            return ste


    def transfert_file(self,src_path,dest_path):
        if(self.ssh_client is None):
            self.ssh_connection()
        print("File to upload : "+src_path)
        sftp = self.ssh_client.open_sftp()
        sftp.put(src_path,dest_path)
        sftp.close()
        

    def handle_python(self):
        # install for working with python script
        answ = self.send_cmd("python3 --version",True)
        if(not "Python 3" in answ):
            print("install python3")
            self.send_cmd("sudo yum -y install python3")
            self.send_cmd("sudo python3 -m venv worker/env")
            self.send_cmd("source ~/worker/env/bin/activate",False)
            self.send_cmd("sudo python3 -m pip install pip --upgrade")
            self.send_cmd("sudo python3 -m pip install boto3")
            self.send_cmd("sudo python3 -m pip install Pillow")
    
    def handle_aws(self):
        answ = self.send_cmd("aws --version",True)
        if( not "aws-cli/2." in answ) :
            print("install aws2.0")
            #install aws2
            self.send_cmd("curl ""https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"" -o ""awscliv2.zip""")
            self.send_cmd("unzip awscliv2.zip")
            self.send_cmd("sudo ./aws/install")
            self.send_cmd("rm awscliv2.zip")
            #modification of credential to made it work
            self.send_cmd("aws configure set aws_access_key_id ASIARHMD34J322VUCS7G")
            self.send_cmd("aws configure set aws_access_key_id region us-east-1")
        self.handle_aws_credentials_info()

    def handle_aws_credentials_info(self):
        #get files from your computer
        aws_path = input('please give the path to repertory .aws : ')
        print(aws_path)
        with open(aws_path+"\credentials","r") as myFile:
            lines = myFile.readlines()
            i = 0
            for line in lines:
                if(i == 0):
                    self.send_cmd("sudo echo \""+line.replace('\n',"")+"\" > ./.aws/credentials")
                    i = 1
                else:
                    self.send_cmd("sudo echo \""+line.replace('\n',"")+"\" >> ./.aws/credentials")
        
        with open(aws_path+"\config","r") as myFile:
            lines = myFile.readlines()
            i = 0
            for line in lines:
                if(i==0):
                    self.send_cmd("sudo echo \""+line.replace('\n',"")+"\" > ./.aws/config")
                    i = 1
                else:
                    self.send_cmd("sudo echo \""+line.replace('\n',"")+"\" >> ./.aws/config")


    def config(self):
        self.handle_python()
        self.handle_aws()
        self.transfert_file("servor_sqs.py","servor_sqs.py")
        self.ssh_client.close()


conf = ConfigManager()
if(len(sys.argv) > 1) :
    conf.hostname = sys.argv[1]
    print("Hostname :" + conf.hostname)
conf.config()

