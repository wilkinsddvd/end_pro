-- Migration: Add response-time columns to ticket table
-- Run this script against an existing database to add the new columns.

ALTER TABLE ticket
    ADD COLUMN first_response_at DATETIME NULL COMMENT '首次回复时间',
    ADD COLUMN completed_at DATETIME NULL COMMENT '完成时间';

CREATE INDEX idx_response_time ON ticket(created_at, first_response_at);
