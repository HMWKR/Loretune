-- 신규 IP 음악영상 제작 플랫폼: 설계용 스키마 v0.1, 2026-10-23.
-- NOT production-applied, NOT benchmarked. Run PostgreSQL + pgvector migrations and RLS tests before use.
-- Aethon databases, users, code and validation results are not assumed.
-- Migration role owns these objects. Runtime API/worker roles MUST NOT own tables, be superuser or BYPASSRLS.
-- Runtime roles receive explicit least-privilege GRANTs in deployment migrations; this file creates no unsafe broad GRANT.
-- Every request sets app.tenant_id using SET LOCAL only after authenticated membership validation.
-- This RLS layer isolates tenants; IP/project/object permissions are additionally enforced by domain services.
-- Arbitrary JSON payloads require versioned JSON Schema + cross-object/IP checks in services.
-- Non-core workflow records (plans/storyboards/shares/integrations) are included as scoped storage contracts.
-- All monetary numbers are exact decimal, and account currencies are never implicitly mixed.

BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS ipmv;
SET search_path TO ipmv, public;

CREATE FUNCTION ipmv.current_tenant_id() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.tenant_id', true), '')::uuid
$$;

CREATE FUNCTION ipmv.reject_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'immutable version/event; append a new revision or correction' USING ERRCODE = '55000';
END;
$$;

CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL CHECK (length(name) BETWEEN 1 AND 100),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleting','deleted')),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE principals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_subject text NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled','deleted')),
  created_at timestamptz NOT NULL DEFAULT now()
);
-- principals is a private identity table: no general client SELECT. Resolve only authenticated subject.

CREATE TABLE memberships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  principal_id uuid NOT NULL REFERENCES principals(id),
  role text NOT NULL CHECK (role IN ('owner','admin','producer','creator','reviewer','viewer')),
  active boolean NOT NULL DEFAULT true,
  expires_at timestamptz,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  UNIQUE (tenant_id, principal_id)
);

CREATE TABLE ips (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  stable_key text NOT NULL,
  default_locale text NOT NULL DEFAULT 'ko-KR',
  description text NOT NULL DEFAULT '',
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  UNIQUE (tenant_id, stable_key)
);

CREATE TABLE eras (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  name text NOT NULL,
  starts_at timestamptz,
  ends_at timestamptz,
  description text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  CHECK (ends_at IS NULL OR starts_at IS NULL OR starts_at <= ends_at)
);

CREATE TABLE narrative_branches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  name text NOT NULL,
  parent_id uuid,
  fork_snapshot_id uuid,
  description text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, parent_id) REFERENCES narrative_branches(tenant_id, id),
  CHECK (parent_id IS NULL OR parent_id <> id),
  CHECK ((parent_id IS NULL AND fork_snapshot_id IS NULL) OR (parent_id IS NOT NULL AND fork_snapshot_id IS NOT NULL)),
  UNIQUE (tenant_id, ip_id, name)
);

CREATE TABLE entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  entity_type text NOT NULL CHECK (entity_type IN ('human_person','fictional_character','group','costume','location','event','motif','prop')),
  stable_key text NOT NULL,
  current_revision bigint NOT NULL DEFAULT 1 CHECK (current_revision > 0),
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  UNIQUE (tenant_id, ip_id, stable_key)
);

CREATE TABLE entity_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  entity_id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0),
  display_name text NOT NULL,
  attributes jsonb NOT NULL,
  schema_version text NOT NULL,
  payload_hash text NOT NULL CHECK (payload_hash ~ '^[a-f0-9]{64}$'),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, entity_id) REFERENCES entities(tenant_id, id),
  UNIQUE (tenant_id, entity_id, revision)
);

CREATE TABLE predicate_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  key text NOT NULL,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  subject_types text[] NOT NULL,
  object_types text[],
  value_schema jsonb,
  cardinality text NOT NULL CHECK (cardinality IN ('one','many')),
  scope text NOT NULL CHECK (scope IN ('fiction','real_world','production')),
  inverse_key text,
  schema_hash text NOT NULL,
  retired_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  UNIQUE (tenant_id, ip_id, key, revision),
  CHECK (cardinality(subject_types) > 0),
  CHECK ((object_types IS NOT NULL)::int + (value_schema IS NOT NULL)::int = 1)
);

CREATE TABLE assertions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  subject_id uuid NOT NULL,
  predicate_id uuid NOT NULL,
  current_revision bigint NOT NULL DEFAULT 1 CHECK (current_revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, subject_id) REFERENCES entities(tenant_id, id),
  FOREIGN KEY (tenant_id, predicate_id) REFERENCES predicate_definitions(tenant_id, id)
);

CREATE TABLE assertion_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  assertion_id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0),
  object_entity_id uuid,
  value jsonb,
  branch_id uuid NOT NULL,
  era_id uuid,
  valid_story_from timestamptz,
  valid_story_to timestamptz,
  story_ordinal_from bigint,
  story_ordinal_to bigint,
  confidence numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  scope text NOT NULL CHECK (scope IN ('fiction','real_world','production')),
  supersedes_id uuid,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  payload_hash text NOT NULL CHECK (payload_hash ~ '^[a-f0-9]{64}$'),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, assertion_id) REFERENCES assertions(tenant_id, id),
  FOREIGN KEY (tenant_id, object_entity_id) REFERENCES entities(tenant_id, id),
  FOREIGN KEY (tenant_id, branch_id) REFERENCES narrative_branches(tenant_id, id),
  FOREIGN KEY (tenant_id, era_id) REFERENCES eras(tenant_id, id),
  FOREIGN KEY (tenant_id, supersedes_id) REFERENCES assertion_revisions(tenant_id, id),
  UNIQUE (tenant_id, assertion_id, revision),
  CHECK (num_nonnulls(object_entity_id, value) = 1),
  CHECK (valid_story_to IS NULL OR valid_story_from IS NULL OR valid_story_from <= valid_story_to),
  CHECK (story_ordinal_to IS NULL OR story_ordinal_from IS NULL OR story_ordinal_from <= story_ordinal_to)
);

CREATE TABLE assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  kind text NOT NULL CHECK (kind IN ('image','video','audio','document','lyrics','model3d','font','archive')),
  rights_status text NOT NULL DEFAULT 'unknown' CHECK (rights_status IN ('unknown','declared','verified','restricted','revoked')),
  rights_manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
  rights_expires_at timestamptz,
  deletion_state text NOT NULL DEFAULT 'live' CHECK (deletion_state IN ('live','tombstoned','purging','deleted')),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id)
);

CREATE TABLE asset_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  asset_id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0),
  object_key text NOT NULL UNIQUE,
  sha256 text NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
  byte_size bigint NOT NULL CHECK (byte_size >= 0),
  media_type text NOT NULL,
  media_info jsonb NOT NULL DEFAULT '{}'::jsonb,
  role text NOT NULL CHECK (role IN ('original','proxy','thumbnail','generated','render','subtitle','bundle')),
  source_revision_id uuid,
  scan_report jsonb NOT NULL,
  created_by uuid REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, asset_id) REFERENCES assets(tenant_id, id),
  FOREIGN KEY (tenant_id, source_revision_id) REFERENCES asset_revisions(tenant_id, id),
  UNIQUE (tenant_id, asset_id, revision)
);

CREATE TABLE evidence_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  assertion_revision_id uuid NOT NULL,
  asset_revision_id uuid NOT NULL,
  locator text NOT NULL,
  quote_hash text CHECK (quote_hash ~ '^[a-f0-9]{64}$'),
  extraction_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, assertion_revision_id) REFERENCES assertion_revisions(tenant_id, id),
  FOREIGN KEY (tenant_id, asset_revision_id) REFERENCES asset_revisions(tenant_id, id),
  UNIQUE (tenant_id, assertion_revision_id, asset_revision_id, locator)
);

CREATE TABLE songs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  title text NOT NULL,
  audio_revision_id uuid NOT NULL,
  lyrics_revision_id uuid,
  language text,
  analysis_revision bigint NOT NULL DEFAULT 0 CHECK (analysis_revision >= 0),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, audio_revision_id) REFERENCES asset_revisions(tenant_id, id),
  FOREIGN KEY (tenant_id, lyrics_revision_id) REFERENCES asset_revisions(tenant_id, id)
);

CREATE TABLE song_segments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  song_id uuid NOT NULL,
  analysis_revision bigint NOT NULL CHECK (analysis_revision > 0),
  segment_index integer NOT NULL CHECK (segment_index >= 0),
  start_sample bigint NOT NULL CHECK (start_sample >= 0),
  end_sample bigint NOT NULL,
  sample_rate integer NOT NULL CHECK (sample_rate BETWEEN 8000 AND 384000),
  label text NOT NULL,
  lyrics text,
  confidence numeric(5,4) CHECK (confidence BETWEEN 0 AND 1),
  origin text NOT NULL CHECK (origin IN ('automatic','manual')),
  created_by uuid REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, song_id) REFERENCES songs(tenant_id, id),
  CHECK (end_sample > start_sample),
  UNIQUE (tenant_id, song_id, analysis_revision, segment_index)
);

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  era_id uuid,
  branch_id uuid NOT NULL,
  song_id uuid NOT NULL,
  name text NOT NULL,
  output_kind text NOT NULL CHECK (output_kind IN ('teaser','music_video','lyric_video','vertical_clip','visualizer')),
  state text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','planning','producing','review','approved','released','archived')),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  fps_numerator integer NOT NULL CHECK (fps_numerator > 0),
  fps_denominator integer NOT NULL CHECK (fps_denominator > 0),
  target_duration_frames bigint NOT NULL CHECK (target_duration_frames > 0),
  aspect_ratio text NOT NULL,
  brief text NOT NULL DEFAULT '',
  created_by uuid NOT NULL REFERENCES principals(id),
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, era_id) REFERENCES eras(tenant_id, id),
  FOREIGN KEY (tenant_id, branch_id) REFERENCES narrative_branches(tenant_id, id),
  FOREIGN KEY (tenant_id, song_id) REFERENCES songs(tenant_id, id)
);

CREATE TABLE access_grants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  principal_id uuid NOT NULL REFERENCES principals(id),
  ip_id uuid,
  project_id uuid,
  asset_id uuid,
  permission text NOT NULL,
  expires_at timestamptz,
  revoked_at timestamptz,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, asset_id) REFERENCES assets(tenant_id, id),
  CHECK (num_nonnulls(ip_id, project_id, asset_id) = 1)
);

CREATE TABLE preference_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  scope text NOT NULL CHECK (scope IN ('ip','era','project','personal')),
  era_id uuid,
  project_id uuid,
  principal_id uuid REFERENCES principals(id),
  key text NOT NULL,
  current_revision bigint NOT NULL DEFAULT 1 CHECK (current_revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, era_id) REFERENCES eras(tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  CHECK ((scope = 'ip' AND num_nonnulls(era_id, project_id, principal_id) = 0) OR (scope = 'era' AND era_id IS NOT NULL AND num_nonnulls(project_id, principal_id) = 0) OR (scope = 'project' AND project_id IS NOT NULL AND num_nonnulls(era_id, principal_id) = 0) OR (scope = 'personal' AND principal_id IS NOT NULL AND num_nonnulls(era_id, project_id) = 0))
);

CREATE TABLE preference_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  rule_id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0),
  rule jsonb NOT NULL,
  confidence numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  evidence_count integer NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  evidence_feedback_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  counter_evidence_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  expires_at timestamptz,
  supersedes_id uuid,
  payload_hash text NOT NULL CHECK (payload_hash ~ '^[a-f0-9]{64}$'),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, rule_id) REFERENCES preference_rules(tenant_id, id),
  FOREIGN KEY (tenant_id, supersedes_id) REFERENCES preference_revisions(tenant_id, id),
  UNIQUE (tenant_id, rule_id, revision)
);

CREATE TABLE context_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid NOT NULL,
  branch_id uuid NOT NULL,
  knowledge_as_of timestamptz NOT NULL,
  manifest jsonb NOT NULL,
  manifest_hash text NOT NULL CHECK (manifest_hash ~ '^[a-f0-9]{64}$'),
  policy_version text NOT NULL,
  retriever_version text NOT NULL,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, branch_id) REFERENCES narrative_branches(tenant_id, id),
  UNIQUE (tenant_id, project_id, manifest_hash)
);

ALTER TABLE narrative_branches ADD CONSTRAINT branch_fork_snapshot_fk FOREIGN KEY (tenant_id, fork_snapshot_id) REFERENCES context_snapshots(tenant_id, id);

CREATE TABLE shots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid NOT NULL,
  order_key text NOT NULL,
  current_revision bigint NOT NULL DEFAULT 1 CHECK (current_revision > 0),
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  UNIQUE (tenant_id, project_id, order_key)
);

CREATE TABLE shot_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  shot_id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0),
  in_frame bigint NOT NULL CHECK (in_frame >= 0),
  out_frame bigint NOT NULL,
  snapshot_id uuid NOT NULL,
  spec jsonb NOT NULL,
  spec_hash text NOT NULL CHECK (spec_hash ~ '^[a-f0-9]{64}$'),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, shot_id) REFERENCES shots(tenant_id, id),
  FOREIGN KEY (tenant_id, snapshot_id) REFERENCES context_snapshots(tenant_id, id),
  CHECK (out_frame > in_frame),
  UNIQUE (tenant_id, shot_id, revision)
);

CREATE TABLE shot_dependencies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  shot_revision_id uuid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind IN ('assertion_revision','entity_revision','asset_revision','preference_revision','song_segment','shot_revision','template_revision')),
  source_id uuid NOT NULL,
  source_hash text NOT NULL CHECK (source_hash ~ '^[a-f0-9]{64}$'),
  dependency_role text NOT NULL,
  confidence numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, shot_revision_id) REFERENCES shot_revisions(tenant_id, id),
  UNIQUE (tenant_id, shot_revision_id, source_kind, source_id, dependency_role)
);

-- provider_model_releases is global public metadata, not tenant private data; no secrets here.
CREATE TABLE provider_model_releases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  model text NOT NULL,
  revision text NOT NULL,
  capabilities jsonb NOT NULL,
  price_manifest jsonb NOT NULL,
  price_version text NOT NULL,
  license_status text NOT NULL CHECK (license_status IN ('verified','restricted','unknown')),
  retention_status text NOT NULL CHECK (retention_status IN ('verified','unknown')),
  docs_url text NOT NULL,
  verified_at timestamptz NOT NULL,
  test_evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  disabled_at timestamptz,
  UNIQUE (provider, model, revision, price_version)
);

CREATE TABLE generation_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid,
  ip_id uuid,
  scope_kind text NOT NULL CHECK (scope_kind IN ('workspace','ip','project')),
  parent_job_id uuid,
  kind text NOT NULL,
  state text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','validated','reserved','queued','submitting','submission_unknown','running','validating_output','retry_wait','cancel_requested','cancelled','succeeded','failed','blocked','reconciliation_required')),
  snapshot_id uuid,
  model_release_id uuid REFERENCES provider_model_releases(id),
  idempotency_key text NOT NULL,
  request_hash text NOT NULL CHECK (request_hash ~ '^[a-f0-9]{64}$'),
  payload jsonb NOT NULL,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  lease_owner text,
  lease_until timestamptz,
  heartbeat_at timestamptz,
  available_at timestamptz NOT NULL DEFAULT now(),
  priority integer NOT NULL DEFAULT 0,
  max_attempts_per_shot integer NOT NULL DEFAULT 3 CHECK (max_attempts_per_shot BETWEEN 1 AND 3),
  cost_status text NOT NULL DEFAULT 'pending' CHECK (cost_status IN ('pending','confirmed','disputed')),
  cancel_requested_at timestamptz,
  error_code text,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, parent_job_id) REFERENCES generation_jobs(tenant_id, id),
  FOREIGN KEY (tenant_id, snapshot_id) REFERENCES context_snapshots(tenant_id, id),
  CHECK ((scope_kind = 'workspace' AND num_nonnulls(project_id, ip_id) = 0) OR (scope_kind = 'ip' AND ip_id IS NOT NULL AND project_id IS NULL) OR (scope_kind = 'project' AND project_id IS NOT NULL AND ip_id IS NULL)),
  UNIQUE (tenant_id, idempotency_key),
  CHECK (parent_job_id IS NULL OR parent_job_id <> id)
);

CREATE TABLE provider_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  job_id uuid NOT NULL,
  shot_revision_id uuid,
  attempt_no integer NOT NULL CHECK (attempt_no > 0),
  provider text NOT NULL,
  model_release_id uuid NOT NULL REFERENCES provider_model_releases(id),
  external_id text,
  external_idempotency_key text,
  request_hash text NOT NULL CHECK (request_hash ~ '^[a-f0-9]{64}$'),
  submission_state text NOT NULL DEFAULT 'not_submitted' CHECK (submission_state IN ('not_submitted','submitting','unknown','accepted','rejected')),
  provider_state text,
  submitted_at timestamptz,
  last_polled_at timestamptz,
  cost_status text NOT NULL DEFAULT 'pending' CHECK (cost_status IN ('pending','confirmed','disputed')),
  billed_units numeric(18,6),
  billed_unit_type text,
  confirmed_amount numeric(18,6) CHECK (confirmed_amount >= 0),
  currency char(3),
  usage_evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, job_id) REFERENCES generation_jobs(tenant_id, id),
  FOREIGN KEY (tenant_id, shot_revision_id) REFERENCES shot_revisions(tenant_id, id),
  UNIQUE (tenant_id, job_id, attempt_no),
  CHECK (confirmed_amount IS NULL OR currency IS NOT NULL)
);

CREATE UNIQUE INDEX provider_external_task_unique ON provider_attempts(provider, external_id) WHERE external_id IS NOT NULL;

CREATE TABLE job_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  job_id uuid NOT NULL,
  sequence bigint NOT NULL CHECK (sequence > 0),
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, job_id) REFERENCES generation_jobs(tenant_id, id),
  UNIQUE (tenant_id, job_id, sequence)
);

CREATE TABLE takes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  shot_revision_id uuid NOT NULL,
  asset_revision_id uuid NOT NULL,
  job_id uuid NOT NULL,
  provider_attempt_id uuid,
  ordinal integer NOT NULL CHECK (ordinal > 0),
  generation_manifest jsonb NOT NULL,
  technical_validation jsonb NOT NULL,
  created_by uuid REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, shot_revision_id) REFERENCES shot_revisions(tenant_id, id),
  FOREIGN KEY (tenant_id, asset_revision_id) REFERENCES asset_revisions(tenant_id, id),
  FOREIGN KEY (tenant_id, job_id) REFERENCES generation_jobs(tenant_id, id),
  FOREIGN KEY (tenant_id, provider_attempt_id) REFERENCES provider_attempts(tenant_id, id),
  UNIQUE (tenant_id, shot_revision_id, ordinal)
);

CREATE TABLE project_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid NOT NULL,
  revision bigint NOT NULL CHECK (revision > 0),
  snapshot_id uuid NOT NULL,
  audio_revision_id uuid NOT NULL,
  audio_start_sample bigint NOT NULL DEFAULT 0 CHECK (audio_start_sample >= 0),
  edit_decisions jsonb NOT NULL,
  text_layers jsonb NOT NULL DEFAULT '[]'::jsonb,
  aspect_variants jsonb NOT NULL DEFAULT '[]'::jsonb,
  manifest_hash text NOT NULL CHECK (manifest_hash ~ '^[a-f0-9]{64}$'),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, snapshot_id) REFERENCES context_snapshots(tenant_id, id),
  FOREIGN KEY (tenant_id, audio_revision_id) REFERENCES asset_revisions(tenant_id, id),
  UNIQUE (tenant_id, project_id, revision)
);

CREATE TABLE feedback_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid NOT NULL,
  take_id uuid,
  project_version_id uuid,
  decision text NOT NULL CHECK (decision IN ('accept','reject','needs_changes','compare')),
  dimensions jsonb NOT NULL,
  reason text NOT NULL,
  suggested_scope text NOT NULL CHECK (suggested_scope IN ('shot','project','era','ip','personal')),
  actor_id uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, take_id) REFERENCES takes(tenant_id, id),
  FOREIGN KEY (tenant_id, project_version_id) REFERENCES project_versions(tenant_id, id),
  CHECK (num_nonnulls(take_id, project_version_id) >= 1)
);

CREATE TABLE reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_version_id uuid NOT NULL,
  actor_id uuid NOT NULL REFERENCES principals(id),
  at_frame bigint NOT NULL CHECK (at_frame >= 0),
  body text NOT NULL,
  parent_review_id uuid,
  state text NOT NULL DEFAULT 'open' CHECK (state IN ('open','resolved','reopened')),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  resolution text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_version_id) REFERENCES project_versions(tenant_id, id),
  FOREIGN KEY (tenant_id, parent_review_id) REFERENCES reviews(tenant_id, id)
);

CREATE TABLE exports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_version_id uuid NOT NULL,
  profile text NOT NULL,
  artifact_revision_id uuid,
  job_id uuid NOT NULL,
  state text NOT NULL DEFAULT 'queued' CHECK (state IN ('queued','rendering','validating','ready','failed')),
  validation_report jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_version_id) REFERENCES project_versions(tenant_id, id),
  FOREIGN KEY (tenant_id, artifact_revision_id) REFERENCES asset_revisions(tenant_id, id),
  FOREIGN KEY (tenant_id, job_id) REFERENCES generation_jobs(tenant_id, id)
);

CREATE TABLE approval_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  target_kind text NOT NULL CHECK (target_kind IN ('entity_revision','assertion_revision','preference_revision','plan','storyboard','take','project_version','export','memory_proposal')),
  target_id uuid NOT NULL,
  scope text NOT NULL CHECK (scope IN ('canon','preference','production','release','proposal')),
  decision text NOT NULL CHECK (decision IN ('approve','reject','request_changes','revoke')),
  expected_revision bigint NOT NULL CHECK (expected_revision > 0),
  actor_id uuid NOT NULL REFERENCES principals(id),
  reason text NOT NULL DEFAULT '',
  supersedes_decision_id uuid,
  idempotency_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, supersedes_decision_id) REFERENCES approval_decisions(tenant_id, id),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE budget_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('customer_credit','provider_cost','customer_invoice')),
  currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
  posted_balance numeric(18,6) NOT NULL DEFAULT 0,
  reserved_balance numeric(18,6) NOT NULL DEFAULT 0 CHECK (reserved_balance >= 0),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  UNIQUE (tenant_id, name, currency)
);

CREATE TABLE budget_reservations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  account_id uuid NOT NULL,
  job_id uuid NOT NULL,
  amount numeric(18,6) NOT NULL CHECK (amount >= 0),
  state text NOT NULL DEFAULT 'active' CHECK (state IN ('active','pending_liability','settled','released','disputed')),
  expires_at timestamptz,
  price_version text NOT NULL,
  estimate_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, account_id) REFERENCES budget_accounts(tenant_id, id),
  FOREIGN KEY (tenant_id, job_id) REFERENCES generation_jobs(tenant_id, id),
  UNIQUE (tenant_id, account_id, job_id)
);

CREATE TABLE ledger_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  account_id uuid NOT NULL,
  reservation_id uuid,
  provider_attempt_id uuid,
  event_key text NOT NULL,
  entry_type text NOT NULL CHECK (entry_type IN ('fund','reserve','settle','release','refund','adjust','dispute')),
  posted_delta numeric(18,6) NOT NULL,
  reserved_delta numeric(18,6) NOT NULL,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  recorded_by uuid REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, account_id) REFERENCES budget_accounts(tenant_id, id),
  FOREIGN KEY (tenant_id, reservation_id) REFERENCES budget_reservations(tenant_id, id),
  FOREIGN KEY (tenant_id, provider_attempt_id) REFERENCES provider_attempts(tenant_id, id),
  UNIQUE (tenant_id, event_key),
  CHECK (posted_delta <> 0 OR reserved_delta <> 0)
);

CREATE TABLE webhook_inbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  provider text NOT NULL,
  dedupe_key text NOT NULL,
  provider_attempt_id uuid,
  raw_body_object_key text,
  payload_hash text NOT NULL,
  signature_status text NOT NULL CHECK (signature_status IN ('verified','invalid')),
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  processing_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, provider_attempt_id) REFERENCES provider_attempts(tenant_id, id),
  UNIQUE (tenant_id, provider, dedupe_key)
);

CREATE TABLE outbox_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  aggregate_kind text NOT NULL,
  aggregate_id uuid NOT NULL,
  event_key text NOT NULL,
  payload jsonb NOT NULL,
  available_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  UNIQUE (tenant_id, event_key)
);

CREATE TABLE retrieval_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  asset_revision_id uuid NOT NULL,
  chunk_index integer NOT NULL CHECK (chunk_index >= 0),
  text_content text NOT NULL,
  locator text NOT NULL,
  search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', text_content)) STORED,
  embedding_config text NOT NULL,
  embedding_dimensions integer NOT NULL CHECK (embedding_dimensions > 0),
  embedding vector,
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, asset_revision_id) REFERENCES asset_revisions(tenant_id, id),
  UNIQUE (tenant_id, asset_revision_id, chunk_index, embedding_config),
  CHECK (embedding IS NULL OR vector_dims(embedding) = embedding_dimensions)
);

CREATE TABLE audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  actor_id uuid REFERENCES principals(id),
  action text NOT NULL,
  target_kind text NOT NULL,
  target_id uuid,
  before_hash text,
  after_hash text,
  request_id text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id)
);

CREATE TABLE deletion_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  scope text NOT NULL CHECK (scope IN ('asset','project','ip','workspace','principal_data')),
  target_id uuid NOT NULL,
  state text NOT NULL DEFAULT 'requested' CHECK (state IN ('requested','tombstoned','purging','waiting_external','retention_exception','completed','failed')),
  include_derived boolean NOT NULL,
  reason text NOT NULL,
  propagation jsonb NOT NULL DEFAULT '{}'::jsonb,
  requested_by uuid NOT NULL REFERENCES principals(id),
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id)
);

CREATE TABLE planning_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid NOT NULL,
  snapshot_id uuid NOT NULL,
  kind text NOT NULL CHECK (kind IN ('plan','storyboard','rights_check','impact_preview','estimate')),
  revision bigint NOT NULL CHECK (revision > 0),
  spec jsonb NOT NULL,
  payload_hash text NOT NULL CHECK (payload_hash ~ '^[a-f0-9]{64}$'),
  expires_at timestamptz,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, snapshot_id) REFERENCES context_snapshots(tenant_id, id)
);

CREATE TABLE memory_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  project_version_id uuid NOT NULL,
  proposal_kind text NOT NULL CHECK (proposal_kind IN ('preference','canon_candidate','asset_promotion')),
  proposal jsonb NOT NULL,
  evidence_feedback_ids uuid[] NOT NULL,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, project_version_id) REFERENCES project_versions(tenant_id, id)
);

CREATE TABLE share_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_version_id uuid NOT NULL,
  token_hash text NOT NULL CHECK (token_hash ~ '^[a-f0-9]{64}$'),
  password_hash text,
  expires_at timestamptz NOT NULL,
  allow_comments boolean NOT NULL DEFAULT false,
  allow_downloads boolean NOT NULL DEFAULT false,
  revoked_at timestamptz,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_version_id) REFERENCES project_versions(tenant_id, id),
  UNIQUE (token_hash)
);

CREATE TABLE releases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid NOT NULL,
  export_id uuid NOT NULL,
  approval_id uuid NOT NULL,
  release_label text NOT NULL,
  destination text NOT NULL CHECK (destination IN ('download_package','connected_channel')),
  destination_id uuid,
  external_publication_id text,
  released_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  FOREIGN KEY (tenant_id, export_id) REFERENCES exports(tenant_id, id),
  FOREIGN KEY (tenant_id, approval_id) REFERENCES approval_decisions(tenant_id, id)
);

CREATE TABLE upload_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  ip_id uuid NOT NULL,
  asset_id uuid,
  declared_filename text NOT NULL,
  declared_media_type text NOT NULL,
  expected_bytes bigint NOT NULL CHECK (expected_bytes > 0),
  expected_sha256 text NOT NULL CHECK (expected_sha256 ~ '^[a-f0-9]{64}$'),
  quarantine_key text NOT NULL UNIQUE,
  state text NOT NULL DEFAULT 'open' CHECK (state IN ('open','uploaded','scanning','accepted','rejected','expired')),
  expires_at timestamptz NOT NULL,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, asset_id) REFERENCES assets(tenant_id, id)
);

CREATE TABLE integrations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  provider_key text NOT NULL,
  scopes text[] NOT NULL,
  secret_reference text NOT NULL,
  state text NOT NULL,
  expires_at timestamptz,
  revoked_at timestamptz,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id)
);

CREATE TABLE api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  key_hash text NOT NULL CHECK (key_hash ~ '^[a-f0-9]{64}$'),
  scopes text[] NOT NULL,
  ip_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  UNIQUE (key_hash)
);

CREATE TABLE support_access (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  project_id uuid,
  scope text NOT NULL CHECK (scope IN ('metadata','project_review')),
  reason text NOT NULL,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  granted_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id)
);

CREATE TABLE editing_presets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  scope text NOT NULL CHECK (scope IN ('project','ip','workspace')),
  ip_id uuid,
  project_id uuid,
  name text NOT NULL,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  spec jsonb NOT NULL,
  created_by uuid NOT NULL REFERENCES principals(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, id),
  FOREIGN KEY (tenant_id, ip_id) REFERENCES ips(tenant_id, id),
  FOREIGN KEY (tenant_id, project_id) REFERENCES projects(tenant_id, id),
  CHECK ((scope = 'workspace' AND num_nonnulls(ip_id, project_id) = 0) OR (scope = 'ip' AND ip_id IS NOT NULL AND project_id IS NULL) OR (scope = 'project' AND project_id IS NOT NULL AND ip_id IS NULL))
);

-- Indexes: dimensionless vector avoids assuming a particular embedding provider.
-- Exact search over eligible authorized chunks is the initial contract.
-- Add per-embedding-config partial expression ANN indexes only after dimension, recall and tenant isolation tests.
CREATE INDEX chunks_fts ON retrieval_chunks USING gin(search_vector);
CREATE INDEX chunks_scope ON retrieval_chunks(tenant_id, ip_id, asset_revision_id) WHERE deleted_at IS NULL;
CREATE INDEX jobs_ready ON generation_jobs(state, available_at, priority DESC) WHERE state IN ('queued','retry_wait');
CREATE INDEX jobs_lease ON generation_jobs(lease_until) WHERE lease_until IS NOT NULL;
CREATE INDEX dependencies_source ON shot_dependencies(tenant_id, source_kind, source_id);
CREATE INDEX assertion_branch_time ON assertion_revisions(tenant_id, branch_id, valid_story_from, valid_story_to);
CREATE INDEX feedback_project_time ON feedback_events(tenant_id, project_id, created_at);
CREATE INDEX outbox_pending ON outbox_events(available_at) WHERE published_at IS NULL;
CREATE INDEX inbox_pending ON webhook_inbox(received_at) WHERE processed_at IS NULL;
CREATE INDEX approvals_target ON approval_decisions(tenant_id, target_kind, target_id, created_at DESC);
CREATE INDEX audit_scope_time ON audit_events(tenant_id, occurred_at DESC);
CREATE INDEX reservations_active ON budget_reservations(tenant_id, account_id, state) WHERE state IN ('active','pending_liability','disputed');

-- Lease acquisition pattern, executed by a scoped scheduler transaction, NOT a generation call:
-- SELECT id FROM generation_jobs
-- WHERE tenant_id = ipmv.current_tenant_id() AND state IN ('queued','retry_wait') AND available_at <= now()
-- ORDER BY priority DESC, available_at FOR UPDATE SKIP LOCKED LIMIT 1;
-- Then UPDATE lease_owner/lease_until/state in this same transaction. External network calls occur after commit.
-- Expired lease does NOT imply provider submission failed. Inspect attempts and reconcile before submitting again.

-- All service writes require same-IP/project checks beyond tenant composite FKs.
-- Polymorphic IDs in approvals/dependencies/audit/deletion must resolve to the documented table and tenant.
-- Relationship subject/object types, branch inheritance cycles, one-valued temporal conflicts and approval scope
-- must be checked in the domain service; rejecting these cases is a release-blocking contract test.
-- Account and reservation currencies/account ownership must match in atomic ledger transactions.
-- IDs embedded in JSON/uuid[] must also pass live permission, existence and tenant checks before use.
-- These comments state explicit implementation gates, not claims that SQL alone enforces those invariants.

CREATE TRIGGER entity_revisions_immutable_update BEFORE UPDATE ON entity_revisions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER assertion_revisions_immutable_update BEFORE UPDATE ON assertion_revisions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER asset_revisions_immutable_update BEFORE UPDATE ON asset_revisions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER evidence_links_immutable_update BEFORE UPDATE ON evidence_links FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER song_segments_immutable_update BEFORE UPDATE ON song_segments FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER preference_revisions_immutable_update BEFORE UPDATE ON preference_revisions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER context_snapshots_immutable_update BEFORE UPDATE ON context_snapshots FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER shot_revisions_immutable_update BEFORE UPDATE ON shot_revisions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER shot_dependencies_immutable_update BEFORE UPDATE ON shot_dependencies FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER job_events_immutable_update BEFORE UPDATE ON job_events FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER takes_immutable_update BEFORE UPDATE ON takes FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER project_versions_immutable_update BEFORE UPDATE ON project_versions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER feedback_events_immutable_update BEFORE UPDATE ON feedback_events FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER approval_decisions_immutable_update BEFORE UPDATE ON approval_decisions FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER ledger_entries_immutable_update BEFORE UPDATE ON ledger_entries FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER audit_events_immutable_update BEFORE UPDATE ON audit_events FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER planning_artifacts_immutable_update BEFORE UPDATE ON planning_artifacts FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER memory_proposals_immutable_update BEFORE UPDATE ON memory_proposals FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

CREATE TRIGGER releases_immutable_update BEFORE UPDATE ON releases FOR EACH ROW EXECUTE FUNCTION ipmv.reject_version_update();

-- Version rows/events are append-only for ordinary writers. Privacy/content purging is a separate
-- audited privileged maintenance path, with dependency-order deletion and legal-retention exceptions.
-- Runtime roles receive no blanket DELETE/TRUNCATE permission. An approved purge must not silently
-- mutate old files: tombstone first, then delete content and record the deletion evidence.

ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON memberships USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE ips ENABLE ROW LEVEL SECURITY;
ALTER TABLE ips FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON ips USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE eras ENABLE ROW LEVEL SECURITY;
ALTER TABLE eras FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON eras USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE narrative_branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE narrative_branches FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON narrative_branches USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE entities FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON entities USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE entity_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE entity_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON entity_revisions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE predicate_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE predicate_definitions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON predicate_definitions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE assertions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assertions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON assertions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE assertion_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assertion_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON assertion_revisions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON assets USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE asset_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON asset_revisions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE evidence_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_links FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON evidence_links USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE songs ENABLE ROW LEVEL SECURITY;
ALTER TABLE songs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON songs USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE song_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE song_segments FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON song_segments USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON projects USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE access_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE access_grants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON access_grants USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE preference_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE preference_rules FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON preference_rules USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE preference_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE preference_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON preference_revisions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE context_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_snapshots FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON context_snapshots USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE shots ENABLE ROW LEVEL SECURITY;
ALTER TABLE shots FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON shots USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE shot_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE shot_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON shot_revisions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE shot_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE shot_dependencies FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON shot_dependencies USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE generation_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON generation_jobs USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE provider_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE provider_attempts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON provider_attempts USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE job_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON job_events USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE takes ENABLE ROW LEVEL SECURITY;
ALTER TABLE takes FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON takes USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE project_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON project_versions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE feedback_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON feedback_events USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON reviews USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE exports FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON exports USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE approval_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_decisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON approval_decisions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE budget_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_accounts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON budget_accounts USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE budget_reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_reservations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON budget_reservations USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON ledger_entries USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE webhook_inbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_inbox FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON webhook_inbox USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON outbox_events USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE retrieval_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE retrieval_chunks FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON retrieval_chunks USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON audit_events USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE deletion_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE deletion_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON deletion_requests USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE planning_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE planning_artifacts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON planning_artifacts USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE memory_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_proposals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON memory_proposals USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE share_links FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON share_links USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE releases FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON releases USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON upload_sessions USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON integrations USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON api_keys USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE support_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_access FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON support_access USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE editing_presets ENABLE ROW LEVEL SECURITY;
ALTER TABLE editing_presets FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON editing_presets USING (tenant_id = ipmv.current_tenant_id()) WITH CHECK (tenant_id = ipmv.current_tenant_id());

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_self ON tenants USING (id = ipmv.current_tenant_id()) WITH CHECK (id = ipmv.current_tenant_id());
-- Workspace provisioning uses a narrowly scoped bootstrap service role/function, not a public RLS bypass.
-- A worker processing several tenants creates a fresh transaction and validated tenant context per job.
-- Prevent user-controlled SQL and session-level SET reuse; reset pooled connections and test context leakage.

COMMIT;
