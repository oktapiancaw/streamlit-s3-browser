# Streamlit S3 Browser
<img title="preview" alt="Preview images" src="/public/preview.png">

S3http Client based on Streamlit, from this app you check directories and download files from s3.

### Features

Some simple features that already exist:
- List directories and files
- Download single file

#### Connection Management
And there is also a feature connected to mongo as a storage for s3 connections, and in mongo must use data with a structure like this
```json
{
  "_id": "7f1adae6-0664-4049-a225-eb408afbf488",
  "created_at": "2024-11-22T16:23:32.913Z",
  "created_by": "User",
  "name": "Local S3 Connection",
  "access": {
    "host": "0.0.0.0",
    "port": 8000,
    "endpoint_url": "http:/0.0.0.0:8000",
    "access_key": "<access_key>",
    "secret_key": "<secret_key>",
    "bucket": "buckt"
  },
  "description": "Simple description",
  "connection_type": "s3http",
  "tags": [
    "file-storage",
    "datalake"
  ],
  "version": "0.0.2"
}
```

Then just add env in the following way

```bash
copy .env.example .env
```

### Build your own

To run with the changes that you changed in the code can do the following steps

```bash
docker compose up --build
```



### Contributors

[//]: contributor-faces

<a href="https://github.com/oktapiancaw"><img src="https://avatars.githubusercontent.com/u/48079010?v=4" title="Oktapian Candra" width="80" height="80" style="border-radius: 50%"></a>

[//]: contributor-faces