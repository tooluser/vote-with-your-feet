# AWS Lightsail Deployment Guide

Deploy Vote With Your Feet to AWS Lightsail with persistent SQLite storage and free HTTPS via Let's Encrypt.

**Cost**: ~$5/month
**Traffic capacity**: Easily handles 1,000+ requests/day
**Time to deploy**: ~30 minutes

---

## Prerequisites

- AWS Account (create one at [aws.amazon.com](https://aws.amazon.com))
- A domain name pointed to your server (for HTTPS)
- SSH client (Terminal on Mac/Linux, or PuTTY on Windows)

---

## Step 1: Create a Lightsail Instance

1. Go to [Lightsail Console](https://lightsail.aws.amazon.com)

2. Click **Create instance**

3. Configure the instance:
   - **Region**: Choose one close to your users
   - **Platform**: Linux/Unix
   - **Blueprint**: OS Only → **Ubuntu 22.04 LTS**
   - **Instance plan**: $5/month (1 GB RAM, 1 vCPU, 40 GB SSD)
   - **Instance name**: `vote-poll`

4. Click **Create instance**

5. Wait ~2 minutes for the instance to start (status: "Running")

---

## Step 2: Configure Networking

### Open Required Ports

1. In Lightsail console, click your instance name
2. Go to **Networking** tab
3. Under **IPv4 Firewall**, add these rules:
   - **HTTPS** (TCP 443) — for secure web traffic
   - **Custom** (TCP 8080) — optional, for direct access during setup

Your firewall should now allow: SSH (22), HTTP (80), HTTPS (443)

### Attach a Static IP (Required for Domain)

1. In the **Networking** tab, scroll to **Public IP**
2. Click **Attach static IP**
3. Create a new static IP, name it `vote-poll-ip`
4. Note this IP address — you'll need it for DNS

---

## Step 3: Point Your Domain to the Server

In your domain registrar's DNS settings, create an **A record**:

| Type | Name | Value |
|------|------|-------|
| A | @ (or subdomain like `vote`) | YOUR_STATIC_IP |

DNS propagation takes 5-30 minutes. Verify with:

```bash
dig +short yourdomain.com
```

---

## Step 4: Connect to Your Server

1. In Lightsail console, click your instance
2. Click **Connect using SSH** (browser-based), or:

```bash
# Download your SSH key from Lightsail console (Account → SSH keys)
ssh -i ~/LightsailDefaultKey.pem ubuntu@YOUR_STATIC_IP
```

---

## Step 5: Install Docker

Run these commands on your server:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose

# Start Docker and enable on boot
sudo systemctl start docker
sudo systemctl enable docker

# Add ubuntu user to docker group (avoids needing sudo)
sudo usermod -aG docker ubuntu

# Apply group change (or log out and back in)
newgrp docker
```

Verify Docker works:

```bash
docker --version
```

---

## Step 6: Deploy the Application

### Clone and Configure

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/vote_with_your_feet.git
cd vote_with_your_feet

# Create data directory for persistent database
mkdir -p data

# Create environment file with secure secrets
cat > .env << 'EOF'
ADMIN_SECRET=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING
SECRET_KEY=CHANGE_THIS_TO_ANOTHER_RANDOM_STRING
EOF
```

Generate secure random strings for the secrets:

```bash
# Generate random secrets (copy these into your .env file)
openssl rand -hex 32
openssl rand -hex 32
```

### Start the Application

```bash
docker-compose up -d
```

Verify it's running:

```bash
docker-compose ps
curl http://localhost:8080/health
```

You should see `{"status": "healthy"}`.

---

## Step 7: Set Up Nginx and Let's Encrypt (HTTPS)

### Install Nginx and Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Configure Nginx

```bash
sudo tee /etc/nginx/sites-available/vote-poll << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for live updates)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
```

Replace `YOUR_DOMAIN.com` with your actual domain:

```bash
sudo sed -i 's/YOUR_DOMAIN.com/yourdomain.com/g' /etc/nginx/sites-available/vote-poll
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/vote-poll /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Obtain SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com
```

Certbot will:

- Verify domain ownership
- Obtain certificate from Let's Encrypt
- Configure Nginx for HTTPS
- Set up auto-renewal

When prompted:

- Enter your email for renewal notices
- Agree to terms of service
- Choose to redirect HTTP to HTTPS (recommended)

### Verify HTTPS

Visit `https://yourdomain.com` — you should see the app with a valid certificate.

---

## Step 8: Set Up Automatic Database Backups

### Create Backup Script

```bash
sudo tee /home/ubuntu/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/home/ubuntu/backups
mkdir -p $BACKUP_DIR

# Copy database (SQLite safe copy while app is running)
cp /home/ubuntu/vote_with_your_feet/data/votes.db "$BACKUP_DIR/votes_$DATE.db"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "votes_*.db" -mtime +7 -delete

echo "Backup completed: votes_$DATE.db"
EOF

chmod +x /home/ubuntu/backup-db.sh
```

### Schedule Daily Backups

```bash
# Add cron job for daily backup at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /home/ubuntu/backup-db.sh >> /home/ubuntu/backup.log 2>&1") | crontab -
```

### Optional: Backup to S3

For off-site backups, install AWS CLI and sync to S3:

```bash
sudo apt install -y awscli
aws configure  # Enter your AWS credentials

# Add to backup script:
# aws s3 cp "$BACKUP_DIR/votes_$DATE.db" s3://your-backup-bucket/vote-poll/
```

---

## Step 9: Configure Auto-Start on Reboot

Docker Compose containers restart automatically (`restart: unless-stopped` in docker-compose.yml).

Verify Nginx starts on boot:

```bash
sudo systemctl enable nginx
```

---

## Step 10: Test Your Deployment

### Access Points

| Interface | URL |
|-----------|-----|
| Voting Display | `https://yourdomain.com/display` |
| Admin Panel | `https://yourdomain.com/admin?secret=YOUR_ADMIN_SECRET` |
| Health Check | `https://yourdomain.com/health` |
| Vote API | `POST https://yourdomain.com/api/vote` |

### Quick Test

```bash
# Check health endpoint
curl https://yourdomain.com/health

# Submit a test vote
curl -X POST https://yourdomain.com/api/vote \
  -H "Content-Type: application/json" \
  -d '{"zone": 1}'
```

---

## Maintenance

### View Logs

```bash
cd ~/vote_with_your_feet
docker-compose logs -f        # Application logs
sudo tail -f /var/log/nginx/access.log  # Web access logs
```

### Update Application

```bash
cd ~/vote_with_your_feet
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Restart Services

```bash
docker-compose restart         # Restart app
sudo systemctl restart nginx   # Restart Nginx
```

### Renew SSL Certificate

Certbot auto-renews certificates. To manually renew:

```bash
sudo certbot renew --dry-run   # Test renewal
sudo certbot renew             # Actually renew
```

### Check Disk Space

```bash
df -h
```

The $5 Lightsail instance has 40 GB — plenty for SQLite and logs.

---

## Troubleshooting

### App Not Responding

```bash
docker-compose ps              # Check container status
docker-compose logs --tail=50  # Check recent logs
docker-compose restart         # Restart container
```

### 502 Bad Gateway

Nginx can't reach the app:

```bash
curl http://localhost:8080/health  # Test app directly
docker-compose up -d               # Ensure container is running
```

### Certificate Issues

```bash
sudo certbot certificates          # Check certificate status
sudo certbot renew --force-renewal # Force renewal if needed
```

### Database Issues

```bash
# Check database file exists and has data
ls -la ~/vote_with_your_feet/data/
sqlite3 ~/vote_with_your_feet/data/votes.db ".tables"
```

---

## Security Checklist

- [ ] Changed `ADMIN_SECRET` to a secure random string
- [ ] Changed `SECRET_KEY` to a secure random string
- [ ] HTTPS working (green padlock in browser)
- [ ] SSH key downloaded and stored securely
- [ ] Firewall allows only ports 22, 80, 443
- [ ] Backups configured and tested

---

## Cost Breakdown

| Item | Monthly Cost |
|------|-------------|
| Lightsail instance (1GB) | $5.00 |
| Static IP (attached) | Free |
| Let's Encrypt SSL | Free |
| 40 GB SSD storage | Included |
| 2 TB data transfer | Included |
| **Total** | **$5.00** |

For ~1,000 requests/day, the $5 instance is more than sufficient. The 2 TB transfer allowance covers roughly 20 million page loads per month.

---

## Alternative: Upgrade Path

If you outgrow the $5 instance:

1. **$10 instance** (2 GB RAM): Handles 10,000+ requests/day
2. **Add RDS PostgreSQL**: For multi-instance deployments
3. **Load balancer + multiple instances**: For high availability

For this application's expected load, the $5 instance should serve you well indefinitely.
