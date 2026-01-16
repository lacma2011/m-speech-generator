# TODO & Reference Guide

This document tracks planned features, deployment notes, and technical details for future reference.

---

## Storage & Persistence Explained

### Docker Volume Setup

Your `docker-compose.yml` has **three types of storage**:

#### 1. Named Docker Volume (for base model)
```yaml
voice_models:/app/models
```
- **What**: XTTS v2 base model (~1.5GB)
- **Where**: Managed by Docker (survives container rebuilds)
- **Persists**: ✅ Forever (until you run `docker volume rm voice_models`)
- **Backup**: `docker run --rm -v voice_models:/data -v $(pwd):/backup ubuntu tar czf /backup/voice_models.tar.gz /data`

#### 2. Bind Mounts (for your data)
```yaml
./voice_samples:/app/voice_samples  # Training audio
./output:/app/output                # Generated audio
.:/app                               # Source code
```
- **What**: Your files directly on the server
- **Where**: In your project directory (`~/speech_generator/`)
- **Persists**: ✅ Forever (normal files on disk)
- **Backup**: Just copy the directories

### Storage Requirements

**DigitalOcean $24/month droplet = 80GB SSD**

**Estimated Usage:**
```
Operating System:        ~10GB
Docker images:           ~5GB
XTTS v2 base model:      ~1.5GB
Training audio samples:  ~5-10GB (hours of audio)
Fine-tuned models:       ~1.5-2GB each
Generated outputs:       ~2-5GB (accumulates over time)
────────────────────────────────────
TOTAL USED:              ~25-35GB
AVAILABLE:               45-55GB remaining ✓
```

**For Fine-Tuning:**
- Input audio: 30min-2hrs (~500MB-3GB)
- Dataset prep: 2x audio size (~1-6GB)
- Trained model: ~1.5-2GB
- **Total per voice**: ~5-10GB

**Conclusion**: 80GB is plenty for multiple fine-tuned models!

### Check Storage on Server

```bash
# Overall disk usage
df -h

# Project directory size
du -sh ~/speech_generator/

# Docker volume usage
docker system df -v

# Specific directories
du -sh ~/speech_generator/voice_samples/
du -sh ~/speech_generator/output/
```

### If You Run Out of Space

**Option 1: Clean up**
```bash
# Remove old generated audio
rm ~/speech_generator/output/*.wav

# Clean Docker cache
docker system prune -a

# Remove old training datasets
rm -rf ~/speech_generator/datasets/old_*
```

**Option 2: Upgrade droplet**
- $48/month = 160GB disk (2x storage)
- Can resize anytime in DigitalOcean dashboard

**Option 3: Add block storage**
- $10/month per 100GB
- Attach and mount to `/mnt/storage`
- Move training data there

---

## Deployment Checklist

### Pre-Deployment
- [ ] Push code to GitHub (or prepare for manual upload)
- [ ] Have DigitalOcean account ready
- [ ] Get promo code for $200 free credits (Google: "DigitalOcean promo")

### Initial Setup (Done Once)
- [ ] Create 4GB RAM droplet with Docker ($24/month)
- [ ] Configure SSH key authentication
- [ ] Set up firewall (UFW)
- [ ] Clone repository to server
- [ ] Run `docker compose build`
- [ ] Test with `docker compose run --rm voice-generator python web_server.py`
- [ ] Verify access at `http://your-ip:5002`

### Production Setup (Optional but Recommended)
- [ ] Configure custom domain (A record to droplet IP)
- [ ] Install Nginx reverse proxy
- [ ] Set up HTTPS with Let's Encrypt (free SSL)
- [ ] Configure systemd service for auto-start
- [ ] Set up tmux or systemd for background running
- [ ] Configure firewall rules (SSH, HTTP, HTTPS only)
- [ ] Disable root SSH login (create regular user)

### Post-Deployment
- [ ] Test voice cloning from public URL
- [ ] Set up monitoring (optional: htop, Netdata)
- [ ] Schedule weekly backups (optional)
- [ ] Document your custom domain/URL

---

## Maintenance Tasks

### Weekly
- [ ] Check disk usage: `df -h`
- [ ] Review logs: `docker compose logs --tail 100`
- [ ] Clean old generated files: `rm ~/speech_generator/output/*.wav` (if needed)

### Monthly
- [ ] Update system packages: `apt-get update && apt-get upgrade -y`
- [ ] Review security updates
- [ ] Backup important data (trained models, sample audio)
- [ ] Check Docker disk usage: `docker system df`

### As Needed
- [ ] Rebuild Docker image after code changes: `docker compose build`
- [ ] Restart service after updates: `systemctl restart voice-generator`
- [ ] Renew SSL certificate (auto-renews with certbot)

---

## Current Status

### ✅ Completed Features
- [x] Basic voice cloning with XTTS v2
- [x] Web interface with file upload
- [x] CLI voice cloning script
- [x] Docker containerization (CPU + GPU)
- [x] macOS launcher scripts (start.sh, start.command, stop.sh)
- [x] Deployment guide for DigitalOcean
- [x] DNS configuration for reliable model downloads
- [x] Dependency version pins (PyTorch, transformers)
- [x] Fine-tuning utilities (train_voice.py)

### 🚧 Future Enhancements

#### High Priority
- [ ] Add authentication/password protection for public deployment
- [ ] Rate limiting to prevent abuse
- [ ] Queue system for multiple simultaneous requests
- [ ] Progress indicator during voice generation
- [ ] Better error messages in web UI

#### Medium Priority
- [ ] Save/manage multiple voice profiles
- [ ] Audio preview before download
- [ ] Support for longer text inputs (chunking)
- [ ] Batch processing multiple texts
- [ ] API key system for external access
- [ ] Usage analytics/logging

#### Low Priority
- [ ] Dark mode toggle
- [ ] Multiple language UI
- [ ] Voice sample library/presets
- [ ] Advanced tuning parameters in UI
- [ ] Audio quality settings (sample rate, format)
- [ ] Integration with cloud storage (S3, Dropbox)

#### Nice to Have
- [ ] Mobile-responsive UI improvements
- [ ] Real-time voice preview
- [ ] Voice mixing/blending features
- [ ] Text-to-speech history
- [ ] Export to different audio formats
- [ ] Webhook notifications when generation completes

---

## Known Issues

### Resolved
- ✅ PyTorch 2.6+ compatibility (pinned to <2.6.0)
- ✅ transformers BeamSearchScorer import error (pinned to 4.33-4.40)
- ✅ DNS resolution for coqui.gateway.scarf.sh (added DNS servers)
- ✅ GPU Dockerfile missing dependency pins (fixed)

### Active
- None currently

### To Investigate
- [ ] Memory usage optimization for multiple concurrent users
- [ ] Apple Silicon (MPS) GPU support in Docker
- [ ] Faster model loading time (currently 10-30 seconds)

---

## Security Considerations

### For Public Deployment

**Must Do:**
- [ ] Add authentication (basic auth or login system)
- [ ] Set up rate limiting (prevent API abuse)
- [ ] Configure HTTPS (Let's Encrypt)
- [ ] Enable firewall (UFW)
- [ ] Disable root SSH login
- [ ] Keep Docker images updated

**Should Do:**
- [ ] Add input validation/sanitization
- [ ] Limit file upload sizes (currently 50MB)
- [ ] Log access/usage for monitoring
- [ ] Set up fail2ban for SSH protection
- [ ] Regular security audits

**Nice to Have:**
- [ ] API key system for access control
- [ ] CAPTCHA for abuse prevention
- [ ] IP whitelisting option
- [ ] Automated backups to external storage

---

## Cost Breakdown

### Current Setup (DigitalOcean)

**Monthly Costs:**
- Droplet (4GB RAM, 2 CPU, 80GB SSD): $24/month
- Domain (optional): ~$12/year
- SSL Certificate: $0 (Let's Encrypt free)

**One-Time:**
- Setup time: $0 (DIY)

**Total**: ~$25/month

### If You Need More

**Scale Up Options:**
| Upgrade | Cost | When Needed |
|---------|------|-------------|
| 8GB RAM droplet | $48/month | Heavy traffic, multiple concurrent users |
| Block Storage (+100GB) | $10/month | Large training datasets |
| Load Balancer | $12/month | High availability, 1000+ requests/day |
| GPU instance (g4dn.xlarge) | ~$380/month | Sub-5sec generation, high volume |

---

## Quick Commands Reference

### Local Development (macOS)
```bash
./start.sh                  # Start with browser auto-open
./start.sh --no-browser     # Start without browser
./start.sh --rebuild        # Force rebuild
./stop.sh                   # Stop server
```

### Server Deployment
```bash
# Build and run
docker compose build
docker compose run --rm voice-generator python web_server.py

# Stop
docker compose down

# View logs
docker compose logs -f

# Update
git pull
docker compose build
docker compose down
docker compose run --rm voice-generator python web_server.py
```

### System Management
```bash
# Check disk space
df -h
du -sh ~/speech_generator/

# Check memory
free -h

# Check running containers
docker ps

# Clean Docker cache
docker system prune -a

# Restart systemd service
systemctl restart voice-generator
systemctl status voice-generator
```

---

## Notes for Future Development

### Adding Authentication

When ready to add password protection:

1. **Quick option**: Nginx basic auth
```bash
apt-get install apache2-utils
htpasswd -c /etc/nginx/.htpasswd username
# Add auth_basic to nginx config
```

2. **Better option**: Flask-Login
- Add Flask-Login to requirements.txt
- Create login page
- Add session management
- Protect routes with @login_required

### Scaling Considerations

**When traffic grows:**
- Move to 8GB RAM droplet ($48/month)
- Add Redis for queue management
- Use Gunicorn with multiple workers
- Set up Nginx caching
- Consider CDN for static assets

**For high volume:**
- Multiple droplets + load balancer
- Separate model server from web server
- Queue system (Celery + Redis)
- Auto-scaling with Kubernetes

---

## Contact & Support

**Documentation:**
- README.md - Quick start guide
- DEPLOYMENT.md - Server deployment guide
- CLAUDE.md - Developer/AI assistant context
- This file (TODO.md) - Reference & planning

**Useful Links:**
- XTTS v2 Docs: https://docs.coqui.ai/en/latest/models/xtts.html
- Docker Compose: https://docs.docker.com/compose/
- DigitalOcean Docs: https://docs.digitalocean.com/

---

**Last Updated**: 2026-01-12
**Status**: Production Ready
**Deployment Status**: Local development ✅ | Server deployment 📋 (guide ready)
