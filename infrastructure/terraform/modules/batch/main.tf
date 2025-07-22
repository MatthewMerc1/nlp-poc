resource "aws_iam_role" "batch_service" {
  name = "batch_service_role"
  assume_role_policy = data.aws_iam_policy_document.batch_service_assume_role.json
}

data "aws_iam_policy_document" "batch_service_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["batch.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "batch_service" {
  role       = aws_iam_role.batch_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_iam_role" "batch_instance" {
  name = "batch_instance_role"
  assume_role_policy = data.aws_iam_policy_document.batch_instance_assume_role.json
}

data "aws_iam_policy_document" "batch_instance_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "batch_instance" {
  role       = aws_iam_role.batch_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "batch_instance_ecs" {
  role       = aws_iam_role.batch_instance.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_batch_compute_environment" "main" {
  compute_environment_name = var.compute_environment_name
  compute_resources {
    max_vcpus           = var.max_vcpus
    min_vcpus           = var.min_vcpus
    desired_vcpus       = var.desired_vcpus
    instance_types      = var.instance_types
    subnets             = var.subnet_ids
    security_group_ids  = var.security_group_ids
    type                = "EC2"
    allocation_strategy = "SPOT_CAPACITY_OPTIMIZED"
    instance_role       = aws_iam_role.batch_instance.arn
  }
  service_role = aws_iam_role.batch_service.arn
  type         = "MANAGED"
  state        = "ENABLED"
}

resource "aws_batch_job_queue" "main" {
  name                 = var.job_queue_name
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.main.arn]
}

resource "aws_batch_job_definition" "main" {
  name       = var.job_definition_name
  type       = "container"
  container_properties = jsonencode({
    image: var.job_image,
    vcpus: var.job_vcpus,
    memory: var.job_memory,
    command: var.job_command,
    environment: var.job_environment,
    jobRoleArn: aws_iam_role.batch_instance.arn,
    executionRoleArn: aws_iam_role.batch_instance.arn,
    logConfiguration: {
      logDriver: "awslogs",
      options: {
        "awslogs-group": "/aws/batch/job",
        "awslogs-region": var.aws_region,
        "awslogs-stream-prefix": "batch"
      }
    }
  })
  retry_strategy {
    attempts = 3
  }
} 