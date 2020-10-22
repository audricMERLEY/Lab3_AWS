import boto3
import sys
import time
import random
import progress


class TimeoutException(Exception):
    pass
class ParamException(Exception):
    pass

class Lab3 :
    cmd_param = {
        #for command send
        '-s' : 'A',
        'send' : 'A',
        '--send' : 'A',
        #for command help
        '-h' : 'N',
        'help' : 'N',
        '--help' : 'N',
        #for command timeout
        '-t' : '1',
        'timeout' : '1',
        '--timeout' : '1',
        #for command clear
        '-c' : 'N',
        'clear' : 'N',
        '--clear' : 'N'
    }


    def __init__(self):
        self.client = boto3.client('sqs')
        self.sqs = boto3.resource('sqs')
        self.requestQueue = None
        self.responseQueue = None
        self.rdm_id = 0
        self.timeOut = 10
        self.create_queue()

    def help(self):
        print('*****HELP*****\nThere is 2 ways to execute and use the following commands :')
        print('> Directly with the prompt : lab3_client [command] [value] [command] [value]')
        print('> Enter in the program with the command : lab3_client  then using the set [command] [value] \n\n')
        print('Commands : ')
        print('-s      --send      send        |   Use this command to send numbers to the server                        | value : REQUIRED (set of numbers)')
        print('                                |   Example : -s 1 5 6 8')
        print('-t      --timeout   timeout     |   Use this command to change the timeOut of the answer in second        | value : REQUIRED')
        print('                                |   Example : -t 10')
        print('-c      --clear     clear       |   Use this command to clear the requestQueue and the reponseQueue')
        print('                                |   Example : -c')
        print('-h      --help      help        |   Use this command to display help (but i guess you get it since you are on the help display).')
        print('                                |   Example : -h')
        print('                    exit        |   Use this command to exit from the menu.')


    def create_queue(self):
        queues =  self.client.list_queues()
        response_queue_created = False
        request_queue_created = False
        for url in queues['QueueUrls'] :
            response_queue_created = response_queue_created or (url == 'responseQueue')
            request_queue_created = request_queue_created or (url == 'requestQueue')
            if(response_queue_created and request_queue_created) :
                break
        if (not response_queue_created) :
            self.client.create_queue(QueueName='responseQueue')
        if(not request_queue_created) :
            self.client.create_queue(QueueName='requestQueue')
        self.requestQueue = self.sqs.get_queue_by_name(QueueName='requestQueue')
        self.responseQueue = self.sqs.get_queue_by_name(QueueName='responseQueue')


    def parse_response(self,content):
        response = {}
        contentArray = content.split(' ')
        for index in range(0,len(contentArray),2) :
            if(index+1 > len(contentArray) or contentArray[index] == ''):
                break
            response[contentArray[index]] = float(contentArray[index+1])
        return response

    def get_answer(self) :
        rep = False
        response = {}
        print('waiting for answer')
        tic = time.perf_counter()

        progress.printProgressBar(0, self.timeOut, prefix = 'Reach timeOut:', suffix = 'TimeOut', length = 50)
        while(not rep) :
            toc = time.perf_counter()
            spentTime = toc-tic
            progress.printProgressBar(spentTime, self.timeOut, prefix = 'Reach timeOut:', suffix = 'TimeOut', length = 50)
            if(spentTime > self.timeOut):
                raise TimeoutException()
            for m in self.responseQueue.receive_messages(MessageAttributeNames=['ID']) :
                if(m.message_attributes['ID']['StringValue'] == str(self.rdm_id)) :
                    response = self.parse_response(m.body)
                    rep = True                
                    self.client.delete_message(QueueUrl = m.queue_url,ReceiptHandle = m.receipt_handle)
                    break
        print()
        return response
    

    def clear_queue(self) :
        self.requestQueue.purge()
        self.responseQueue.purge()
        print("cleared")
        

    def send(self,values):
        request = ' '.join(map(str, values))
        self.rdm_id = int(random.random()*10000)
        self.requestQueue.send_message(MessageBody = request,MessageAttributes={
        'ID': {
            'StringValue': str(self.rdm_id),
            'DataType': 'String'
        }})
        print('send done')
        try:
            response = self.get_answer()
            for rep in response :
                print(rep+' : '+str(response[rep]))
        except TimeoutException:
            print()
            print("time out")

        
    def change_parameter(self,name, value):
        msg = ''
        if name == '-h' or name == '--help' or name == 'help' :
            self.help()
        elif name == '-s' or name == '--send' or name == 'send' :
            self.send(value)
        elif name == '-c' or name == '--clear' or name == 'clear' :
            self.clear_queue()
        elif name == '-t' or name == '--timeout' or name == 'timeout' :
            self.timeOut = int(value)
            print("Timeout change to "+str(self.timeOut))
        else :
            msg = 'The command '+name+' doesn''t exist, use -h or --help or help to get information on which command you can use'
        print(msg)


    def split_and_exec_commands_line(self,line):
        line_cmds = line if isinstance(line,list) else line.split(' ')
        name = line_cmds[0]
        values = None
        try :
            if(name in self.cmd_param.keys()) :
                nb_param = self.cmd_param[name]
            else :
                raise ParamException(name+" doesn't exist.\nFeel free to use command -h or --help or help to get more information on which command you can use.")
            if(nb_param == 'N'):
                line_cmds.pop(0)
            elif(nb_param.isdigit()) :
                if(len(line_cmds)-1 >= int(nb_param)) :
                    values = line_cmds[1:int(nb_param)+1]
                    del line_cmds[0:int(nb_param)+1]
                    if(int(nb_param) == 1):
                        values = values[0]
                else :
                    raise ParamException(nb_param+" needed but only "+str(len(line_cmds)-1)+" available for command "+name+" in line "+line_cmds)
            else :
                #means everythong until next commands
                if(len(line_cmds) >= 2) :
                    max_idx = len(line_cmds)
                    for cmd_name in self.cmd_param.keys() :
                        if cmd_name in line_cmds[1:] :
                            max_idx = min(max_idx,line_cmds.index(cmd_name))
                    values = line_cmds[1:max_idx]
                    del line_cmds[0:max_idx]
                else :
                    raise ParamException("At least one param needed but nothing found for command "+name+" in line "+line_cmds)
        except ParamException as exp:
            print("Error : "+exp.args[0])
        else :
            self.change_parameter(name,values)
            if(len(line_cmds) > 0):
                self.split_and_exec_commands_line(line_cmds)

        



#processing
def menu():
    quit = False
    print('Hello and welcome to the lab3 client program.')
    print('With this program, you can send a set of number to a server through SQS.')
    print('The program on the server side will collect them and make analysis on them. He will then send them back to you and your bucket.')
    print('Feel free to use command -h or --help or help to get more information on which command you can use.')
    print('To exit from this menu, please use the command "exit"')
    while (not quit) :
        try:
            line = input("")
            if line == "exit" :
                quit = True
            else:
                lab3.split_and_exec_commands_line(line)
        except Exception as e:
            print(e)
        

lab3 = Lab3()
if(len(sys.argv) > 1) :
    lab3.split_and_exec_commands_line(sys.argv[1:])
else :
    menu()



