# reference an existing container repository
data "aws_ecr_repository" "example" {
    name = "example"
}


provider "aws" {
    region = ""
}

resource "aws_lambda_function" "example" {
    function_name = "example"
    role         = aws_iam_role.lambda.arn
    handler      = "index.handler"
    runtime      = "provided.al2"
    timeout      = 10

    image_uri = data.aws_ecr_repository.example.repository_url

    depends_on = [ aws_iam_role.lambda ]

    environment {
        variables = {
            FOO = "bar"
        }
    }
}



resource "aws_iam_role" "lambda" {
    name = "lambda"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda" {
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    role       = aws_iam_role.lambda.name
    depends_on = [ aws_iam_role.lambda ]
}

# add a public function url
resource "aws_api_gateway_resource" "example" {
    rest_api_id = aws_api_gateway_rest_api.example.id
    parent_id   = aws_api_gateway_rest_api.example.root_resource_id
    path_part   = "example"
}

resource "aws_api_gateway_method" "example" {
    rest_api_id   = aws_api_gateway_rest_api.example.id
    resource_id   = aws_api_gateway_resource.example.id
    http_method   = "GET"
    authorization = "NONE"
}

resource "aws_api_gateway_integration" "example" {
    rest_api_id = aws_api_gateway_rest_api.example.id
    resource_id = aws_api_gateway_resource.example.id
    http_method = aws_api_gateway_method.example.http_method
    type        = "AWS_PROXY"
    uri         = aws_lambda_function.example.invoke_arn
}

resource "aws_api_gateway_deployment" "example" {
    depends_on = [aws_api_gateway_integration.example]
    rest_api_id = aws_api_gateway_rest_api.example.id
    stage_name  = "prod"
}

resource "aws_lambda_permission" "example" {
    statement_id  = "AllowAPIGatewayInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.example.function_name
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_api_gateway_deployment.example.execution_arn}/*/${aws_api_gateway_method.example.http_method}/${aws_api_gateway_resource.example.path_part}"
}

resource "aws_api_gateway_rest_api" "example" {
    name = "example"
}

resource "aws_api_gateway_account" "example" {
    cloudwatch_role_arn = aws_iam_role.lambda.arn
    
}

resource "aws_cloudwatch_log_group" "example" {
    name              = "/aws/lambda/example"
    retention_in_days = 14
}



