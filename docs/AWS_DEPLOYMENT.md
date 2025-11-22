# AWS Deployment Guide

This guide covers deploying the Vote With Your Feet polling application to AWS.

## Prerequisites

- AWS Account
- Docker installed locally
- AWS CLI configured
- Domain name (optional, for HTTPS)

## Environment Variables

Create a `.env` file with the following variables:

```bash
ADMIN_SECRET=your-secure-secret-here
DATABASE_URL=sqlite:///votes.db
SECRET_KEY=your-flask-secret-key
```

## Deployment Option 1: AWS Lightsail (Recommended for Simple Deployment)

**Cost**: $5-10/month

### Steps:

1. **Create a Lightsail Container Service**
   ```bash
   aws lightsail create-container-service \
     --service-name vote-poll \
     --power small \
     --scale 1
   ```

2. **Build and Push Docker Image**
   ```bash
   docker build -t vote-poll:latest .
   aws lightsail push-container-image \
     --service-name vote-poll \
     --label vote-poll \
     --image vote-poll:latest
   ```

3. **Deploy the Container**
   - Go to Lightsail Console
   - Select your container service
   - Create a deployment with the pushed image
   - Set environment variables: `ADMIN_SECRET`, `DATABASE_URL`, `SECRET_KEY`
   - Configure port 5000 as public endpoint
   - Deploy

4. **Access Your Application**
   - Lightsail will provide a public URL
   - Admin interface: `https://your-url.amazonaws.com/admin?secret=YOUR_SECRET`
   - Display interface: `https://your-url.amazonaws.com/display`
   - Voting API: `https://your-url.amazonaws.com/api/vote`

## Deployment Option 2: EC2 with Docker

**Cost**: $5-20/month (t2.micro/t2.small)

### Steps:

1. **Launch EC2 Instance**
   - AMI: Amazon Linux 2023 or Ubuntu 22.04
   - Instance type: t2.micro or t2.small
   - Security group: Allow ports 22, 80, 443, 5000

2. **Install Docker**
   ```bash
   # Amazon Linux 2023
   sudo yum update -y
   sudo yum install docker -y
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -a -G docker ec2-user

   # Ubuntu
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Clone Repository and Deploy**
   ```bash
   git clone <your-repo-url>
   cd vote_with_your_feet

   # Create .env file
   echo "ADMIN_SECRET=your-secret" > .env
   echo "DATABASE_URL=sqlite:///votes.db" >> .env
   echo "SECRET_KEY=your-key" >> .env

   # Run with docker-compose
   docker-compose up -d
   ```

4. **Configure Nginx (Optional, for production)**
   ```bash
   sudo apt install nginx -y
   ```

   Create `/etc/nginx/sites-available/vote-poll`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

## Deployment Option 3: ECS Fargate

**Cost**: $15-30/month

### Steps:

1. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name vote-poll-cluster
   ```

2. **Push Image to ECR**
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name vote-poll

   # Get login token
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin \
     <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and push
   docker build -t vote-poll .
   docker tag vote-poll:latest \
     <account-id>.dkr.ecr.us-east-1.amazonaws.com/vote-poll:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/vote-poll:latest
   ```

3. **Create Task Definition**
   - Use ECS Console or CLI
   - Configure container with environment variables
   - Allocate 512 CPU units, 1GB memory
   - Map port 5000

4. **Create Service**
   - Launch type: Fargate
   - Configure Application Load Balancer
   - Target port: 5000

5. **Optional: Use EFS for SQLite Persistence**
   - Create EFS file system
   - Mount to `/app/data` in task definition
   - Update DATABASE_URL to use mounted path

## Security Configuration

### Security Group Rules

**For EC2/Lightsail:**
- Port 22 (SSH): Your IP only
- Port 80 (HTTP): 0.0.0.0/0
- Port 443 (HTTPS): 0.0.0.0/0
- Port 5000: 0.0.0.0/0 (or behind load balancer)

### Secrets Management

**Store secrets in AWS Secrets Manager:**

```bash
# Create secret
aws secretsmanager create-secret \
  --name vote-poll/admin-secret \
  --secret-string "your-admin-secret"

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id vote-poll/admin-secret \
  --query SecretString --output text
```

**Or use AWS Systems Manager Parameter Store:**

```bash
aws ssm put-parameter \
  --name /vote-poll/admin-secret \
  --value "your-admin-secret" \
  --type SecureString
```

### HTTPS with AWS Certificate Manager

1. **Request Certificate**
   - Use AWS Certificate Manager
   - Validate domain ownership

2. **Configure Load Balancer**
   - Add HTTPS listener (port 443)
   - Attach certificate
   - Redirect HTTP to HTTPS

## Database Options

### SQLite (Default)

- Good for: Small deployments, single instance
- Persistence: Mount volume or use EFS
- Backup: Periodic copies to S3

```bash
# Backup script
aws s3 cp votes.db s3://your-bucket/backups/votes-$(date +%Y%m%d).db
```

### PostgreSQL on RDS

- Good for: Production, multiple instances
- Create RDS instance (db.t3.micro: ~$15/month)

```bash
# Update .env
DATABASE_URL=postgresql://user:pass@your-rds-endpoint:5432/votedb
```

## IP Restriction (Optional)

To restrict admin access by IP, add to security group or use Nginx:

```nginx
location /admin {
    allow 203.0.113.0/24;  # Your office IP range
    deny all;
    proxy_pass http://localhost:5000;
}
```

## Monitoring

### CloudWatch Logs

Configure container to send logs to CloudWatch:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Health Checks

Add health check endpoint:

```python
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp votes.db "backups/votes_$DATE.db"
aws s3 cp "backups/votes_$DATE.db" s3://your-backup-bucket/
```

Run with cron:
```bash
0 */6 * * * /path/to/backup.sh
```

## Scaling Considerations

For high traffic:
1. Use RDS PostgreSQL instead of SQLite
2. Deploy multiple ECS tasks behind ALB
3. Use ElastiCache for session management
4. Consider API Gateway for rate limiting

## Cost Estimates

- **Lightsail**: $5-10/month (simplest)
- **EC2 t2.micro**: $8/month + $2 data transfer
- **ECS Fargate**: $15-30/month
- **RDS db.t3.micro**: $15/month
- **ALB**: $16/month + data transfer

## Support

For issues or questions, refer to AWS documentation:
- [Lightsail Containers](https://aws.amazon.com/lightsail/features/containers/)
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [EC2 User Guide](https://docs.aws.amazon.com/ec2/)

