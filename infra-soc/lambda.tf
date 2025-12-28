# Zip the Python code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

# The Lambda Function
resource "aws_lambda_function" "soc_responder" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "GuardDuty-Incident-Response"
  role          = aws_iam_role.lambda_soc_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.security_alerts.arn # Environment Variable!
    }
  }
}

# EventBridge Rule: Trigger on GuardDuty Findings
resource "aws_cloudwatch_event_rule" "guardduty_rule" {
  name        = "GuardDuty-Findings-Rule"
  description = "Triggers Lambda when GuardDuty detects a threat"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
  })
}

# Link EventBridge to Lambda
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.guardduty_rule.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.soc_responder.arn
}

# Permission for EventBridge to call Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.soc_responder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.guardduty_rule.arn
}