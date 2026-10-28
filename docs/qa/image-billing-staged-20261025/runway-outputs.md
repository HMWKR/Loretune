---
title: API Output Formats
description: Understand Runway Dev output formats and responses. Learn how to handle generated videos, images and metadata from AI generation requests.
---

After a task succeeds, the `GET /v1/tasks/:id` endpoint will return a response
like this:

```json
{
  "id": "d2e3d1f4-1b3c-4b5c-8d46-1c1d7ee86892",
  "status": "SUCCEEDED",
  "createdAt": "2024-06-27T19:49:32.335Z",
  "output": [
    "https://dnznrvs05pmza.cloudfront.net/output.mp4?_jwt=..."
  ]
}
```

The `output` member will contain one or more URLs that link to the result of your
generation.

It's important to note that these URLs are ephemeral: they will expire within 24-48
hours of accessing the API. We expect you to download the data at this endpoint and
save it to your own storage. Since these URLs will expire, do not expose them
directly in your product.
