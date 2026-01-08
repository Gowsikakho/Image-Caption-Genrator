# Deployment Guide

## Local Development

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment file:
   ```bash
   cp .env.example .env
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t image-caption-generator .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 image-caption-generator
   ```

## Production Deployment

### Environment Variables

Set the following environment variables for production:

- `FLASK_DEBUG=false`
- `FLASK_HOST=0.0.0.0` (for Docker/cloud deployment)
- `SECRET_KEY=<strong-random-key>`
- `CORS_ORIGINS=<your-frontend-domains>`

### Security Considerations

- Use HTTPS in production
- Set up proper firewall rules
- Configure reverse proxy (nginx/Apache)
- Enable rate limiting
- Set up monitoring and logging
- Regular security updates

### Cloud Deployment Options

- **AWS**: Use Elastic Beanstalk or ECS
- **Google Cloud**: Use App Engine or Cloud Run
- **Azure**: Use App Service or Container Instances
- **Heroku**: Direct deployment with Procfile