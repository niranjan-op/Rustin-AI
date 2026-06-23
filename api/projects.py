import os
import sqlite3
import uuid
from datetime import datetime

from chainlit.server import app
from chainlit.auth import get_current_user
from chainlit.user import User
from fastapi import HTTPException, Query, Depends
from pydantic import BaseModel, Field

DB_PATH = ".files/test.db"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="My Project")
    path: str = Field(..., min_length=1, example="C:/projects/my-project")
    description: str = Field(..., min_length=1, example="A project description")
    instructions: str | None = None


class ProjectResponse(BaseModel):
    name: str
    path: str
    description: str
    instructions: str | None = None


class ProjectListResponse(BaseModel):
    id: str
    name: str
    path: str


@app.get(r"/api/projects/validate-path")
async def validate_path(
    path: str = Query(..., description="The absolute path to validate", min_length=1),
):
    normalized_path = os.path.normpath(os.path.expanduser(path))
    exists = os.path.isdir(normalized_path)
    return {"exists": exists}


@app.post(r"/api/projects/create-project", response_model=dict)
async def create_project(project: ProjectCreate, current_user: User | None = Depends(get_current_user)):
    user_identifier = current_user.identifier if current_user else "guest"
    normalized_path = os.path.normpath(os.path.expanduser(project.path))
    if not os.path.isdir(normalized_path):
        raise HTTPException(
            status_code=400,
            detail=f"path '{project.path}' does not exist on this machine",
        )
    if project.instructions == None:
        project.instructions = "None"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        project_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO PROJECTS(id, name, path, description, created_at, updated_at, instructions, git_branch, user_identifier)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                project_id,
                project.name,
                project.path,
                project.description,
                str(datetime.now().isoformat()),
                str(datetime.now().isoformat()),
                project.instructions,
                "None",
                user_identifier,
            ),
        )
        conn.commit()
        return {
            "status": "success",
            "message": f"Project:`{project.name}` created successfully",
            "project_id": project_id,
            "project_path": project.path,
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400, detail=f"A project named '{project.name}' already exists."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@app.get(r"/api/projects/projects-list", response_model=list[ProjectListResponse])
async def projects_list(current_user: User | None = Depends(get_current_user)):
    user_identifier = current_user.identifier if current_user else "guest"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, path FROM projects
            WHERE user_identifier = ?
            ORDER BY created_at DESC;
            """,
            (user_identifier,)
        )
        rows = cursor.fetchall()
        return [
            ProjectListResponse(id=row[0], name=row[1], path=row[2]) for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database Error: {str(e)}")
    finally:
        conn.close()


@app.delete(r"/api/projects/delete-project")
async def delete_project(
    project_id: str = Query(..., description="The project ID to delete"),
    current_user: User | None = Depends(get_current_user)
):
    user_identifier = current_user.identifier if current_user else "guest"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM PROJECTS WHERE id=? AND user_identifier = ?;
            """,
            (project_id, user_identifier),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"status": "success", "message": "Project deleted successfully!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


# =========================================================
# ROUTE REORDERING
# Chainlit registers a catch-all /{full_path:path} route
# that intercepts all requests. Move it to the end so our
# custom /api/* routes are matched first.
# =========================================================
_catchall = None
for i, route in enumerate(app.routes):
    if hasattr(route, "path") and route.path == "/{full_path:path}":
        _catchall = app.routes.pop(i)
        break
if _catchall:
    app.routes.append(_catchall)
