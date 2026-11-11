CREATE TABLE `audit_submissions` (
	`id` text PRIMARY KEY NOT NULL,
	`client_name` text NOT NULL,
	`techs_per_shift` integer NOT NULL,
	`total_shifts` integer DEFAULT 3 NOT NULL,
	`manuals_volume_gb` real NOT NULL,
	`work_orders_count` integer NOT NULL,
	`avg_tokens_per_page` integer DEFAULT 420 NOT NULL,
	`deployment_constraint` text NOT NULL,
	`peak_query_ratio` real DEFAULT 0.4 NOT NULL,
	`avg_queries_per_tech_shift` integer DEFAULT 15 NOT NULL,
	`electricity_rate_kwh_usd` real DEFAULT 0.18 NOT NULL,
	`target_p95_ttft_seconds` real DEFAULT 1.5 NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `hardware_catalog` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`tier` text NOT NULL,
	`vram_gb` real NOT NULL,
	`system_ram_gb` real NOT NULL,
	`tdp_watts` integer NOT NULL,
	`unit_cost_capex_usd` real DEFAULT 0 NOT NULL,
	`monthly_maint_opex_usd` real DEFAULT 0 NOT NULL,
	`max_bandwidth_gbps` real NOT NULL
);
--> statement-breakpoint
CREATE TABLE `model_registry` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`param_count_b` real NOT NULL,
	`context_window_tokens` integer NOT NULL,
	`hidden_dim` integer NOT NULL,
	`layer_count` integer NOT NULL,
	`q_head_count` integer NOT NULL,
	`kv_head_count` integer NOT NULL,
	`head_dim` integer NOT NULL,
	`weight_quant_bits` integer NOT NULL,
	`kv_cache_bits` integer DEFAULT 16 NOT NULL,
	`input_token_cost_1m` real DEFAULT 0 NOT NULL,
	`output_token_cost_1m` real DEFAULT 0 NOT NULL,
	`is_edge_compatible` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `telemetry_calibration` (
	`id` text PRIMARY KEY NOT NULL,
	`model_id` text NOT NULL,
	`hardware_id` text NOT NULL,
	`measured_p95_ttft_ms` real NOT NULL,
	`measured_peak_vram_gb` real NOT NULL,
	`measured_context_recall` real NOT NULL,
	`measured_faithfulness` real NOT NULL,
	`compute_scaling_multiplier` real DEFAULT 1 NOT NULL,
	`rolling_sample_count` integer NOT NULL,
	`last_updated` integer NOT NULL,
	FOREIGN KEY (`model_id`) REFERENCES `model_registry`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`hardware_id`) REFERENCES `hardware_catalog`(`id`) ON UPDATE no action ON DELETE no action
);
