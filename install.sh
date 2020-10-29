# This script will be used to create the instance and launch pythonn script to configurate the machine and add depencies (python3)
# First step : Handle key-pair : add in file lab3KeyPair the key but manage to get the actual key if it's already created

# Second step : Handle security group. Get the id and manage to get it even if already created

# Third step : Add authorization to security group

# Fourth step : Create instance and get the instance-id, manage if instance already exist

# Fifth step : Lanch the instance

# Sixth step : Launch python script to install libraires and launch server (with transfert thanks to sftp)
# Could be great to display shell on it

# When finished : close the instance

echo "Create keypair"
KEY_DATA=$(aws ec2 create-key-pair --key-name lab3KeyPair --query "KeyMaterial" --output text)
if [ ${?} -ne 0 ]; then
    # means the key already exist :
    echo "key already exist"
else
echo $KEY_DATA > lab3KeyPair.pem
fi
# key_pair created
# 2nd step: create security group
echo "Create security group"
GROUP_ID=$(aws ec2 create-security-group --group-name lab3SecurityGroup --description "Security group created for lab3 instance" --query 'GroupId' --output text)
if [ ${?} -ne 0 ]; then
    # means the group already exist :
    echo "security group already exist"
    GROUP_ID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=lab3SecurityGroup --query "SecurityGroups[0].GroupId" --output text)
fi
echo "security-group-id $GROUP_ID"
# Third step : Add authorization to security group
echo "Add authorisations to security group"
$(aws ec2 authorize-security-group-ingress --group-id $GROUP_ID --cidr 0.0.0.0/0 --protocol all --port all)
if [ ${?} -ne 0 ]; then
    echo "error while adding autorisations"
fi
# Fourth step : Create instance and get the instance-id, manage if instance already exist
echo "Does instance exist"
INSTANCE_ID=$(aws ec2 describe-instances --filters Name=instance-state-name,Values=pending,running,shutting-down,stopping,stopped Name=instance-type,Values=t2.micro Name=image-id,Values=ami-0c94855ba95c71c99 Name=key-name,Values=lab3KeyPair Name=instance.group-id,Values=$GROUP_ID --query "Reservations[0].Instances[0].{Instance:InstanceId}" --output text)
if [ $INSTANCE_ID = "None" ]; then
echo "Didn't find correct instance. Create one :"
INSTANCE_ID=$(aws ec2 run-instances --image-id ami-0c94855ba95c71c99 --instance-type t2.micro --security-group-ids $GROUP_ID --key-name lab3KeyPair --count 1 --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Lab3MERLEY}]' --query "Instances[0].InstanceId" --output text)
if [ ${?} -ne 0 ]; then
    echo "error while creating instance"
fi
fi
echo "instance-id $INSTANCE_ID"
# Fifth step : Run instance
echo "Run instance"
TEMP=$(aws ec2 start-instances --instance-ids $INSTANCE_ID)
if [ ${?} -ne 0 ]; then
    echo "error while loading instance"
fi

HOSTNAME=$(aws ec2 describe-instances --filters Name=instance-id,Values=$INSTANCE_ID --query "Reservations[0].Instances[0].{Instance:PublicDnsName}" --output text)
echo "hostname : $HOSTNAME"

#echo "Launch python script to manage environment of server"
READY=$(aws ec2 describe-instances --filters Name=instance-id,Values=$INSTANCE_ID --query "Reservations[0].Instances[0].State.Name" --output text)
echo "Wait for the instance initialisation : ..."
while [ $READY != "running" ]
do
    echo "Still not running. Next test in 5 sec"
    sleep 5
    READY=$(aws ec2 describe-instances --filters Name=instance-id,Values=$INSTANCE_ID --query "Reservations[0].Instances[0].State.Name" --output text)

done
echo "Instance is running"
sleep 15
RES=$(./temp.bat $HOSTNAME)
echo  "Appuyer sur Entrée pour continuer..."
read a

