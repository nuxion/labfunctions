packer {
  required_plugins {
    googlecompute = {
      version = ">= 0.0.1"
      source  = "github.com/hashicorp/googlecompute"
    }
  }
}

source "googlecompute" "labagent" {
  project_id        = var.project_id
  source_image      = "debian-11-bullseye-v20220406"
  ssh_username      = "op"
  zone              = var.zone
  disk_size         = 20
  disk_type         = var.disk_type
  image_name        = "lab-agent-${legacy_isotime("2006-01-02")}"
  image_description = "Labfunctions default agent "
  machine_type      = "e2-micro"
}

build {
  sources = ["sources.googlecompute.labagent"]
  provisioner "shell" {
    inline = [
      "curl -Ls https://raw.githubusercontent.com/nuxion/cloudscripts/1442b4a3cbf027e64b9b58e453fb06c480fe3414/install.sh | sh",
      "sudo cscli -i docker",
      "sudo usermod -aG docker `echo $USER`",
      "sudo usermod -aG op `echo $USER`",
      "sudo docker pull ${var.docker_lab_image}:${var.docker_lab_version}"
    ]
  }
}
