output "public_ip" {
  value = aws_instance.vllm_nexus.public_ip
}

output "ssh_command" {
  value = "ssh -i <your-key.pem> ubuntu@${aws_instance.vllm_nexus.public_ip}"
}
