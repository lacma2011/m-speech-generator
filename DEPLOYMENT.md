# Deployment Guide - DigitalOcean

This guide will help you deploy the Voice Generator to DigitalOcean for public access.

**Cost**: ~$24/month (4GB RAM droplet)
**Setup Time**: 20-30 minutes
**Requirements**: DigitalOcean account

---

## Step 1: Create DigitalOcean Account

1. Go to [DigitalOcean.com](https://www.digitalocean.com/)
2. Sign up for a new account
3. **Pro tip**: Search for "DigitalOcean promo code" to get $200 in free credits (valid for 60 days)

---

## Step 2: Create a Droplet

### 2.1 Click "Create" → "Droplets"

### 2.2 Choose Configuration

**Image**:
- Select "Marketplace"
- Search for "Docker"
- Choose **"Docker on Ubuntu 22.04"**

**Droplet Size**:
- Choose "Basic"
- CPU Options: **Regular (4GB RAM / 2 CPUs) - $24/month**
- This is the minimum recommended for XTTS v2

**Datacenter Region**:
- Choose closest to your users (e.g., New York, San Francisco, London)

**Authentication**:
- **Recommended**: SSH Key (more secure)
  - Click "New SSH Key"
  - Paste your public key (run `cat ~/.ssh/id_rsa.pub` on your Mac)
- **Alternative**: Password (simpler but less secure)

**Hostname**:
- Give it a memorable name like "voice-generator"

### 2.3 Click "Create Droplet"

Wait 1-2 minutes for the droplet to be created. You'll get an IP address.

---

## Step 3: Connect to Your Droplet

Open Terminal on your Mac:

```bash
# Replace with your droplet's IP address
ssh root@your.droplet.ip.address

# If using SSH key, you'll connect automatically
# If using password, enter the password sent to your email
```

---

## Step 4: Deploy Your App

### 4.1 Clone Your Repository

```bash
# Install git if needed
apt-get update && apt-get install -y git

# Clone your repo (replace with your repo URL)
git clone https://github.com/your-username/speech_generator.git
cd speech_generator
```

**Don't have a GitHub repo yet?** See the "Alternative: Upload Files" section below.

### 4.2 Start the Application

```bash
# Build the Docker image
docker compose build

# Start the web server (runs in foreground)
docker compose run --rm voice-generator python web_server.py
```

This will:
- ✓ Build the Docker image (takes 5-10 minutes on first run)
- ✓ Download the XTTS v2 model (~1.5GB, one-time)
- ✓ Start the web server on port 5002

You should see:
```
Loading XTTS v2 model on cpu...
Server ready!
Open http://localhost:5002 in your browser
```

---

## Step 5: Access Your App

### Option A: Direct IP Access (Quick Test)

Open your browser and go to:
```
http://your.droplet.ip.address:5002
```

You should see the Voice Generator interface!

### Option B: Use a Custom Domain (Recommended)

#### 5.1 Point Your Domain to Droplet

In your domain registrar (GoDaddy, Namecheap, etc.):
1. Add an **A Record**:
   - Host: `@` (or subdomain like `voice`)
   - Points to: `your.droplet.ip.address`
   - TTL: 3600

Wait 5-10 minutes for DNS to propagate.

#### 5.2 Install Nginx Reverse Proxy

```bash
# Install Nginx
apt-get install -y nginx

# Create Nginx configuration
nano /etc/nginx/sites-available/voice-generator
```

Paste this configuration (replace `yourdomain.com`):

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # Increase timeout for longer voice generation
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Increase max upload size for voice samples
    client_max_body_size 50M;
}
```

Save and exit (Ctrl+X, Y, Enter).

Enable the site:
```bash
# Enable the configuration
ln -s /etc/nginx/sites-available/voice-generator /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

Now visit: `http://yourdomain.com`

#### 5.3 Add HTTPS (Optional but Recommended)

```bash
# Install Certbot
apt-get install -y certbot python3-certbot-nginx

# Get free SSL certificate
certbot --nginx -d yourdomain.com

# Follow the prompts, choose "redirect HTTP to HTTPS"
```

Now visit: `https://yourdomain.com` 🔒

---

## Step 6: Keep It Running

### Run in Background

The current setup stops when you close the SSH session. Let's fix that:

```bash
# Stop the current server (Ctrl+C if running)

# Install tmux (terminal multiplexer)
apt-get install -y tmux

# Start a tmux session
tmux new -s voice-generator

# Run the server
docker compose run --rm voice-generator python web_server.py

# Detach from tmux: Press Ctrl+B, then D
```

Your server will keep running even after you close SSH!

**To reconnect later**:
```bash
ssh root@your.droplet.ip.address
tmux attach -t voice-generator
```

### Auto-Start on Reboot (Better)

Create a systemd service:

```bash
nano /etc/systemd/system/voice-generator.service
```

Paste this (adjust paths if needed):

```ini
[Unit]
Description=Voice Generator Web Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/root/speech_generator
ExecStart=/usr/bin/docker compose run --rm voice-generator python web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and enable:

```bash
# Reload systemd
systemctl daemon-reload

# Enable auto-start
systemctl enable voice-generator

# Start now
systemctl start voice-generator

# Check status
systemctl status voice-generator
```

---

## Step 7: Update Your App

When you make changes to your code:

```bash
# SSH into droplet
ssh root@your.droplet.ip.address
cd speech_generator

# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose run --rm voice-generator python web_server.py
```

---

## Alternative: Upload Files Without Git

If you don't want to use GitHub:

### On Your Mac:
```bash
# Compress your project
cd /path/to/speech_generator
tar -czf voice-generator.tar.gz .

# Upload to droplet
scp voice-generator.tar.gz root@your.droplet.ip.address:/root/
```

### On Your Droplet:
```bash
# Extract files
cd /root
mkdir speech_generator
tar -xzf voice-generator.tar.gz -C speech_generator
cd speech_generator

# Start the app
./start.sh --no-browser
```

---

## Monitoring & Maintenance

### Check Logs
```bash
# View Docker logs
docker compose logs -f

# Or if using systemd
journalctl -u voice-generator -f
```

### Restart Server
```bash
# Stop containers
docker compose down

# Start again
docker compose run --rm voice-generator python web_server.py
```

### Free Up Disk Space
```bash
# Remove old Docker images
docker system prune -a

# Check disk usage
df -h
```

### Monitor Resources
```bash
# Install htop
apt-get install -y htop

# View CPU/RAM usage
htop
```

---

## Security Best Practices

### 1. Set Up Firewall
```bash
# Enable UFW firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. Disable Root Login (After Setup)
```bash
# Create a new user
adduser yourname
usermod -aG sudo,docker yourname

# Test SSH with new user
ssh yourname@your.droplet.ip.address

# Then disable root login
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart sshd
```

### 3. Regular Updates
```bash
# Update system packages weekly
apt-get update && apt-get upgrade -y

# Rebuild Docker image for security patches
docker compose down
docker compose build
docker compose run --rm voice-generator python web_server.py
```

---

## Troubleshooting

### Port 5002 Not Accessible
```bash
# Check if server is running
docker ps

# Check if port is listening
netstat -tlnp | grep 5002

# Check firewall
ufw status
```

### Out of Memory
```bash
# Check memory usage
free -h

# Upgrade to 8GB droplet if needed (resize in DigitalOcean dashboard)
```

### Model Download Fails
```bash
# DNS issues - use the fallback script
python download_model_configs.py
```

### Docker Not Found
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin
```

---

## Cost Optimization

### Current Setup Cost: ~$24/month

**Ways to reduce costs:**

1. **Use $6/month droplet for testing** (1GB RAM)
   - Will be slower but works for low traffic
   - Upgrade later if needed

2. **Pause when not in use**
   - DigitalOcean doesn't charge for powered-off droplets (only storage)
   - Power on when needed

3. **Use Oracle Cloud Free Tier**
   - See separate guide (more complex setup)

---

## Next Steps

✅ Your Voice Generator is now live!

**Share your app**:
- Send the URL to others: `http://your.droplet.ip.address:5002` or `https://yourdomain.com`
- No authentication by default - anyone can use it

**Want to add authentication?** Let me know and I can create a guide for adding password protection.

**Need help?** Check the troubleshooting section or create an issue on GitHub.

---

## Quick Reference Commands

```bash
# SSH into droplet
ssh root@your.droplet.ip.address

# Navigate to app
cd speech_generator

# Build images
docker compose build

# Start server (foreground)
docker compose run --rm voice-generator python web_server.py

# Stop server
docker compose down

# Update app
git pull && docker compose build && docker compose run --rm voice-generator python web_server.py

# View logs
docker compose logs -f

# Check status (if using systemd)
systemctl status voice-generator
```

---

**Estimated Total Time**: 30 minutes
**Monthly Cost**: $24 (or free with credits)
**Performance**: 30-60 seconds per voice generation on CPU
