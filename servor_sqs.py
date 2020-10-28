# What must be done : 
# if queues answer and request doesn't exist : make it
# get the queues
# read the queues
# When something happen, split the command
# following  the command will do calculation or processing
# stock on s3 bucket (log et image) => a créer aussi
# send back une réponse 

import os
import boto3
import statistics
from datetime import datetime
from PIL import Image

#Exception raised when there will be problems with params : not the good number, a letter instead of a number,...
class ParamException(Exception):
    pass

class Worker :

    # This could have worked if there weren't Worker's methodes (with return self.cmd_param[cmd](content) in def command_function(self,cmd,content)
    #cmd_param = {
    #    "-calc":calculation,
    #    "-nvg":greyLevel,
    #    "-thr":threshold,
    #}


    def __init__(self):
        self.sqs_client = boto3.client('sqs') # Init sqs_client : used to list ,create SQS queue and delete messages. 
        self.bucket_client = boto3.client('s3')# Init bucket_client : used to list ,create bucket and uploading log files. 
        self.sqs = boto3.resource('sqs') # Init sqs : used to get SQS queue by the url/name.
        self.request_queue = None # Queue used to send request to server.
        self.response_queue = None # Queue used to get answer from the server.
        self.bucket = "logbucketa215sc487hgjdfi" #Bucket name where logs files will be stocked and images retrieves.
        self.init_queues() # Init of requestQueue and responseQueue.
        self.init_bucket()


    # Function init_queue
    # Test if SQS queues requestQueue and responseQueue already exist.
    # If they don't, it will create them.
    def init_queues(self):
        queues =  self.sqs_client.list_queues()
        response_queue_created = False
        request_queue_created = False
        for url in queues['QueueUrls'] :
            response_queue_created = response_queue_created or (url == 'responseQueue')
            request_queue_created = request_queue_created or (url == 'requestQueue')
            if(response_queue_created and request_queue_created) :
                break
        if (not response_queue_created) :
            self.sqs_client.create_queue(QueueName='responseQueue')
        if(not request_queue_created) :
            self.sqs_client.create_queue(QueueName='requestQueue')
        self.request_queue = self.sqs.get_queue_by_name(QueueName='requestQueue')
        self.response_queue = self.sqs.get_queue_by_name(QueueName='responseQueue')
    

    # Function init_bucket
    # Test if bucket log_bucket already exists.
    # If it doesn't, it will create it.
    def init_bucket(self):
        buckets = self.bucket_client.list_buckets()
        bucket_created = False
        for bucket in buckets['Buckets']:
            if(bucket["Name"] == self.bucket) :
                bucket_created = True
                break
        if(not bucket_created):
            self.bucket_client.create_bucket(Bucket=self.bucket)
    

    # Function calculation
    # PARAM |
    # content [REQUIRED]: string line with the set of number.
    # RETURN |
    # Dictionnary in the format {key1 : value1,key2 : value2,....}.
    # EXAMPLE |
    # rep = self.calculation(1 2 5 6")
    # rep will be {'MEANS' : 7,'MIN':1,'MAX' : 6, 'MEDIAN' : 3.5, }
    def calculation(self,content):
        print('Calculation start.')
        numbers = content.split(' ')
        numbers = list(map(float, numbers))
        res = {}
        res["Mean"] = statistics.mean(numbers)
        res["Min"] = min(numbers)
        res["Max"] = max(numbers)
        res["Median"] = statistics.median(numbers)
        print('Calculation end.')
        return res
          

    # Function create_response
    # PARAM |
    # response [REQUIRED]: dictionnary with the different keys|values to send back.
    # RETURN |
    # string in the format "key1 value1 key2 value2".
    # EXAMPLE |
    # rep = self.create_response({'MEANS' : 7,'MIN':1,'MAX' : 6, 'MEDIAN' : 3.5})
    # rep will be "MEANS 7 MIN 1 MAX 6 MEDIAN 3.5"
    def create_response(self,response):
        content = ""
        for rep in response:
            content += rep+' '+str(response[rep])+' '
        return content


    # Function send_response  
    # PARAM |
    # content [REQUIRED]: string with the answer to send back.
    # ID [REQUIRED]: number used to link the request with this answer.
    # EXAMPLE |
    # self.create_response(self.create_response({'MEANS' : 7,'MIN':1,'MAX' : 6, 'MEDIAN' : 3.5}),5)
    def send_response(self,content,ID):
        print('Send response start.')
        self.response_queue.send_message(MessageBody=content,MessageAttributes={
        'ID': {
            'StringValue': ID,
            'DataType': 'String'
        }})
        print('Send response end.')


    # Function save_log  
    # PARAM |
    # content [REQUIRED]: answer to save inside a file.
    # EXAMPLE |
    # self.save_log(self.create_response({'MEANS' : 7,'MIN':1,'MAX' : 6, 'MEDIAN' : 3.5}))
    def save_log(self,content):
        print('Save log to bucket start.')
        now = datetime.now()
        filename = now.strftime("%d_%m_%Y_%H_%M_%S")+".log"
        log = open(str(filename), "x")
        log.write("At "+now.strftime("%d/%m/%Y %H:%M:%S")+" : "+content)
        log.close()
        self.save_file_to_bucket(filename)
        os.remove(filename)
        print('Save log to bucket end.')

    # Function save_file_to_bucket  
    # PARAM |
    # filename [REQUIRED]: file path on the computer.
    # dst_file : the name of the file in the bucket. By default it's the same as the filename
    def save_file_to_bucket(self,filename,dst_file = ""):
        dst_file = filename if dst_file == "" else dst_file
        self.bucket_client.upload_file(filename,self.bucket,dst_file)

    # Function get_image_bucket  
    # PARAM |
    # filename [REQUIRED]: file name in the bucket. The file will be download with the same name on the computer. Repertory is the one of this file
    def get_image_bucket(self,filename):
        self.bucket_client.download_file(self.bucket, filename, filename)


    def value_threshold(self,pixel):
        res = 254 if(pixel > 125)else 0
        return res

    # Function grey_level  
    # Made threshold on one image and upload it on the bucket
    # PARAM |
    # src_path [REQUIRED]: file path on the computer of the image to modify
    # dst_path [REQUIRED]: the nme of the image modified that will appear in the bucket
    def threshold(self,src_path,dst_path):
        print("Threshold start.")
        self.get_image_bucket(src_path)
        msg = {"Result":"0"}
        if os.path.exists(src_path) :
            im = Image.open(src_path)
            # Processing
            channels = im.split()
            if(len(channels) >=  3):
                R = channels[0].point(self.value_threshold)
                G = channels[1].point(self.value_threshold)
                B = channels[2].point(self.value_threshold)
                im = Image.merge("RGB",(R,G,B))
            elif len(channels) == 1:
                Bin = B = channels[0].point(self.value_threshold)
                im = Image.merge("L",(Bin))
            else:
                raise ParamException("Sry prblm when doing threshold , image format not known, needed 1 or more than 3 channels but found : "+str(len(channels))+" channels")
            tmp_path = "tempThresholdImage.jpg"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            im.save(tmp_path,"JPEG")
            self.save_file_to_bucket(tmp_path,dst_path)
            os.remove(tmp_path)
            os.remove(src_path)
            msg["Result"] = "1"
        print("Threshold end.")
        return msg
    

    # Function grey_level  
    # Made greyscale on one image and upload it on the bucket
    # PARAM |
    # src_path [REQUIRED]: file path on the computer of the image to modify
    # dst_path [REQUIRED]: the nme of the image modified that will appear in the bucket
    def grey_level(self,src_path,dst_path):
        print("Grey level start.")
        self.get_image_bucket(src_path)
        msg = {"Result":"0"}
        if os.path.exists(src_path) :
            im = Image.open(src_path)
            im = im.convert(mode="L")

            tmp_path = "tempGreyScaleImage.jpg"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            im.save(tmp_path,"JPEG")
            self.save_file_to_bucket(tmp_path,dst_path)
            os.remove(tmp_path)
            os.remove(src_path)
            msg["Result"] = "1"
        print("Grey level end.")
        return msg


    def get_check_paths_param(self,line,nbr_needed):
        paths = line.split(' ')
        if(len(paths) != nbr_needed):
            raise ParamException("Number of params isn't correct, needed: "+nbr_needed+" | found "+len(paths)+" for cmd line "+line)
        if("" in paths ) :
            raise ParamException("One of the param is null for " + str(paths))
        return paths


    # Function command_function
    # PARAM |
    # cmd [REQUIRED]: string line in the format '-cmd'.
    # content [REQUIRED]: string line with the param of the command.
    # RETURN |
    # Dictionnary in the format {key1 : value1,key2 : value2,....}.
    # EXAMPLE |
    # rep = self.command_function("-calc","1 2 5 6")
    # rep will be {'MEANS' : 7,'MIN':1,'MAX' : 6, 'MEDIAN' : 3.5}
    def command_function(self,cmd,content):
        if cmd == "-calc":
            return self.calculation(content)
        elif cmd == "-nvg":
            paths = self.get_check_paths_param(content,2)
            return self.grey_level(paths[0],paths[1])
        elif cmd == "-thr":
            paths = self.get_check_paths_param(content,2)
            return self.threshold(paths[0],paths[1])
        else :
            raise ParamException("Command "+content+"unknown")
    


    def receive_worker(self):
        while True :
            for m in self.request_queue.receive_messages(MessageAttributeNames=['ID',"cmd"]):
                try :
                    #Handle attributes.
                    content = m.body
                    print('Message receive :'+content)
                    ID = m.message_attributes['ID']['StringValue'] # ID that will be used to link the request with the answer.
                    cmd = m.message_attributes['cmd']['StringValue']

                    #Process.
                    response = self.command_function(cmd,content)

                    #Answer back.
                    cnt = self.create_response(response)
                    self.send_response(cnt,ID)
                    #Save log in bucket.
                    self.save_log(cnt)
                except ParamException as exp:
                    print("Error : "+exp.args[0])
                except Exception as e:
                    print("Error : ")
                    print(e)
                finally:
                    self.sqs_client.delete_message(QueueUrl = m.queue_url,ReceiptHandle = m.receipt_handle)
                
            



#Processing :
worker = Worker()
worker.receive_worker()