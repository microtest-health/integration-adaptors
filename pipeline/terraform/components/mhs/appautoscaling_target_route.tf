# The autoscaling target that configures autoscaling for the MHS route ECS service.
resource "aws_appautoscaling_target" "mhs_route_autoscaling_target" {
  max_capacity = var.mhs_route_service_maximum_instance_count
  min_capacity = var.mhs_route_service_minimum_instance_count
  resource_id = "service/${aws_ecs_cluster.mhs_cluster.name}/${aws_ecs_service.mhs_route_service.name}"
  role_arn = var.task_scaling_role_arn
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace = "ecs"
}
