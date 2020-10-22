import boto3
import sys
import time
import random
import progress


class TimeoutException(Exception):
    pass

class Lab3 :
    def __init__(self):
        self.client = boto3.client('sqs')
        self.sqs = boto3.resource('sqs')
        self.requestQueue = self.sqs.get_queue_by_name(QueueName='requestQueue')
        self.responseQueue = self.sqs.get_queue_by_name(QueueName='responseQueue')
        self.rdm_id = 0
        self.timeOut = 10

    def help(self):
        print('*****HELP*****\nThere is 2 ways to execute and use the following commands :')
        print('> Directly with the prompt : lab3_client [command] [value] [command] [value]')
        print('> Enter in the program with the command : lab3_client  then using the set [command] [value] \n\n')
        print('Commands : ')
        print('-s      --send      send        |   Use this command to send numbers to the server                        | value : REQUIRED (set of numbers)')
        print('                                |   Example : -s 1 5 6 8')
        print('-t      --timeOut   timeOut     |   Use this command to change the timeOut of the answer in second        | value : REQUIRED')
        print('                                |   Example : -t 10')
        print('-c      --clear     clear       |   Use this command to clear the requestQueue and the reponseQueue')
        print('                                |   Example : -c')
        print('-h      --help      help        |   Use this command to display help (but i guess you get it since you are on the help display).')
        print('                                |   Example : -h')
        print('                    exit        |   Use this command to exit from the menu.')



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
        messages_to_remove = self.responseQueue.receive_messages()
        i = 0
        while(len(messages_to_remove)>0 or i < 10) :
            i+=1
            for m in self.responseQueue.receive_messages() :             
                self.client.delete_message(QueueUrl = m.queue_url,ReceiptHandle = m.receipt_handle)
            messages_to_remove = self.responseQueue.receive_messages()

        messages_to_remove = self.requestQueue.receive_messages()
        i = 0
        while(len(messages_to_remove)>0 or i < 10) :
            i+=1
            for m in self.responseQueue.receive_messages() :             
                self.client.delete_message(QueueUrl = m.queue_url,ReceiptHandle = m.receipt_handle)
            messages_to_remove = self.requestQueue.receive_messages()
        

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
            self.timeOut = value
        else :
            msg = 'The command '+name+' doesn''t exist, use -h or --help or help to get information on which command you can use'
        print(msg)


    def split_and_exec_commands_line(self,line):
        line_cmds = line if isinstance(line,list) else line.split(' ')
        send_cmd = False
        for index in range(0,len(line_cmds),2) :
            name = line_cmds[index]
            value = ''
            if(index+1 < len(line_cmds)) :
                value = line_cmds[index+1]
                send_cmd = False
                if(name == '-s' or name == '--send' or name == 'send'):
                    value = line_cmds[index+1::1]
                    send_cmd = True
            self.change_parameter(name,value)
            if send_cmd :
                break


#processing
def menu():
    quit = False
    print('Hello and welcome to the lab3 client program.')
    print('With this program, you can send a set of number to a server through SQS.')
    print('The program on the server side will collect them and make analysis on them. He will then send them back to you and your bucket.')
    print('Feel free to use command -h or --help or help to get more information on which you can command you can use.')
    print('To exit from this menu, please use the command "exit"')
    while (not quit) :
        line = input("")
        if line == "exit" :
            quit = True
        else:
            lab3.split_and_exec_commands_line(line)

lab3 = Lab3()
if(len(sys.argv) > 1) :
    lab3.split_and_exec_commands_line(sys.argv[1:])
else :
    menu()



