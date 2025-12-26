# BrityMail Service - Server Integration Guide

**Version:** 1.0  
**Last Updated:** December 4, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Security Setup](#security-setup)
6. [Service Management](#service-management)
7. [API Documentation](#api-documentation)
8. [Web Interface](#web-interface)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## 🎯 Overview

BrityMail Service is a multi-account email forwarding service that integrates with Brityworks email platform. It provides:

- **SMTP Server** - Receives emails on port 25
- **REST API** - FastAPI-based service on port 8000
- **Web Management Interface** - PHP-based admin panel
- **Multi-Account Support** - Manage multiple Brityworks accounts
- **Secure Authentication** - API key and password protection

---

## 💻 System Requirements

### Operating System
- Linux (CentOS/RHEL/Rocky Linux recommended)
- Root access required for installation

### Software Dependencies
- **Python 3.8+**
- **Apache/httpd** (for web interface)
- **PHP 7.4+** (for admin panel)
- **pip** (Python package manager)

### Network Requirements
- Port **25** - SMTP server
- Port **8000** - FastAPI REST API
- Port **80/443** - Web interface (Apache)

### Firewall Configuration
```bash
# Open required ports
firewall-cmd --permanent --add-port=25/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

---

## 🚀 Installation Steps

### Step 1: Install System Dependencies

```bash
# Update system
yum update -y

# Install Python 3 and pip
yum install -y python3 python3-pip

# Install Apache and PHP
yum install -y httpd php php-json php-session

# Enable and start Apache
systemctl enable httpd
systemctl start httpd
```

### Step 2: Create Application Directory

```bash
# Create directory
mkdir -p /var/www/britymailService
cd /var/www/britymailService

# Set ownership
chown -R root:root /var/www/britymailService
```

### Step 3: Upload Application Files

Upload the following files to `/var/www/britymailService/`:
- `main.py` - FastAPI application
- `manage_accounts.php` - Web admin interface
- `accounts.json` - Account configuration
- `requirements.txt` - Python dependencies

### Step 4: Install Python Dependencies

```bash
cd /var/www/britymailService
pip3 install -r requirements.txt
```

**Dependencies installed:**
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `httpx==0.25.1` - HTTP client
- `pydantic==2.5.0` - Data validation
- `aiosmtpd==1.4.4.post2` - SMTP server

### Step 5: Verify Installation

```bash
# Check Python version
python3 --version

# Verify dependencies
pip3 list | grep -E "fastapi|uvicorn|httpx|pydantic|aiosmtpd"

# Check Apache status
systemctl status httpd
```

---

## ⚙️ Configuration

### 1. Configure accounts.json

The `accounts.json` file contains Brityworks account credentials:

```json
[
  {
    "account_id": "account_1",
    "email": "user@brityworks.com",
    "display_name": "Account 1",
    "is_selected": true,
    "cookies": {
      "SCOUTER": "...",
      "EP_LOGINID": "..."
    },
    "headers": {
      "accept": "application/json",
      "content-type": "application/json;charset=UTF-8"
    }
  }
]
```

**Important:** Set `is_selected: true` for accounts you want to use for sending emails.

### 2. Set File Permissions

```bash
# Secure accounts.json (root only)
chmod 600 /var/www/britymailService/accounts.json
chown root:root /var/www/britymailService/accounts.json

# Set PHP file permissions
chmod 644 /var/www/britymailService/manage_accounts.php
```

### 3. Configure Apache

Create `/etc/httpd/conf.d/britymailService.conf`:

```apache
<Directory "/var/www/britymailService">
    Options -Indexes
    AllowOverride All
    Require all granted
    
    # Block direct access to sensitive files
    <FilesMatch "^(accounts\.json|main\.py|requirements\.txt|\.env)$">
        Order allow,deny
        Deny from all
    </FilesMatch>
    
    # Allow only PHP files to be served
    <FilesMatch "\.php$">
        Require all granted
    </FilesMatch>
</Directory>
```

Reload Apache:
```bash
systemctl reload httpd
```

### 4. Create .htaccess (Optional)

Create `/var/www/britymailService/.htaccess`:

```apache
# Block access to sensitive files
<FilesMatch "^(accounts\.json|\.env|config\.json|main\.py|requirements\.txt)$">
    Order allow,deny
    Deny from all
</FilesMatch>

# Disable directory listing
Options -Indexes
```

---

## 🔒 Security Setup

### 1. File System Protection

```bash
# Set restrictive permissions on accounts.json
chmod 600 /var/www/britymailService/accounts.json
chown root:root /var/www/britymailService/accounts.json

# Verify permissions
ls -la /var/www/britymailService/accounts.json
# Expected: -rw------- 1 root root
```

### 2. Web Server Protection

Test that sensitive files are blocked:

```bash
# Should return 403 Forbidden
curl http://YOUR_SERVER_IP/britymailService/accounts.json
curl http://YOUR_SERVER_IP/britymailService/main.py
```

### 3. Authentication Credentials

**Admin Password:** `LORDLAVA12`  
**API Key:** `LORDLAVA12`

**⚠️ IMPORTANT:** Change these credentials in production!

**To change the password:**
1. Edit `manage_accounts.php`
2. Find: `$ADMIN_PASSWORD = 'LORDLAVA12';`
3. Replace with your secure password

**To change the API key:**
1. Edit `main.py`
2. Find: `ADMIN_API_KEY = "LORDLAVA12"`
3. Replace with your secure API key

### 4. Session Security

- **Session Timeout:** 1 hour
- **Session Storage:** Server-side PHP sessions
- **Cookie:** PHPSESSID (httponly)

---

## 🔧 Service Management

### Create Systemd Service

Create `/etc/systemd/system/britymail.service`:

```ini
[Unit]
Description=BrityMail Service - FastAPI Email Forwarder
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/britymailService
ExecStart=/usr/bin/python3 /var/www/britymailService/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable britymail.service

# Start the service
systemctl start britymail.service

# Check status
systemctl status britymail.service
```

### Service Commands

```bash
# Start service
systemctl start britymail.service

# Stop service
systemctl stop britymail.service

# Restart service
systemctl restart britymail.service

# View logs
journalctl -u britymail.service -f

# Check if running
systemctl is-active britymail.service
```

### Manual Start (for testing)

```bash
cd /var/www/britymailService
python3 main.py
```

The service will start:
- **SMTP Server** on port 25
- **REST API** on port 8000

---

## 📡 API Documentation

### Base URL
```
http://YOUR_SERVER_IP:8000
```

### Authentication

All admin operations require the API key header:
```
X-API-Key: LORDLAVA12
```

### Endpoints

#### 1. Health Check
```bash
GET /
# No authentication required
```

#### 2. List Accounts (Public)
```bash
GET /accounts/
# Returns basic info without cookies/headers
```

#### 3. List Accounts (Full Access)
```bash
GET /accounts/?full=true
# Headers: X-API-Key: LORDLAVA12
# Returns complete account data including cookies/headers
```

#### 4. Get Single Account
```bash
GET /accounts/{account_id}?full=true
# Headers: X-API-Key: LORDLAVA12
```

#### 5. Create Account
```bash
POST /accounts/
# Headers: 
#   X-API-Key: LORDLAVA12
#   Content-Type: application/json
# Body: JSON account object
```

#### 6. Update Account
```bash
PUT /accounts/{account_id}
# Headers: 
#   X-API-Key: LORDLAVA12
#   Content-Type: application/json
# Body: JSON account object
```

#### 7. Delete Account
```bash
DELETE /accounts/{account_id}
# Headers: X-API-Key: LORDLAVA12
```

#### 8. Select/Deselect Account
```bash
POST /accounts/{account_id}/select
POST /accounts/{account_id}/deselect
# Headers: X-API-Key: LORDLAVA12
```

### Example API Calls

```bash
# List all accounts with full data
curl -H "X-API-Key: LORDLAVA12" \
  "http://YOUR_SERVER_IP:8000/accounts/?full=true"

# Create new account
curl -X POST \
  -H "X-API-Key: LORDLAVA12" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account_2",
    "email": "user@brityworks.com",
    "display_name": "Account 2",
    "cookies": {...},
    "headers": {...}
  }' \
  "http://YOUR_SERVER_IP:8000/accounts/"

# Select account for sending
curl -X POST \
  -H "X-API-Key: LORDLAVA12" \
  "http://YOUR_SERVER_IP:8000/accounts/account_2/select"
```

**Full API documentation:** See `FULL_CONTROL_API.md`

---

## 🌐 Web Interface

### Access URL
```
http://YOUR_SERVER_IP/britymailService/manage_accounts.php
```

### Login Credentials
- **Password:** `LORDLAVA12`
- **Session:** 1 hour timeout

### Features

#### Account Management
- ✅ View all accounts
- ✅ Add new accounts
- ✅ Edit existing accounts
- ✅ Delete accounts
- ✅ Select/deselect accounts for sending

#### Data Viewing
- ✅ Expandable cookies display
- ✅ Expandable headers display
- ✅ Full JSON view
- ✅ Copy to clipboard functionality

#### Security
- ✅ Password authentication
- ✅ Session timeout (1 hour)
- ✅ Logout functionality
- ✅ Auto-logout on timeout

**Full feature documentation:** See `ADMIN_FEATURES.md`

---

## 🔍 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
journalctl -u britymail.service -n 50
```

**Common issues:**
1. Port 25 or 8000 already in use
   ```bash
   netstat -tulpn | grep -E ':(25|8000)'
   ```

2. Missing Python dependencies
   ```bash
   pip3 install -r requirements.txt
   ```

3. Permission issues
   ```bash
   chmod 600 /var/www/britymailService/accounts.json
   chown root:root /var/www/britymailService/accounts.json
   ```

### Web Interface Not Loading

**Check Apache status:**
```bash
systemctl status httpd
```

**Check Apache error log:**
```bash
tail -f /var/log/httpd/error_log
```

**Verify file permissions:**
```bash
ls -la /var/www/britymailService/
```

### API Returns 403 Forbidden

**Check API key:**
- Ensure you're sending: `X-API-Key: LORDLAVA12`
- Verify the key matches in `main.py`

### Emails Not Sending

**Check account selection:**
```bash
curl -H "X-API-Key: LORDLAVA12" \
  "http://YOUR_SERVER_IP:8000/accounts/?full=true"
```

Ensure at least one account has `"is_selected": true`

**Check service logs:**
```bash
journalctl -u britymail.service -f
```

### Can't Access accounts.json via Web

**This is correct!** The file should return 403 Forbidden for security.

**Test:**
```bash
curl http://YOUR_SERVER_IP/britymailService/accounts.json
# Expected: 403 Forbidden
```

---

## 🛠️ Maintenance

### Update Accounts

**Via Web Interface:**
1. Go to `http://YOUR_SERVER_IP/britymailService/manage_accounts.php`
2. Login with password: `LORDLAVA12`
3. Edit accounts as needed

**Via API:**
```bash
curl -X PUT \
  -H "X-API-Key: LORDLAVA12" \
  -H "Content-Type: application/json" \
  -d @account_data.json \
  "http://YOUR_SERVER_IP:8000/accounts/account_1"
```

**Manual Edit:**
```bash
nano /var/www/britymailService/accounts.json
# Restart service after manual edits
systemctl restart britymail.service
```

### Backup Configuration

```bash
# Backup accounts.json
cp /var/www/britymailService/accounts.json \
   /root/backups/accounts.json.$(date +%Y%m%d)

# Backup entire directory
tar -czf /root/backups/britymailService-$(date +%Y%m%d).tar.gz \
  /var/www/britymailService/
```

### View Logs

```bash
# Service logs
journalctl -u britymail.service -f

# Apache logs
tail -f /var/log/httpd/access_log
tail -f /var/log/httpd/error_log

# Last 100 lines
journalctl -u britymail.service -n 100
```

### Update Dependencies

```bash
cd /var/www/britymailService
pip3 install --upgrade -r requirements.txt
systemctl restart britymail.service
```

### Monitor Service

```bash
# Check if service is running
systemctl is-active britymail.service

# Check service uptime
systemctl status britymail.service

# Monitor in real-time
watch -n 2 'systemctl status britymail.service'
```

---

## 📊 Quick Reference

### Important Files
```
/var/www/britymailService/
├── main.py                    # FastAPI application
├── manage_accounts.php        # Web admin interface
├── accounts.json              # Account configuration (600 permissions)
├── requirements.txt           # Python dependencies
├── SECURITY.md               # Security documentation
├── FULL_CONTROL_API.md       # API documentation
├── ADMIN_FEATURES.md         # Web interface features
└── README.md                 # This file
```

### Configuration Files
```
/etc/httpd/conf.d/britymailService.conf  # Apache configuration
/etc/systemd/system/britymail.service    # Systemd service
/var/www/britymailService/.htaccess      # Web access control
```

### Ports
- **25** - SMTP server
- **8000** - REST API
- **80** - Web interface (Apache)

### Credentials
- **Admin Password:** `LORDLAVA12`
- **API Key:** `LORDLAVA12`

### URLs
- **Web Interface:** `http://YOUR_SERVER_IP/britymailService/manage_accounts.php`
- **API Base:** `http://YOUR_SERVER_IP:8000`
- **Health Check:** `http://YOUR_SERVER_IP:8000/`

### Common Commands
```bash
# Service management
systemctl start britymail.service
systemctl stop britymail.service
systemctl restart britymail.service
systemctl status britymail.service

# View logs
journalctl -u britymail.service -f

# Test API
curl http://YOUR_SERVER_IP:8000/

# Test web access
curl http://YOUR_SERVER_IP/britymailService/manage_accounts.php
```

---

## 🔐 Security Checklist

Before going to production, ensure:

- [ ] Changed default password in `manage_accounts.php`
- [ ] Changed default API key in `main.py`
- [ ] Set `accounts.json` permissions to 600
- [ ] Apache configuration blocks sensitive files
- [ ] Firewall rules configured
- [ ] HTTPS enabled (recommended)
- [ ] Regular backups configured
- [ ] Log monitoring in place
- [ ] Rate limiting configured (recommended)

---

## 📞 Support

For detailed documentation, see:
- **Security:** `SECURITY.md`
- **API Reference:** `FULL_CONTROL_API.md`
- **Admin Features:** `ADMIN_FEATURES.md`

---

**Installation Complete!** 🎉

Your BrityMail Service should now be running and accessible.
