variable "project_id" {
	type = string
}

variable "docker_lab_version" {
  type = string
}

variable "img_version" {
  type = string
}

variable "zone" {
	type = string
	default = "us-east1-c"
}

variable "disk_type" {
	type = string
	default = "pd-standard"
}

variable "machine_type" {
	type = string
	default = "n1-standard-1"
}

variable "docker_lab_image" {
  type = string
  default = "nuxion/labfunctions"
}

variable "docker_mirror" {
  type = string
  default = ""
}
