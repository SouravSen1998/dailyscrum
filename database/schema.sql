CREATE DATABASE IF NOT EXISTS daily_scrum;
USE daily_scrum;

CREATE TABLE IF NOT EXISTS jira_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jira_key VARCHAR(50) NOT NULL UNIQUE,
    summary VARCHAR(500) NOT NULL,
    status VARCHAR(100),
    priority VARCHAR(50),
    assignee_name VARCHAR(255),
    assignee_email VARCHAR(255),
    client_name VARCHAR(255),
    project_name VARCHAR(255),
    support_type VARCHAR(100),
    target_delivery_date DATE NULL,
    jira_created_at DATETIME NULL,
    jira_updated_at DATETIME NULL,
    age_days DECIMAL(10,2) DEFAULT 0,
    product_name VARCHAR(255),
    raw_json JSON NULL,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticket_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jira_ticket_key VARCHAR(50) NOT NULL,
    comment_text TEXT,
    commented_by VARCHAR(255),
    commented_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
