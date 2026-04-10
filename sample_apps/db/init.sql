-- ============================================================
-- Ankole Framework - PostgreSQL Database Schema
-- ============================================================

-- Clean slate
DROP TABLE IF EXISTS approvals CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TYPE IF EXISTS project_status;
DROP TYPE IF EXISTS approval_status;

-- ------------------------------------------------------------
-- Custom enum types
-- ------------------------------------------------------------
CREATE TYPE project_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected');
CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected');

-- ------------------------------------------------------------
-- Roles
-- ------------------------------------------------------------
CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,
    description VARCHAR(255),
    permissions JSONB        NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Users
-- ------------------------------------------------------------
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role_id       INTEGER      NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Projects
-- ------------------------------------------------------------
CREATE TABLE projects (
    id                 SERIAL PRIMARY KEY,
    name               VARCHAR(120) NOT NULL,
    description        TEXT,
    status             project_status NOT NULL DEFAULT 'draft',
    created_by         INTEGER        NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    required_approvals INTEGER        NOT NULL DEFAULT 3,
    created_at         TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP      NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Approvals  (one row per approval step per project)
-- ------------------------------------------------------------
CREATE TABLE approvals (
    id          SERIAL PRIMARY KEY,
    project_id  INTEGER         NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    approver_id INTEGER         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    step_number INTEGER         NOT NULL,
    status      approval_status NOT NULL DEFAULT 'pending',
    comment     TEXT,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, step_number)
);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
CREATE INDEX idx_users_role        ON users(role_id);
CREATE INDEX idx_projects_creator  ON projects(created_by);
CREATE INDEX idx_projects_status   ON projects(status);
CREATE INDEX idx_approvals_project ON approvals(project_id);
CREATE INDEX idx_approvals_approver ON approvals(approver_id);

-- ============================================================
-- Seed data
-- ============================================================

-- Roles -------------------------------------------------------
INSERT INTO roles (name, description, permissions) VALUES
  ('admin',    'Full system administrator',
   '["manage_users","manage_roles","manage_projects","approve_projects","view_dashboard"]'),
  ('approver', 'Can review and approve projects',
   '["approve_projects","view_dashboard","view_projects"]'),
  ('member',   'Regular member who can create projects',
   '["create_projects","view_dashboard","view_projects"]');

-- Users -------------------------------------------------------
-- Passwords are placeholder hashes.
-- The Flask application uses werkzeug.security to hash and verify passwords.
-- On first run the app re-hashes these with generate_password_hash().
-- Plain-text passwords for test/dev purposes are noted in comments.

-- admin / admin123
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
  ('admin', 'admin@ankole.local',
   'placeholder_will_be_set_by_app',
   (SELECT id FROM roles WHERE name = 'admin'), TRUE);

-- approver1 / approver123
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
  ('approver1', 'approver1@ankole.local',
   'placeholder_will_be_set_by_app',
   (SELECT id FROM roles WHERE name = 'approver'), TRUE);

-- approver2 / approver123
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
  ('approver2', 'approver2@ankole.local',
   'placeholder_will_be_set_by_app',
   (SELECT id FROM roles WHERE name = 'approver'), TRUE);

-- approver3 / approver123
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
  ('approver3', 'approver3@ankole.local',
   'placeholder_will_be_set_by_app',
   (SELECT id FROM roles WHERE name = 'approver'), TRUE);

-- member1 / member123
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
  ('member1', 'member1@ankole.local',
   'placeholder_will_be_set_by_app',
   (SELECT id FROM roles WHERE name = 'member'), TRUE);

-- member2 / member123
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
  ('member2', 'member2@ankole.local',
   'placeholder_will_be_set_by_app',
   (SELECT id FROM roles WHERE name = 'member'), TRUE);
