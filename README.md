# VTOL Log Sender

Uploads the logs from a pixhawk to a dedicated server using a curl command. 

Note: Curl command is specific to the server this is originally intended for.

## Instructions 
1. Create a .env file in the root of the repository containing:

  ```
  INGEST_API_KEY={insert key}
  UPLOAD_URL={insert key}
  ```
2. Build and Run using Docker Compose 

```
docker compose up --build
```

