# Enable GuardDuty
resource "aws_guardduty_detector" "primary" {
  enable = true
}

# Create the SNS Topic for Security Alerts
resource "aws_sns_topic" "security_alerts" {
  name = "Security-Alerts-Topic"
}

# Create the Email Subscription
resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email # We will define this in variables.tf
}