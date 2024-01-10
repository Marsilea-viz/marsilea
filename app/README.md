# How to run the app version of Marsilea

## Using Docker

### Step 1: Build the image

```bash
docker build -t marsilea-app .
```

### Step 2: Run the container

```bash
docker run -p 8501:8501 marsilea-app
```

Go to http://localhost:8501 to see the app.