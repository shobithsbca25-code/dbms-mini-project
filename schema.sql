CREATE DATABASE IF NOT EXISTS expense_tracker_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE expense_tracker_db;

CREATE TABLE IF NOT EXISTS expenses (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(100) NOT NULL,
  category VARCHAR(50) NOT NULL,
  amount DECIMAL(11, 2) NOT NULL,
  spent_on DATE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_expenses_amount_positive CHECK (amount > 0)
);

-- Optional sample records. Run this section once if you want demo data.
INSERT INTO expenses (title, category, amount, spent_on) VALUES
  ('Groceries', 'Food', 42.80, '2026-10-25'),
  ('Bus pass', 'Travel', 18.00, '2026-10-26'),
  ('Notebook', 'Study', 6.50, '2026-10-27');
