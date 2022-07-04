packer {
  required_plugins {
    googlecompute = {
      version = ">= 0.0.1"
      source  = "github.com/hashicorp/googlecompute"
    }
  }
}

source "googlecompute" "nvidia_docker" {
  project_id        = var.project_id
  source_image      = "debian-11-bullseye-v20220406"
  ssh_username      = "op"
  zone              = var.zone
  disk_size         = 20
  disk_type         = var.disk_type
  image_name        = "lab-nvidia-${legacy_isotime("2006-01-02")}"
  image_description = "Labfunctions agent with NVIDIA/GPU support"
  machine_type      = "n1-standard-1"
  accelerator_type  = "projects/${var.project_id}/zones/${var.zone}/acceleratorTypes/nvidia-tesla-t4"
  accelerator_count = 1
  on_host_maintenance = "TERMINATE" # needed for instances with gpu 
}

build {
  sources = ["sources.googlecompute.nvidia_docker"]
  provisioner "shell" {
    inline = [
      "curl -Ls https://raw.githubusercontent.com/nuxion/cloudscripts/1442b4a3cbf027e64b9b58e453fb06c480fe3414/install.sh | sh",
      "sudo cscli -i nvidia-docker",
      "sudo usermod -aG docker `echo $USER`",
      "sudo usermod -aG op `echo $USER`",
      "sudo docker pull ${var.docker_lab_image}:${var.docker_lab_version}"
    ]
  }
}
