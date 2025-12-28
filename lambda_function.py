import json
import boto3
import logging
import os

# Set up logging for CloudWatch monitoring
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sns_client = boto3.client('sns')

def lambda_handler(event, context):
    """
    This function processes GuardDuty findings, extracts the attacker's IP,
    and sends a formatted alert via Amazon SNS.
    """
    
    # 1. Configuration: Get SNS Topic ARN from Environment Variables
    # This allows the code to be portable and secure
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    
    # 2. Extract specific fields from the GuardDuty JSON finding
    # We use .get() to avoid errors if a field is missing
    detail = event.get('detail', {})
    finding_type = detail.get('type', 'Unknown Finding')
    severity = detail.get('severity', 0)
    
    logger.info(f"Analyzing finding: {finding_type} | Severity: {severity}")

    # 3. Logic to extract the Attacker's IP address
    # Not all findings have an IP, so we handle the exception
    try:
        attacker_ip = detail['service']['action']['networkConnectionAction']['remoteIpDetails']['ipAddressV4']
    except KeyError:
        attacker_ip = "N/A (Internal or non-network event)"

    # 4. Filter: Only send alerts for medium to high severity (Severity >= 4)
    if severity < 4:
        logger.info(f"Finding ignored due to low severity ({severity})")
        return {'statusCode': 200, 'body': 'Low severity finding. No alert sent.'}

    # 5. Format the security alert message
    email_subject = f"🚨 GUARDDUTY ALERT: {finding_type}"
    email_body = (
        f"Security finding detected in your AWS Account.\n\n"
        f"TYPE: {finding_type}\n"
        f"SEVERITY: {severity}\n"
        f"ATTACKER IP: {attacker_ip}\n\n"
        f"Please check the AWS Console for immediate investigation."
    )

    # 6. Publish to SNS
    try:
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject=email_subject,
            Message=email_body
        )
        logger.info("Security alert sent successfully via SNS.")
    except Exception as e:
        logger.error(f"Failed to send alert: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Incident processed successfully.')
    }