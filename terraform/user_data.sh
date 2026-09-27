#!/bin/bash
set -e
# Driver, Docker, and NVIDIA Container Toolkit already ship on this AMI —
# just make sure the default user can run docker without sudo.
usermod -aG docker ubuntu
systemctl enable --now docker
