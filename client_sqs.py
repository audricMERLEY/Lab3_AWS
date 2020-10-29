import boto3
import os
import sys
import time
import random
import progress

#Color for Failure during process, will be used when printing problems.
FAIL = '\033[91m'
#Color for Success during process, will be used when printing results.
OKGREEN = '\033[92m'
#Used to go back to normal color.
ENDC = '\033[0m'


#Exception raised when there will be a time out during sending message to server.
class TimeoutException(Exception):
    pass

#Exception raised when there will be problems woth params : not the good number, a letter instead of a number,...
class ParamException(Exception):
    pass


# Class used to send message to server
# Action that are/can be done :
# > Create SQS Queues if they don't exist (responseQueue and requestQueue).
# > Send/Receive messages to/from server by SQS queues.
# > Change timeout (when waiting for the answer from the server).
# > Purge SQS queues.
# > Display help for commands.
class Lab3 :
    # This dictionnary gives for each commands the number of param/value needed.
    # Values types :
    # > 'A' means at least one param and no limit.
    # > 'N' means no param needed.
    # > '1' means 1 param needed.
    cmd_param = {
        # For command send number get result.
        '-s' : 'A',
        'send' : 'A',
        '--send' : 'A',
        # For command greyScale.
        '-n' : '2',
        'nvg' : '2',
        '--nvg' : '2',
        # For command threshold.
        '-thl' : '2',
        'threshold' : '2',
        '--threshold' : '2',
        # For command help.
        '-h' : 'N',
        'help' : 'N',
        '--help' : 'N',
        # For command timeout.
        '-t' : '1',
        'timeout' : '1',
        '--timeout' : '1',
        # For command clear.
        '-c' : 'N',
        'clear' : 'N',
        '--clear' : 'N',
        # For command bucket.
        '-b' : '1',
        'bucket' : '1',
        '--bucket' : '1'
    }


    def __init__(self):
        self.client = boto3.client('sqs') # Init client : used to list ,create SQS queue and delete messages. 
        self.sqs = boto3.resource('sqs') # Init sqs : used to get SQS queue by the url/name.
        self.request_queue = None # Queue used to send request to server.
        self.response_queue = None # Queue used to get answer from the server.
        self.bucket_client = boto3.client('s3')# Init bucket_client : used to list ,create bucket and uploading log files. 
        self.bucket = "" #Bucket name where logs files will be stocked and images retrieves.
        self.rdm_id = 0 # Random ID that will be used to link the request with the answer.
        self.time_out = 10 # Time out when waiting the answer from the server.
        self.create_queue() # Init of requestQueue and responseQueue.
        self.init_bucket()

    # Display help.
    def help(self):
        print('*****HELP*****\nThere is 2 ways to execute and use the following commands :')
        print('> Directly with the prompt : lab3_client [command] [value] [command] [value]')
        print('> Enter in the program with the command : lab3_client  then using the set [command] [value] \n\n')
        print('Commands : ')
        print('-s      --send      send        |   Use this command to send numbers to the server and get back calculation on these') 
        print('                                |   Value : REQUIRED (set of numbers)')
        print('                                |   Example : -s 1 5 6 8')
        print('---')
        print('-n      --nvg       nvg         |   Use this command to ask the server to make a greyScale on an image from a bucket (can find the modified image in the same bucket )')
        print('                                |   Value : REQUIRED image_path_on_computer image_transformed_on_bucket')
        print('                                |   Example : --nvg small_image_color.png small_image_greyScale.png')
        print('---')
        print('-thl  --threshold   threshold   |   Use this command to ask the server to make a threshold on an image from a bucket (can find the modified image in the same bucket)')
        print('                                |   Value : REQUIRED image_path_on_computer image_transformed_on_bucket')
        print('                                |   Example : -thl small_image_greyScale.png small_image_binary.png')
        print('---')
        print('-t      --timeout   timeout     |   Use this command to change the TimeOut of the answer in second')
        print('                                |   Value : REQUIRED time in second ')
        print('                                |   Example : -t 10')
        print('---')
        print('-c      --clear     clear       |   Use this command to clear the requestQueue and the reponseQueue')
        print('                                |   Example : -c')
        print('---')
        print('-b      --bucket    bucket      |   Use this command to change name of bucket')
        print('                                |   Example : -b bucketlog145879')
        print('---')
        print('-h      --help      help        |   Use this command to display help (but i guess you get it since you are on the help display).')
        print('                                |   Example : -h')
        print('---')
        print('                    exit        |   Use this command to exit from the menu.')


    # Function create_queue
    # Test if SQS queues requestQueue and responseQueue already exist.
    # If they don't, it will create them.
    def create_queue(self):
        queues =  self.client.list_queues(QueueNamePrefix='re')
        response_queue_created = False
        request_queue_created = False
        if("QueueUrls" in queues):
            for url in queues['QueueUrls'] :
                response_queue_created = response_queue_created or (url == 'responseQueue')
                request_queue_created = request_queue_created or (url == 'requestQueue')
                if(response_queue_created and request_queue_created) :
                    break
        if (not response_queue_created) :
            self.client.create_queue(QueueName='responseQueue')
        if(not request_queue_created) :
            self.client.create_queue(QueueName='requestQueue')
        self.request_queue = self.sqs.get_queue_by_name(QueueName='requestQueue')
        self.response_queue = self.sqs.get_queue_by_name(QueueName='responseQueue')


    # Function init_bucket
    # Test if bucket log_bucket already exists.
    # If it doesn't, it will create it.
    def init_bucket(self,force = False):
        if(not force):
            with open("configure.txt",'r') as myFile:
                self.bucket = myFile.readline().replace('\n',' ')
        buckets = self.bucket_client.list_buckets()
        bucket_created = False
        for bucket in buckets['Buckets']:
            if(bucket["Name"] == self.bucket) :
                bucket_created = True
                break
        if(not bucket_created):
            self.bucket_client.create_bucket(Bucket=self.bucket)


    # Function clear_queue
    # Remove everything (purge) from SQS queue request_queue and reponse_queue.
    # WARNING |
    # AWS forbid to do 2 purges of the same Queue if time difference between both purges is less than 60 sec.
    def clear_queue(self) :
        self.request_queue.purge()
        self.response_queue.purge()
        print(OKGREEN+"responseQueue and requestQueue cleared"+ENDC)
    

    # Function parse_reponse
    # PARAM |
    # content [REQUIRED]: string line in the format 'Key1 value1 Key2 value2 ....'.
    # RETURN |
    # Dictionnary in the format {key1 : value1,key2 : value2}.
    # WARNING | 
    # Key will be String and value will be float.
    # EXAMPLE |
    # rep = parse_reponse('MEANS 1 MEDIAN 2 MAX 3')
    # rep will be {'MEANS' : 1, 'MEDIAN' : 2, 'MAX' : 3}
    def parse_response(self,content):
        response = {}
        content_array = content.split(' ')
        for index in range(0,len(content_array),2) :
            # Check if there is a problem.
            if(index+1 > len(content_array) or content_array[index] == ''):
                break
            response[content_array[index]] = float(content_array[index+1])
        return response

    # Function get_answer
    # Wait for the answer of the server.
    # Use a time out to stop the wait after a while.
    # Return response from the server in a dictionnary.
    # RETURN |
    # Dictionnary in the format {key1 : value1,key2 : value2}.
    # WARNING | 
    # Key will be String and value will be float.
    def get_answer(self) :
        rep = False
        response = {}
        print('Waiting for answer...')
        tic = time.perf_counter() # Reference time for the timeout test.
        suffix_str = "Timeout("+str(self.time_out)+")"
        progress.printProgressBar(0, self.time_out, prefix = 'Reach TimeOut:', suffix = suffix_str, length = 50) # Display a progress bar on prompt (at 0%).
        while(not rep) :
            toc = time.perf_counter()
            spent_time = toc-tic 
            progress.printProgressBar(spent_time, self.time_out, prefix = 'Reach TimeOut:', suffix = suffix_str, length = 50) # Modify the progress bar to be at the good value (n%).

            # Test if time out.
            if(spent_time > self.time_out):
                print() # Used for the progress bar. 
                raise TimeoutException()

            # Receive messages from the response_queue.
            for m in self.response_queue.receive_messages(MessageAttributeNames=['ID']) :
                # Check if the message's ID is the same as the one sent with the request. 
                if(m.message_attributes['ID']['StringValue'] == str(self.rdm_id)) :
                    response = self.parse_response(m.body)
                    rep = True                
                    self.client.delete_message(QueueUrl = m.queue_url,ReceiptHandle = m.receipt_handle)
                    break
        print() # Used for the progress bar.
        return response
       

    # Function send
    # This function will send values then wait for the answer from the server
    # PARAM |
    # values : an number array with the values to send to the server.
    # cmd [REQUIRED]: the command (string) to send in the metadata.
    # EXAMPLE |
    # self.send([1 2 3],"-calc")
    def send(self,values,cmd):

        # Create a string with the array : [1 2 3]=>"1 2 3".
        if isinstance(values, list) :
            request = ' '.join(map(str, values))
        # Create and add a random ID to the request. It will be used to get the good response message (with the same ID) from response_queue.
        self.rdm_id = int(random.random()*10000)
        self.request_queue.send_message(MessageBody = request,MessageAttributes={
        'ID': {
            'StringValue': str(self.rdm_id),
            'DataType': 'String'
        },
        'cmd': {
            'StringValue': cmd,
            'DataType': 'String'
        }
        })
        print(OKGREEN+'Information send'+ENDC)

        # Try to get the answer from the server until the result is out or the time is out.
        try:
            response = self.get_answer()
            for rep in response :
                print(rep+' : '+str(response[rep]))
        except TimeoutException:
            print(FAIL+"TIME OUT\nIf you want to change the the time out value, use command ""-t value"""+ENDC)

    

    def save_file_to_bucket(self,filename,dst_file = ""):
        dst_file = filename if dst_file == "" else dst_file
        self.bucket_client.upload_file(filename,self.bucket,dst_file)
    
    def get_check_paths_param(self,line,nbr_needed):
        paths = line.split(' ')
        if(len(paths) != nbr_needed):
            raise ParamException("Number of params isn't correct, needed: "+nbr_needed+" | found "+len(paths)+" for cmd line "+line)
        if("" in paths ) :
            raise ParamException("One of the param is null for " + str(paths))
        return paths


    def image_proc(self,paths,line):
        # Upload temp image on bucket
        temp_path = paths[1]+".temp"
        if os.path.exists(paths[0]) :
            self.save_file_to_bucket(paths[0],temp_path)
        else :
            raise ParamException("The file "+paths[0]+" doesn't exist.")
        value = [temp_path,paths[1]]
        self.send(value,line)
        self.bucket_client.delete_object(Bucket=self.bucket,Key=temp_path)
         


    # Function change_parameter
    # PARAM |
    # name : string which represent the command to do.
    # value : string/number/array (depends of the case) which must be used with the command.
    # EXAMPLE |
    # ....
    # self.change_parameter('send',[1 2 3 4 5])
    # self.change_parameter('-t','5')
    # self.change_parameter('--clear',None)  
    def change_parameter(self,name,value):
        if name == '-h' or name == '--help' or name == 'help' :
            self.help()
        elif name == '-s' or name == '--send' or name == 'send' :
            self.send(value,"-calc")
        elif name == '-c' or name == '--clear' or name == 'clear' :
            self.clear_queue()
        elif name == '-t' or name == '--timeout' or name == 'timeout' :
            self.time_out = int(value)
            print("Timeout change to "+str(self.time_out))
        elif name == '-thl' or name == '--threshold' or name == 'threshold' :
            self.image_proc(value,"-thr")
        elif name == '-n' or name == '--nvg' or name == 'nvg' :
            self.image_proc(value,"-nvg")
        elif name == '-b' or name == '--bucket' or name == 'bucket' :
            self.bucket = value
            self.init_bucket(True)
        else :
            msg = 'The command '+name+' doesn''t exist, use -h or --help or help to get information on which command you can use'
            print(FAIL+msg+ENDC)


    # Function split_and_exec_commands_line
    # Used to split the differents command and running them. 
    # PARAM |
    # line : string or array wich contains the differents commands and the values that must be used with it.
    # WARNING |
    # For DEV : it's a recursive function !!!
    # EXAMPLE |
    # lab3 = Lab()
    # lab3.split_and_exec_commands_line('-c -t 8 -h send 1 2 5 6 timeout 6')
    # This will : clear/purges the SQS queues, then set timeout to 8 sec then display help then send [1 2 5 6] and wait for the answer then set timeout to 6 sec.
    def split_and_exec_commands_line(self,line):
        # Test if line is already an array or create it.
        line_cmds = line if isinstance(line,list) else line.split(' ')
        # Get the command name.
        name = line_cmds[0]
        values = None

        # Try to get the params needed with the command.
        # Exception raised if there are problems with the params of the command : not the good number, a letter instead of a number,... 
        try :
            # Check if the command is known.
            if(name in self.cmd_param.keys()) :
                nb_param = self.cmd_param[name]
            else :
                raise ParamException(name+" doesn't exist.\nFeel free to use command -h or --help or help to get more information on which command you can use.")

            # Get the params in conjunction with the number of parameters needed.
            if(nb_param == 'N'):
                line_cmds.pop(0) # Remove the command that will be executed.
            elif(nb_param.isdigit()) :
                if(len(line_cmds)-1 >= int(nb_param)) :
                    values = line_cmds[1:int(nb_param)+1]
                    del line_cmds[0:int(nb_param)+1] # Remove the command that will be executed and the params associated with.
                    if(int(nb_param) == 1):
                        values = values[0]
                else :
                    raise ParamException(nb_param+" needed but only "+str(len(line_cmds)-1)+" available for command "+name+" in line "+line_cmds)
            else :
                # Means params are everything until next command or the end of the command line.

                # Test that at least one param is used.
                if(len(line_cmds) >= 2 and not line_cmds[1] in self.cmd_param) :
                    # Get the index of the last param before another command is wrote.
                    max_idx = len(line_cmds)
                    for cmd_name in self.cmd_param.keys() :
                        if cmd_name in line_cmds[1:] :
                            max_idx = min(max_idx,line_cmds.index(cmd_name))
                    values = line_cmds[1:max_idx]
                    del line_cmds[0:max_idx] # Remove the command that will be executed and the params associated with.
                else :
                    raise ParamException("At least one param needed but nothing found for command "+name+" in line "+line_cmds)
        except ParamException as exp:
            print(FAIL+"Error : "+exp.args[0]+ENDC)
        else :
            self.change_parameter(name,values) # Execute the command with the params needed.
            if(len(line_cmds) > 0):
                self.split_and_exec_commands_line(line_cmds) # Recursive : process with the rest of the commands line.

        



# Processing
def menu():
    quit = False
    print('Hello and welcome to the lab3 client program.')
    print('With this program, you can send a set of number to a server through SQS.')
    print('The program on the server side will collect them and make analysis on them. He will then send them back to you and your bucket.')
    print('Feel free to use command -h or --help or help to get more information on which command you can use.')
    print('To exit from this menu, please use the command "exit"')
    while (not quit) :
        try:
            line = input("> ")
            if line == "exit" :
                quit = True
            else:
                lab3.split_and_exec_commands_line(line)
                input("Click on any key")
        except Exception as e:
            print(FAIL)
            print(e)
            print(ENDC)
        

lab3 = Lab3()
# Condition below : 
# > if the user uses command line (he called "python client_sqs.py -s 1 2 3 5 -t 10 -c ....").
# > if the user wants to see the menu (he called "python client_sqs.py").
if(len(sys.argv) > 1) :
    lab3.split_and_exec_commands_line(sys.argv[1:])
else :
    menu()



