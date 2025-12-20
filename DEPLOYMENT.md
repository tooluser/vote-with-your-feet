# Deployment Guide: Vote With Your Feet

Deploy your polling app to AWS Lightsail VM with custom domain (nowhereville.org) and persistent data storage.

## Prerequisites

- AWS Account with billing enabled
- AWS CLI installed and configured (`aws configure`)
- Domain: nowhereville.org (already owned)
- Access to domain DNS settings
- SSH key pair (we'll create one if needed)

## Overview

We'll deploy using **AWS Lightsail Virtual Machine** which provides:

- Full Ubuntu server with SSH access
- Static IP address (free while attached to instance)
- Persistent storage (data survives restarts and updates)
- Free SSL via Let's Encrypt
- ~$5/month for 1GB RAM, 1 vCPU, 40GB SSD

## Part 1: Prepare Your Application

### 1.1 Create Production Environment File

Create `.env.production` in your project root:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=generate-a-secure-random-string-here
ADMIN_SECRET=your-admin-password-here

# Database (will persist in ./data directory on host)
DATABASE_URL=sqlite:///data/votes.db

# CORS for your domain
CORS_ALLOWED_ORIGINS=https://vote.nowhereville.org
```

**Generate secure keys:**

```bash
# On Mac/Linux
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Run twice to get SECRET_KEY and ADMIN_SECRET
```

### 1.2 Update docker-compose.yml for Production

Your existing `docker-compose.yml` should look like this:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data  # CRITICAL: Persists database on host filesystem
    env_file:
      - .env.production
    restart: unless-stopped
```

The `volumes` line ensures your SQLite database persists on the VM's filesystem, surviving container restarts and updates.

### 1.3 Update Application for Production (Optional)

If not already present, add to `app/__init__.py` after socketio initialization:

```python
# Configure SocketIO for production
socketio.init_app(app,
    cors_allowed_origins=os.getenv('CORS_ALLOWED_ORIGINS', '*').split(','),
    async_mode='threading',
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)
```

### 1.4 Test Docker Build Locally (Optional)

```bash
# Build and test
docker-compose up

# Verify at http://localhost:8080/display
# Then stop with Ctrl+C
docker-compose down
```

## Part 2: Create Lightsail VM Instance

### 2.1 Create SSH Key Pair (if you don't have one)

```bash
# Create new key pair in Lightsail
aws lightsail create-key-pair \
  --key-pair-name vote-key \
  --query 'privateKeyBase64' \
  --output text > ~/.ssh/vote-key.pem

# Set correct permissions
chmod 400 ~/.ssh/vote-key.pem
```

Or use an existing key pair:

```bash
# List your existing keys
aws lightsail get-key-pairs
```

### 2.2 Create Lightsail Instance

```bash
# Create Ubuntu 22.04 instance
aws lightsail create-instances \
  --instance-names vote-with-feet \
  --availability-zone us-east-1a \
  --blueprint-id ubuntu_22_04 \
  --bundle-id nano_3_0 \
  --key-pair-name vote-key

# Wait for instance to be running (takes ~2 minutes)
aws lightsail get-instance \
  --instance-name vote-with-feet \
  --query 'instance.state.name'
```

**Bundle options:**

- `nano_3_0`: $5/mo (512MB RAM, 1 vCPU, 20GB SSD) - **recommended**
- `micro_3_0`: $7/mo (1GB RAM, 1 vCPU, 40GB SSD)
- `small_3_0`: $12/mo (2GB RAM, 1 vCPU, 60GB SSD)

### 2.3 Allocate and Attach Static IP

```bash
# Create static IP
aws lightsail allocate-static-ip \
  --static-ip-name vote-static-ip

# Attach to instance
aws lightsail attach-static-ip \
  --static-ip-name vote-static-ip \
  --instance-name vote-with-feet

# Get the IP address
aws lightsail get-static-ip \
  --static-ip-name vote-static-ip \
  --query 'staticIp.ipAddress' \
  --output text
```

**Save this IP address** - you'll need it for DNS configuration.

### 2.4 Open Firewall Ports

```bash
# Open HTTP (port 80)
aws lightsail open-instance-public-ports \
  --instance-name vote-with-feet \
  --port-info fromPort=80,toPort=80,protocol=TCP

# Open HTTPS (port 443)
aws lightsail open-instance-public-ports \
  --instance-name vote-with-feet \
  --port-info fromPort=443,toPort=443,protocol=TCP

# SSH (port 22) is open by default
```

## Part 3: Setup Server and Deploy Application

### 3.1 Connect to Your Instance via SSH

```bash
# Get your instance's IP
IP=$(aws lightsail get-static-ip \
  --static-ip-name vote-static-ip \
  --query 'staticIp.ipAddress' \
  --output text)

# Connect via SSH
ssh -i ~/.ssh/vote-key.pem ubuntu@$IP
```

**Alternative:** Use Lightsail browser-based SSH:

- Go to [Lightsail Console](https://lightsail.aws.amazon.com/)
- Click on your instance "vote-with-feet"
- Click "Connect using SSH"

### 3.2 Install Docker and Docker Compose on the Server

Once connected to the server, run:

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add ubuntu user to docker group (so you don't need sudo)
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install -y docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
exit
```

Reconnect:

```bash
ssh -i ~/.ssh/vote-key.pem ubuntu@$IP
```

### 3.3 Clone Your Repository or Transfer Files

**Option A: Via Git (if your repo is on GitHub/GitLab):**

```bash
# Install git if needed
sudo apt install -y git

# Clone your repository
git clone https://github.com/yourusername/vote_with_your_feet.git
cd vote_with_your_feet
```

**Option B: Transfer files via SCP (from your local machine):**

```bash
# On your LOCAL machine (not the server), from project directory:
scp -i ~/.ssh/vote-key.pem -r . ubuntu@$IP:~/vote_with_your_feet/

# Then SSH back in
ssh -i ~/.ssh/vote-key.pem ubuntu@$IP
cd vote_with_your_feet
```

### 3.4 Create Production Environment File on Server

```bash
# Create .env.production file
nano .env.production
```

Paste your configuration (use the keys you generated earlier):

```bash
FLASK_ENV=production
SECRET_KEY=your-generated-secret-key-here
ADMIN_SECRET=your-admin-password-here
DATABASE_URL=sqlite:///data/votes.db
CORS_ALLOWED_ORIGINS=https://vote.nowhereville.org
```

Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

### 3.5 Create Data Directory

```bash
# Create directory for persistent database
mkdir -p data
```

### 3.6 Start Application with Docker Compose

```bash
# Build and start containers
docker-compose up -d

# Check if running
docker-compose ps

# View logs
docker-compose logs -f
```

Press `Ctrl+C` to exit logs (app keeps running).

### 3.7 Verify Application is Running

```bash
# Test locally on server
curl http://localhost:8080/api/display/data

# Should return JSON with poll data (or empty if no polls yet)
```

**Test from your local machine:**

```bash
# Replace with your actual IP
curl http://YOUR_IP:8080/api/display/data
```

⚠️ **Note:** At this point, you can access via HTTP on port 8080, but NOT yet on standard HTTP/HTTPS ports. We'll set up Nginx reverse proxy with SSL next.

## Part 4: Configure Domain and SSL

### 4.1 Point Your Domain to the Server

**Go to your domain registrar (wherever nowhereville.org is hosted) and add an A record:**

- **Type:** `A`
- **Name:** `vote` (creates vote.nowhereville.org)
- **Value:** Your static IP address from Part 2.3
- **TTL:** `3600` (1 hour) or use default

**Wait 5-15 minutes** for DNS propagation.

**Verify DNS is working:**

```bash
# From your local machine
dig vote.nowhereville.org

# Or use online tool: https://www.whatsmydns.net/
# Enter: vote.nowhereville.org
```

### 4.2 Install Nginx as Reverse Proxy

Back on your server (via SSH):

```bash
# Install Nginx
sudo apt install -y nginx

# Stop default site
sudo systemctl stop nginx
```

### 4.3 Create Nginx Configuration

```bash
# Create config file
sudo nano /etc/nginx/sites-available/vote
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name vote.nowhereville.org;

    # Redirect HTTP to HTTPS (will be enabled after SSL setup)
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }
}
```

Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

Enable the site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/vote /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 4.4 Test HTTP Access

```bash
# From your local machine
curl http://vote.nowhereville.org/api/display/data

# Or visit in browser:
# http://vote.nowhereville.org/display
```

### 4.5 Install Let's Encrypt SSL Certificate

Back on the server:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your email)
sudo certbot --nginx -d vote.nowhereville.org --non-interactive --agree-tos -m your-email@example.com
```

Certbot will:

1. Verify domain ownership
2. Issue SSL certificate
3. Automatically update Nginx config for HTTPS
4. Set up auto-renewal

### 4.6 Update CORS Settings

Update your `.env.production` to use HTTPS:

```bash
cd ~/vote_with_your_feet
nano .env.production
```

Change the CORS line to:

```bash
CORS_ALLOWED_ORIGINS=https://vote.nowhereville.org
```

Restart the application:

```bash
docker-compose restart
```

### 4.7 Test HTTPS Access

```bash
# From your local machine
curl https://vote.nowhereville.org/api/display/data

# Visit in browser:
# https://vote.nowhereville.org/display
```

🎉 Your app is now live with HTTPS!

## Part 5: Verify Deployment and Test Persistence

### 5.1 Test Your Application

Visit these URLs:

- **Display**: <https://vote.nowhereville.org/display>
- **Admin**: <https://vote.nowhereville.org/admin?secret=YOUR_ADMIN_SECRET>
- **API Health**: <https://vote.nowhereville.org/api/display/data>

### 5.2 Test Voting Flow

1. Go to admin interface: `https://vote.nowhereville.org/admin?secret=YOUR_SECRET`
2. Create a poll with a question and two answers
3. Click "Activate" on the poll
4. Open display page: `https://vote.nowhereville.org/display`
5. Cast votes via API or create another poll

Test API vote:

```bash
curl -X POST https://vote.nowhereville.org/api/vote \
  -H "Content-Type: application/json" \
  -d '{"answer": "A"}'
```

### 5.3 Test Data Persistence (Critical!)

This verifies your database survives container restarts:

```bash
# SSH to server
ssh -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP
cd vote_with_your_feet

# Check database file exists
ls -lh data/votes.db

# Restart container
docker-compose restart

# Database should still exist
ls -lh data/votes.db

# Visit admin page - polls should still be there
```

### 5.4 Test WebSocket Real-Time Updates

1. Open display page in one browser tab
2. Open admin or API in another tab
3. Cast a vote
4. Verify display updates instantly without refresh

If WebSockets aren't working:

- Check browser console for errors
- Verify Nginx config has WebSocket proxy settings
- Check CORS settings in `.env.production`

## Part 6: Maintenance and Updates

### 6.1 Update Application Code

When you make changes to your application:

**Option A: Via Git (if using repository):**

```bash
# SSH to server
ssh -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP
cd vote_with_your_feet

# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# View logs to verify
docker-compose logs -f
```

**Option B: Via SCP (manual file transfer):**

```bash
# From your LOCAL machine, in project directory
scp -i ~/.ssh/vote-key.pem -r . ubuntu@YOUR_IP:~/vote_with_your_feet/

# Then SSH and restart
ssh -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP
cd vote_with_your_feet
docker-compose up -d --build
```

**Your database persists** - the `./data` directory is mounted as a volume and survives all updates!

### 6.2 View Logs

```bash
# SSH to server
ssh -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP
cd vote_with_your_feet

# View live logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 6.3 Restart Services

```bash
# Restart application
docker-compose restart

# Restart Nginx
sudo systemctl restart nginx

# Restart Docker daemon (if needed)
sudo systemctl restart docker
```

### 6.4 Check Service Status

```bash
# Check Docker containers
docker-compose ps

# Check Nginx
sudo systemctl status nginx

# Check disk usage
df -h

# Check database size
ls -lh data/votes.db
```

### 6.5 Monitor Resources

```bash
# Check memory and CPU usage
htop  # or 'top'

# Check Docker stats
docker stats

# Check container logs for errors
docker-compose logs | grep -i error
```

## Part 7: Database Backup

Your database is stored at `~/vote_with_your_feet/data/votes.db` on the server and persists across restarts and updates.

### 7.1 Manual Backup

**Download database to your local machine:**

```bash
# From your LOCAL machine
scp -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP:~/vote_with_your_feet/data/votes.db \
  ./backup_$(date +%Y%m%d_%H%M%S).db
```

### 7.2 Automated Backup Script (Optional)

Create a backup script on the server:

```bash
# SSH to server
ssh -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP

# Create backup script
nano ~/backup-db.sh
```

Paste this script:

```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
cp ~/vote_with_your_feet/data/votes.db \
   $BACKUP_DIR/votes_$(date +%Y%m%d_%H%M%S).db

# Keep only last 7 days of backups
find $BACKUP_DIR -name "votes_*.db" -mtime +7 -delete

echo "Backup completed: $(date)"
```

Make executable:

```bash
chmod +x ~/backup-db.sh
```

**Schedule daily backups with cron:**

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /home/ubuntu/backup-db.sh >> /home/ubuntu/backup.log 2>&1
```

### 7.3 Restore from Backup

```bash
# SSH to server
ssh -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP
cd vote_with_your_feet

# Stop application
docker-compose down

# Restore database
cp ~/backups/votes_YYYYMMDD_HHMMSS.db data/votes.db

# Start application
docker-compose up -d
```

### 7.4 Download Backup via Web Interface (Optional)

Add to your Flask app for easy backup download through admin interface.

In `app/routes/admin.py`:

```python
from flask import send_file

@admin_bp.route('/backup', methods=['GET'])
@require_secret
def backup_database():
    """Download database backup"""
    return send_file(
        '../data/votes.db',
        as_attachment=True,
        download_name=f'votes_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    )
```

Then download via:

```bash
curl -o backup.db "https://vote.nowhereville.org/admin/backup?secret=YOUR_SECRET"
```

## Troubleshooting

### Application Won't Start

```bash
# Check Docker logs
docker-compose logs

# Common issues:
# 1. Port 8080 already in use
sudo lsof -i :8080

# 2. Permission issues with data directory
sudo chown -R ubuntu:ubuntu ~/vote_with_your_feet/data

# 3. Environment file not found
ls -la .env.production

# 4. Docker not running
sudo systemctl status docker
```

### Can't Access Website

```bash
# 1. Check Nginx is running
sudo systemctl status nginx

# 2. Check firewall ports
sudo ufw status

# 3. Verify DNS propagation
dig vote.nowhereville.org

# 4. Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# 5. Test local connection
curl http://localhost:8080/api/display/data
```

### WebSockets Not Working

```bash
# 1. Check Nginx WebSocket config
sudo nginx -t
sudo cat /etc/nginx/sites-available/vote | grep -A 5 "Upgrade"

# 2. Check browser console for errors (F12 in browser)

# 3. Verify CORS settings
cat .env.production | grep CORS

# 4. Restart services
docker-compose restart
sudo systemctl restart nginx
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Test renewal (dry run)
sudo certbot renew --dry-run

# Certificate auto-renewal should be set up automatically
sudo systemctl status certbot.timer
```

### Database Issues

```bash
# Check database file exists and has correct permissions
ls -lh ~/vote_with_your_feet/data/votes.db
stat ~/vote_with_your_feet/data/votes.db

# Check database integrity
sqlite3 data/votes.db "PRAGMA integrity_check;"

# View database contents
sqlite3 data/votes.db "SELECT * FROM poll;"
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clear Docker cache
docker system prune -a

# Clear old logs
sudo truncate -s 0 /var/log/nginx/access.log
sudo truncate -s 0 /var/log/nginx/error.log

# Clear old backups
rm ~/backups/votes_old*.db
```

### SSH Connection Issues

```bash
# Verify key permissions
chmod 400 ~/.ssh/vote-key.pem

# Test connection with verbose output
ssh -v -i ~/.ssh/vote-key.pem ubuntu@YOUR_IP

# Use Lightsail browser SSH as backup
# Go to: https://lightsail.aws.amazon.com/
# Click instance > Connect using SSH
```

### High Memory Usage

```bash
# Check memory
free -h

# Check what's using memory
docker stats

# Restart services to free memory
docker-compose restart

# If persistent, upgrade to micro ($7/mo) or small ($12/mo) instance
```

## Cost Estimate

- **Lightsail VM (nano)**: $5/month (512MB RAM, 1 vCPU, 20GB SSD)
- **Static IP**: Free while attached to instance
- **Data Transfer**: First 1TB free per month
- **SSL Certificate**: Free via Let's Encrypt
- **Domain**: Already owned

**Total**: ~$5/month

**Scaling options:**

- Micro instance: $7/mo (1GB RAM)
- Small instance: $12/mo (2GB RAM)

## Upgrading Your Instance (if needed)

If your app needs more resources:

```bash
# Create snapshot for backup
aws lightsail create-instance-snapshot \
  --instance-name vote-with-feet \
  --instance-snapshot-name vote-snapshot

# Create new larger instance from snapshot
aws lightsail create-instances-from-snapshot \
  --instance-names vote-with-feet-upgraded \
  --instance-snapshot-name vote-snapshot \
  --availability-zone us-east-1a \
  --bundle-id micro_3_0

# Attach static IP to new instance
aws lightsail attach-static-ip \
  --static-ip-name vote-static-ip \
  --instance-name vote-with-feet-upgraded

# Delete old instance after verifying
aws lightsail delete-instance --instance-name vote-with-feet
```

## Cleanup (if needed)

To remove everything and stop billing:

```bash
# 1. Delete instance (stops billing)
aws lightsail delete-instance --instance-name vote-with-feet

# 2. Release static IP (if you want to free it up)
aws lightsail release-static-ip --static-ip-name vote-static-ip

# 3. Delete key pair (optional)
aws lightsail delete-key-pair --key-pair-name vote-key
rm ~/.ssh/vote-key.pem

# 4. Remove DNS records from domain registrar
# - Delete the A record for vote.nowhereville.org
```

**Note:** Your local backups will remain on your machine.

## Why This Approach?

### ✅ Advantages of Lightsail VM

1. **True Data Persistence**: SQLite database survives all restarts and updates
2. **Lower Cost**: $5/mo vs $7/mo for container service (or $22/mo with managed DB)
3. **Full Control**: SSH access, can install anything you need
4. **Simpler Architecture**: Direct Docker Compose deployment
5. **Easy Debugging**: Direct access to logs, database, and system
6. **Free SSL**: Let's Encrypt certificate auto-renews
7. **Scalable**: Easy to upgrade instance size or migrate to larger VM

### 🎯 Perfect For

- School projects with real users
- Small to medium traffic applications
- Applications requiring persistent storage
- Developers who want SSH access
- Budget-conscious deployments

## Alternative Deployment Options

If your needs change:

### AWS ECS/Fargate (for production scale)

- Auto-scaling
- Zero server management
- Use RDS for database
- ~$50-100/mo minimum

### Heroku (easiest, no AWS knowledge needed)

- Git push deployment
- PostgreSQL included
- ~$7-25/mo
- Less control

### DigitalOcean App Platform

- Similar to Heroku
- Slightly more control
- ~$5-12/mo

### Railway.app (modern alternative)

- Git-based deployment
- PostgreSQL included
- Pay for usage (~$5-10/mo)

## Support

**For AWS Lightsail issues:**

- [Lightsail Documentation](https://lightsail.aws.amazon.com/ls/docs)
- [AWS Support Console](https://console.aws.amazon.com/support/)
- [Lightsail Forums](https://forums.aws.amazon.com/forum.jspa?forumID=231)

**For Let's Encrypt SSL issues:**

- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Let's Encrypt Community](https://community.letsencrypt.org/)

**For application issues:**

- Check logs: `docker-compose logs`
- Review Flask/SocketIO documentation
- Verify environment variables and CORS settings
- Test WebSocket connection in browser console

**For DNS issues:**

- Use [What's My DNS](https://www.whatsmydns.net/) to check propagation
- Contact your domain registrar's support

## Next Steps

After successful deployment:

1. **Monitor Your Application**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Check logs regularly: `docker-compose logs`

2. **Set Up Backups**
   - Implement automated database backups
   - Test restore procedure

3. **Optimize Performance**
   - Monitor resource usage with `htop`
   - Upgrade instance if needed
   - Add caching if traffic increases

4. **Enhance Security**
   - Regularly update system: `sudo apt update && sudo apt upgrade`
   - Review Nginx security headers
   - Keep Docker images updated

5. **Plan for Scale**
   - If traffic grows, consider:
     - Upgrading to larger instance
     - Moving to managed database (RDS)
     - Adding Redis for session storage
     - Implementing CDN for static assets
