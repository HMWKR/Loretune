# Draft — not sent

Subject: Private Kling output inaccessible to originating account (request 01a171d6-bf9e-7e72-a8c8-4eb2c5f83b1d)

We made one fal-ai/kling-video/v2.6/pro/image-to-video request with duration10, audio off, and X-Fal-Object-Lifecycle-Preference specifying expiration_duration_seconds3600 and initial_acl {default:forbid,rules:[]}.

Queue status is COMPLETED; Dashboard shows200, execution330.355seconds, cost$0.70. The output is reported as video/mp4,8,379,663bytes. Using the originating API key, POST rest.fal.ai/storage/auth/token?storage_type=fal-cdn-v3 with expiration_seconds600 succeeds. A subsequent GET of the returned v3b.fal.media file with Authorization: Bearer <token> returns403. Anonymous GET also returns403. GET rest.fal.ai/storage/files/acl for the same output, authenticated with the originating key, returns403. Dashboard playback reports media error4 with no buffered data; one normal Download click produced no download record.

Please verify the output's owner/account/team mapping, applicable key permissions, and whether the Kling2.6 runner preserved the caller CDN token/request association. Please confirm whether this output remains available and its exact expiration. We need owner-authenticated private access, without public ACL fallback, credential expansion, or a new paid generation. Which documented minimal correction is needed, and can access to this existing result be restored?

No API key, token, or signed result URL is included. We have not changed ACLs or retried generation. This is a draft; no support message has been sent.

Additional public evidence to ask about (not a confirmed cause): fal-ai/fal draft PR #1136 describes request-scoped CDN token loss in chained app queue results. Please confirm whether the Kling2.6 deployment chains requests and whether output upload preserved the originating caller token/request association. Does this particular output belong to the caller/team or deployment owner? Is account-token exchange the intended external-client access path, or is a response token contract required? No token values are requested in public replies.
