# 🗄️ Database — Annotation Quality Guardian

## Overview

This directory contains the PostgreSQL schema and sample data for the AQG platform.

## Files

| File              | Description                                    |
|-------------------|------------------------------------------------|
| `schema.sql`      | Table creation scripts (DDL)                   |
| `sample_data.sql` | Sample insert statements for development/testing |

## Tables

| Table            | Purpose                                       |
|------------------|-----------------------------------------------|
| `projects`       | Annotation projects with label sets            |
| `annotators`     | Registered annotators                          |
| `items`          | Data points to be annotated (with gold flags)  |
| `annotations`    | Individual annotation records                  |
| `quality_scores` | Computed quality metrics per project/annotator  |

## Setup

```bash
# Create database
psql -U postgres -c "CREATE DATABASE aqg_db;"

# Run schema
psql -U postgres -d aqg_db -f schema.sql

# Load sample data
psql -U postgres -d aqg_db -f sample_data.sql
```

## ER Diagram

```
projects 1──* items 1──* annotations *──1 annotators
    │                                        │
    └──────────── quality_scores ─────────────┘
```
