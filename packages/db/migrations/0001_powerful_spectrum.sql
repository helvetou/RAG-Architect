ALTER TABLE `audit_submissions` ADD `actor_id` text DEFAULT 'system' NOT NULL;--> statement-breakpoint
ALTER TABLE `audit_submissions` ADD `input_payload_sha256` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `audit_submissions` ADD `output_payload_sha256` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `audit_submissions` ADD `spec_version` text DEFAULT 'SPEC-GMAO-RAG-ARCH-003' NOT NULL;--> statement-breakpoint
ALTER TABLE `audit_submissions` ADD `model_version` text DEFAULT 'llama-3.2-3b-instruct-q4' NOT NULL;--> statement-breakpoint
CREATE TRIGGER `audit_submissions_append_only_update`
BEFORE UPDATE ON `audit_submissions`
BEGIN
  SELECT RAISE(ABORT, 'audit_submissions is append-only');
END;--> statement-breakpoint
CREATE TRIGGER `audit_submissions_append_only_delete`
BEFORE DELETE ON `audit_submissions`
BEGIN
  SELECT RAISE(ABORT, 'audit_submissions is append-only');
END;