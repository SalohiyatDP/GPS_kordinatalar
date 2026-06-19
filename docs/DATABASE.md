# Database Schema

The application uses **SQLite** via SQLAlchemy 2.0. The database file location is
configurable with `APP_DATABASE_URL` (default `sqlite:///./cadastre.db`).

Tables are created automatically on startup (`init_db()`).

## Table: `projects`

Stores saved analysis sessions. Geometry/analysis payloads are stored as JSON
text columns for flexibility.

| Column           | Type        | Notes                                   |
|------------------|-------------|-----------------------------------------|
| `id`             | INTEGER PK  | Auto-increment                          |
| `name`           | VARCHAR(255)| Project name (default `Untitled`)       |
| `created_at`     | DATETIME    | Set on insert                           |
| `updated_at`     | DATETIME    | Updated on modification                 |
| `points_json`    | TEXT        | JSON array of normalized points         |
| `area_json`      | TEXT        | JSON area result (m²/ha/km²/sotix)      |
| `perimeter_json` | TEXT        | JSON perimeter result (m/km)            |
| `analysis_json`  | TEXT        | JSON cadastre analysis (contours, etc.) |

### Example `points_json`
```json
[{ "point_number": 1, "latitude": 41.13, "longitude": 71.63,
   "dms": "41°07'54.29\"N 71°37'49.17\"E" }]
```

### Notes on contour layers

Uploaded contour shapefiles are **not** persisted in the database. They are held
in an in-memory store (keyed by `layer_id`) for the duration of the analysis
session, which keeps large shapefiles (100k+ features) out of the relational
store and enables fast spatial-index reuse across requests.

## ER overview

```
┌──────────────────────────────┐
│           projects           │
├──────────────────────────────┤
│ id (PK)                       │
│ name                          │
│ created_at / updated_at       │
│ points_json                   │
│ area_json                     │
│ perimeter_json                │
│ analysis_json                 │
└──────────────────────────────┘
```
