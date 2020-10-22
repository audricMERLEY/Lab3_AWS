import boto3
import statistics

def calculation(numbers):
    print('calculation')
    res = {}
    res["Mean"] = statistics.mean(numbers)
    res["Min"] = min(numbers)
    res["Max"] = max(numbers)
    res["Median"] = statistics.median(numbers)
    return res

def create_response(response) :
    content = ""
    for rep in response:
        content += rep+' '+str(response[rep])+' '
    return content

def send_response(response,ID) :
    print('send response')
    sqs = boto3.resource('sqs')
    responseQueue = sqs.get_queue_by_name(QueueName='responseQueue')
    responseQueue.send_message(MessageBody=response,MessageAttributes={
        'ID': {
            'StringValue': ID,
            'DataType': 'String'
        }})

def save_reponse(reponse) :
    s3_client = boto3.client('s3')
    s3_rs = boto3.resource('s3')
    s3_rs.Bucket('Log')

def receive_worker() :
    client = boto3.client('sqs')
    sqs = boto3.resource('sqs')
    requestQueue = sqs.get_queue_by_name(QueueName='requestQueue')
    while True :
        for m in requestQueue.receive_messages(MessageAttributeNames=['ID']):
            numbers = [] # to do
            content = m.body
            ID = m.message_attributes['ID']['StringValue']
            print('message receive :'+content)
            numbers = content.split(' ')
            numbers = list(map(float, numbers))
            response = calculation(numbers)
            send_response(create_response(response),ID)
            client.delete_message(QueueUrl = m.queue_url,ReceiptHandle = m.receipt_handle)



#start
receive_worker()