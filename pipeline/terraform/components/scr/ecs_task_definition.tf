resource "aws_ecs_task_definition" "test-environment-scr-service-task" {
  family = "scr-service-task-${var.build_id}"

  container_definitions = jsonencode(
  [
    {
      name = "scr-service"
      image = "${var.ecr_address}/scr-web-service:scr-${var.build_id}"
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group = "/ecs/scr-service-environment"
          awslogs-region = var.region
          awslogs-stream-prefix = var.build_id
        }
      }

      environment = [
        {
          name = "SCR_LOG_LEVEL"
          value = var.scr_log_level
        },
        {
          name = "SCR_MHS_ADDRESS"
          value = var.scr_mhs_address
        }
      ]

      secrets = var.scr_mhs_ca_certs_arn == "" ? [] : [
        {
          name = "SCR_SECRET_MHS_CA_CERTS",
          valueFrom = var.scr_mhs_ca_certs_arn
        }
      ]

      portMappings = [
        {
          containerPort = 80
          hostPort = var.scr_service_port
          protocol = "tcp"
        }
      ]
    }
  ]
  )
  cpu = "128"
  memory = "128"
  requires_compatibilities = [
    "EC2"
  ]
  execution_role_arn = var.task_execution_role
  tags = {
    Name = "${var.environment_id}-scr-task"
    EnvironmentId = var.environment_id
  }
}