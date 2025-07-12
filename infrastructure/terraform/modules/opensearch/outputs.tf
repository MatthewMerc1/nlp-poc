# OpenSearch Module Outputs

output "domain_id" {
  description = "The ID of the OpenSearch domain"
  value       = aws_opensearch_domain.main.domain_id
}

output "domain_name" {
  description = "The name of the OpenSearch domain"
  value       = aws_opensearch_domain.main.domain_name
}

output "domain_arn" {
  description = "The ARN of the OpenSearch domain"
  value       = aws_opensearch_domain.main.arn
}

output "domain_endpoint" {
  description = "The endpoint of the OpenSearch domain"
  value       = aws_opensearch_domain.main.endpoint
}

output "kibana_endpoint" {
  description = "The OpenSearch Dashboard endpoint of the OpenSearch domain"
  value       = aws_opensearch_domain.main.dashboard_endpoint
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_id" {
  description = "The ID of the private subnet"
  value       = aws_subnet.private.id
}

output "security_group_id" {
  description = "The ID of the OpenSearch security group"
  value       = aws_security_group.opensearch.id
}

output "bastion_public_ip" {
  description = "Public IP of the bastion host"
  value       = aws_instance.bastion.public_ip
}

output "bastion_private_ip" {
  description = "Private IP of the bastion host"
  value       = aws_instance.bastion.private_ip
} 