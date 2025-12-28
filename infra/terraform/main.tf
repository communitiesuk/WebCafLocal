resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_container_registry" "main" {
  name                = var.name_prefix
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = "${var.name_prefix}kv"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Purge",
      "Recover",
    ]
  }
}

resource "random_password" "postgres_admin" {
  length           = 24
  special          = true
  override_special = "-_%@"
}

resource "random_password" "django_secret_key" {
  length           = 50
  special          = true
  override_special = "-_"
}

resource "azurerm_key_vault_secret" "postgres_admin_password" {
  name         = "postgres-admin-password"
  value        = random_password.postgres_admin.result
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "database_url" {
  name         = "database-url"
  value        = "postgresql://${var.postgres_admin_user}:${azurerm_key_vault_secret.postgres_admin_password.value}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/webcaf?sslmode=require"
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "django_secret_key" {
  name         = "django-secret-key"
  value        = random_password.django_secret_key.result
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "oidc_client_secret" {
  name         = "oidc-client-secret"
  value        = var.oidc_client_secret
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = var.name_prefix
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = var.postgres_version
  administrator_login    = var.postgres_admin_user
  administrator_password = azurerm_key_vault_secret.postgres_admin_password.value
  sku_name               = var.postgres_sku_name
  storage_mb             = var.postgres_storage_mb
  zone                   = "1"

  authentication {
    password_auth_enabled = true
  }
}

resource "azurerm_postgresql_flexible_server_database" "webcaf" {
  name      = "webcaf"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "allow-azure"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.name_prefix}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${var.name_prefix}-env"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

resource "azurerm_container_app" "main" {
  name                         = var.webapp_name
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = "System"
  }

  secret {
    name  = "django-secret-key"
    value = azurerm_key_vault_secret.django_secret_key.value
  }

  secret {
    name  = "database-url"
    value = azurerm_key_vault_secret.database_url.value
  }

  secret {
    name  = "oidc-client-secret"
    value = azurerm_key_vault_secret.oidc_client_secret.value
  }

  template {
    container {
      name   = "webcaf"
      image  = "${azurerm_container_registry.main.login_server}/webcaf:latest"
      cpu    = 0.5
      memory = "1Gi"

      command = ["/bin/sh", "-c"]
      args    = ["python manage.py migrate && gunicorn webcaf.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --access-logfile -"]

      env {
        name  = "DJANGO_SETTINGS_MODULE"
        value = "webcaf.settings"
      }

      env {
        name  = "DEBUG"
        value = "False"
      }

      env {
        name  = "ENVIRONMENT"
        value = "prod"
      }

      env {
        name  = "SSO_MODE"
        value = "external"
      }

      env {
        name  = "ALLOWED_HOSTS"
        value = var.domain_name
      }

      env {
        name  = "DOMAIN_NAME"
        value = var.domain_name
      }

      env {
        name  = "LOGOUT_REDIRECT_URL"
        value = "https://${var.domain_name}/"
      }

      env {
        name  = "USE_X_FORWARDED_HOST"
        value = "True"
      }

      env {
        name  = "OIDC_RP_CLIENT_ID"
        value = var.oidc_client_id
      }

      env {
        name        = "OIDC_RP_CLIENT_SECRET"
        secret_name = "oidc-client-secret"
      }

      env {
        name  = "OIDC_OP_AUTHORIZATION_ENDPOINT"
        value = "https://login.microsoftonline.com/2062bf1d-f9d8-4916-afd0-ca3624f1b2be/oauth2/v2.0/authorize"
      }

      env {
        name  = "OIDC_OP_TOKEN_ENDPOINT"
        value = "https://login.microsoftonline.com/2062bf1d-f9d8-4916-afd0-ca3624f1b2be/oauth2/v2.0/token"
      }

      env {
        name  = "OIDC_OP_USER_ENDPOINT"
        value = "https://graph.microsoft.com/oidc/userinfo"
      }

      env {
        name  = "OIDC_OP_JWKS_ENDPOINT"
        value = "https://login.microsoftonline.com/2062bf1d-f9d8-4916-afd0-ca3624f1b2be/discovery/v2.0/keys"
      }

      env {
        name  = "OIDC_OP_LOGOUT_ENDPOINT"
        value = "https://login.microsoftonline.com/2062bf1d-f9d8-4916-afd0-ca3624f1b2be/oauth2/v2.0/logout"
      }

      env {
        name  = "ENABLED_2FA"
        value = "False"
      }

      env {
        name        = "SECRET_KEY"
        secret_name = "django-secret-key"
      }

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.main.identity[0].principal_id
}
