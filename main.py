import boto3
from botocore.config import Config


#######################
# set the environement variables
# export AWS_ACCESS_KEY_ID="AKIAWOXK5EJXUSU6D267"
# export AWS_SECRET_ACCESS_KEY="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"
#
################


# boto3 configurations
config = Config(
    region_name='us-east-1'
)

desired_tags = {
    "Environment": "SANDBOX",
    "Project": "vf-grp-ias-dev-ias-sanbox",
    "ManagedBy": "o-380-dl-vci-secretsmanagement@vodafone.onmicrosoft.com",
    "SecurityZone": "DEV",
    "Confidentiality": "C2",
    "TaggingVersion": "V2.4"
}

############ EBS Volumes Tagging ######################
def get_vol_ids():
    """
    this function will get all the EBS Volumes ids in the configured region and retun the ids list.
    
    :param : None
    :return: list, ids of all the volumes in the region configured.
    """
    aws_ec2_cli = boto3.session.Session().resource(service_name='ec2', region_name='us-east-1')
    vol_ids = []
    for vol in aws_ec2_cli.volumes.all():
        vol_ids.append(vol.id)

    return vol_ids


def create_ebs_tags(vol_ids):
    """
    this function will compare the EBS volumes current tags with the desired tags and will
    add the missed tags to the EBS volumes inplace.
    
    :param vol_ids: list, ids of all the volumes in the region configured.
    :return: None
    """
    ec2 = boto3.resource('ec2', config=config)
    for id in vol_ids:
        volume = ec2.Volume(id)
        volume_tags = volume.tags
        # if there are some tags compare with the desired.
        if volume_tags:
            tag_keys = [tag['Key'] for tag in volume_tags]
            diff = set(desired_tags.keys()) - set(tag_keys)
            missed_tags = [{"Key": key, "Value": desired_tags[key]} for key in diff]
            # if there are not missing tags.
            if len(missed_tags) == 0:
                continue
            # if there are some missing tags add them.
            else:
                volume.create_tags(Tags=missed_tags)
        # if the volumes has no tags at all. create all tags.
        else:
            missed_tags = [{"Key": key, "Value": desired_tags[key]} for key in desired_tags]
            volume.create_tags(Tags=missed_tags)




################ LB tagging ################

missed_tags = [{"Key": key, "Value": desired_tags[key]} for key in desired_tags]
def get_elbv2_client():
    """
    this function will create and elastic load balancer v2 client instance and return it back.
    
    :param: 
        None
    :return: 
        lb: elbv2 client instance
    """
    lb = boto3.client('elbv2', config= config)
    return lb 

def get_elbv2_arn(lb_client):
    """
    this function will get elastic load balancers v2 resource arns to be used for tag creation.
    
    :param: 
        lb_client: elbv2 client instance
    :return 
        lb_arns: list, elbv2 resource arns
    """
    resp = lb_client.describe_load_balancers()
    lb_arns = []
    if len(resp['LoadBalancers']) == 0:
        return lb_arns
    else:
        for i in resp['LoadBalancers']:
            lb_arns.append(i['LoadBalancerArn'])
        return lb_arns

def create_elbv2_tags(tags, arns, lb_client):
    """
    this function will create elastic load balancers v2 tags.
    
    :param: 
        tags     : list(dict), list contains kev value dict of desired tags
        arns     : list(str), elbv2 resourecs arns
        lb_client: elbv2 client instance
    :return: 
        lb_arns: list, elbv2 resource arns
    """

    lb_client.add_tags(
        ResourceArns= arns,
        Tags=tags
    )

def update_elbv2_tags():
    """
    this function will implement all the logic for updating the tags of the resources.

    :param: 
        None
    :return: 
        None
    """
    lb_client = get_elbv2_client()
    lb_arns  = get_elbv2_arn(lb_client=lb_client)
    if len(lb_arns) == 0:
        print( "You Don't have any load balancers")
        return
    else:
        create_elbv2_tags(tags= missed_tags, arns= lb_arns, lb_client= lb_client)

#################### Security Group tagging ###################
    
def get_all_security_groups():
    """
     this function will return a list of all security groups
    :param:
        None 
    :return:
        sg_ids: list of all security groups
    """
    ec2 = boto3.client('ec2', config= config)
    resp = ec2.describe_security_groups()
    sg_ids = []
    for sg in resp["SecurityGroups"]:
        sg_ids.append(sg["GroupId"])

    return sg_ids

def tag_sg(sg_ids):
    """
    this function will add the desired tags to the security groups
    :param:
        sg_ids: list of all security groups
    :return:
        None
    """
    sg_ids = get_all_security_groups()
    for id in sg_ids:
        ec2_r = boto3.resource('ec2', config= config)
        security_group = ec2_r.SecurityGroup(id)
        security_group.create_tags(Tags=missed_tags)
        print("Tags added to security group: ", id)
        






################################
if __name__=='__main__':
    vol_ids = get_vol_ids()
    create_ebs_tags(vol_ids)
    update_elbv2_tags()
    sg_ids = get_all_security_groups()
    tag_sg(sg_ids)


