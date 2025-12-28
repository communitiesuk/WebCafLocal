variable "location" {
  type    = string
  default = "uksouth"
}

variable "resource_group_name" {
  type    = string
  default = "webcaflocalpoc-rg"
}

variable "name_prefix" {
  type    = string
  default = "webcaflocalpoc"
}

variable "postgres_admin_user" {
  type    = string
  default = "webcafadmin"
}

variable "postgres_version" {
  type    = string
  default = "15"
}

variable "postgres_sku_name" {
  type    = string
  default = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  type    = number
  default = 32768
}

variable "domain_name" {
  type    = string
  default = "localhost"
}

variable "oidc_client_id" {
  type = string
}

variable "oidc_client_secret" {
  type      = string
  sensitive = true
}

variable "webapp_name" {
  type    = string
  default = "webcaflocalpoc"
}
