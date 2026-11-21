ALTER TABLE `audit_submissions` ADD `input_payload_json` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `audit_submissions` ADD `output_payload_json` text DEFAULT '' NOT NULL;