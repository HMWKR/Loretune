Subject: CDN token exchange403 after successful Kling completion (private self-reader)

Please investigate request01a17232-7047-7ae1-b491-7cfe70686742 on fal-ai/kling-video/v2.6/pro/image-to-video. Queue accepted and COMPLETED. The subsequent POST https://rest.fal.ai/storage/auth/token?storage_type=fal-cdn-v3 returned403 (expiration_seconds600); therefore the media CDN GET was never attempted. We stopped without retrying or changing permissions.

Earlier that day a controlled direct upload of a4423-byte synthetic PNG with private ACL/3600-second retention succeeded, as did token exchange and authenticated read with matching SHA256. This new generation requested default forbid and explicit allow for the verified personal-profile Username. No other recipient/public fallback was used.

Please confirm the reason for token issuance denial, whether the caller account/token service requires an action within existing permissions, and the new output ownership/ACL. Also confirm the request cost and exact output expiry. Do not change ACL to public or generate a replacement. We can provide timestamps/HTTP status privately; no API key/token/signed URL is included here. Draft only; not sent.
