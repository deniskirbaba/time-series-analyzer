import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from redis import Redis
from rq import Queue
from rq.job import Job
from sqlalchemy.ext.asyncio import AsyncSession

from contracts import (
    ModelResponse,
    TaskResponse,
    TimeSeriesCreate,
    TimeSeriesResponse,
    Token,
    UserRegistration,
    UserResponse,
)
from db import (
    AsyncSessionLocal,
    create_task,
    create_time_series,
    create_user,
    delete_time_series,
    get_all_models,
    get_db,
    get_task_by_task_id,
    get_tasks_for_user,
    get_time_series_by_id,
    get_user_by_login,
    init_db,
    populate_models,
    update_analysis_results,
    update_task_by_task_id,
    update_user_balance,
)
from security import (
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from tasks import task_analyze_time_series

load_dotenv()

redis_conn = Redis(
    host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=0
)
queue = Queue("default", connection=redis_conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as session:
        await populate_models(session, Path("data/models_info.json"))
    yield


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user_by_login(db, username)
    if user is None:
        raise credentials_exception

    return UserResponse(
        id=user.id,
        login=user.login,
        name=user.name,
        balance=user.balance,
        time_series=[ts.id for ts in user.time_series],
    )


@app.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegistration, db: Annotated[AsyncSession, Depends(get_db)]
):
    existing_user = await get_user_by_login(db, user_data.login)
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this login already exists."
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = await create_user(
        db=db,
        login=user_data.login,
        hashed_password=hashed_password,
        name=user_data.name,
        balance=0.0,
    )

    return UserResponse(
        id=db_user.id,
        login=db_user.login,
        name=db_user.name,
        balance=db_user.balance,
        time_series=[],
    )


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.login})
    return Token(access_token=access_token, token_type="bearer")


@app.get("/get_current_user_by_access_token", response_model=UserResponse)
async def get_current_user_by_access_token(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return current_user


@app.post("/top_up_balance", response_model=UserResponse)
async def top_up_balance(
    amount: float,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    updated_user = await update_user_balance(db, current_user.id, amount)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=updated_user.id,
        login=updated_user.login,
        name=updated_user.name,
        balance=updated_user.balance,
        time_series=[ts.id for ts in updated_user.time_series],
    )


@app.post("/time_series", response_model=TimeSeriesResponse)
async def create_time_series_endpoint(
    ts_data: TimeSeriesCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if not ts_data.data:
        raise HTTPException(status_code=400, detail="Data cannot be empty")
    assert ts_data.user_id == current_user.id, "User ID does not match"

    db_ts = await create_time_series(
        db=db, user_id=ts_data.user_id, name=ts_data.name, data=ts_data.data
    )

    return TimeSeriesResponse(
        id=db_ts.id,
        user_id=db_ts.user_id,
        name=db_ts.name,
        created_at=db_ts.created_at,
        length=db_ts.length,
        data=db_ts.data,
        analysis_results=db_ts.analysis_results,
        forecasting_ts=db_ts.forecasting_ts,
    )


@app.get("/time_series/{ts_id}", response_model=TimeSeriesResponse)
async def get_time_series_endpoint(
    ts_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    db_ts = await get_time_series_by_id(db, ts_id)

    if not db_ts:
        raise HTTPException(status_code=404, detail="Time series not found")
    assert db_ts.user_id == current_user.id, "User ID does not match"

    return TimeSeriesResponse(
        id=db_ts.id,
        user_id=db_ts.user_id,
        name=db_ts.name,
        created_at=db_ts.created_at,
        length=db_ts.length,
        data=db_ts.data,
        analysis_results=db_ts.analysis_results,
        forecasting_ts=db_ts.forecasting_ts,
    )


@app.delete("/time_series/{ts_id}")
async def delete_time_series_endpoint(
    ts_id: int,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[UserResponse, Depends(get_current_user)],
):
    success = await delete_time_series(db, ts_id, user_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Time series not found or you don't have permission to delete it",
        )

    return {"message": "Time series deleted successfully"}


@app.get("/models", response_model=list[ModelResponse])
async def get_all_models_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[UserResponse, Depends(get_current_user)],
):
    db_models = await get_all_models(db)

    return [
        ModelResponse(name=model.name, info=model.info, tariffs=model.tariffs)
        for model in db_models
    ]


@app.post("/analyze_time_series")
async def analyze_time_series_endpoint(
    ts_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):
    if ts_id not in user.time_series:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to analyze this time series",
        )

    ts = await get_time_series_by_id(db, ts_id)
    ts_data = [d for d in ts.data]  # to avoid lazy loading issues

    if not ts:
        raise HTTPException(status_code=404, detail="Time series not found")

    task = await create_task(db, ts_id, user.id, 0, "analyze", "", "queued")

    job = queue.enqueue(
        task_analyze_time_series,
        ts_data,
        task.id,
        job_timeout="10m",
    )

    job.meta["task_id"] = task.id
    job.save_meta()

    return {"message": "Task enqueued successfully"}


@app.get("/tasks", response_model=list[TaskResponse])
async def get_tasks_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserResponse, Depends(get_current_user)],
):
    tasks = await get_tasks_for_user(db, user.id)

    return [
        TaskResponse(
            user_id=task.user_id,
            ts_id=task.ts_id,
            cost=task.cost,
            type=task.type,
            params=task.params,
            status=task.status,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]


@app.post("/process_job_results")
async def process_job_results_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Iterating through RQ jobs and update database accordingly.
    This endpoint should be called periodically.
    """
    processed_count = 0

    try:
        started_jobs = queue.started_job_registry.get_job_ids()
        for job_id in started_jobs:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                if job.meta and "task_id" in job.meta:
                    task_id = job.meta["task_id"]
                    await update_task_by_task_id(db, task_id, "in_progress")
                    processed_count += 1
            except Exception as e:
                print(f"Error processing started job {job_id}: {e}")
                continue

        finished_jobs = queue.finished_job_registry.get_job_ids()
        for job_id in finished_jobs:
            try:
                job = Job.fetch(job_id, connection=redis_conn)

                if job.is_finished and job.result:
                    result = job.result

                    if isinstance(result, dict) and "task_id" in result:
                        task_id = result["task_id"]

                        if result.get("success"):
                            await update_task_by_task_id(db, task_id, "done")

                            task = await get_task_by_task_id(db, task_id)
                            if task and "results" in result:
                                await update_analysis_results(
                                    db, task.ts_id, result["results"]
                                )
                            processed_count += 1
                        else:
                            await update_task_by_task_id(db, task_id, "failed")
                            processed_count += 1

                queue.finished_job_registry.remove(job_id)

            except Exception as e:
                print(f"Error processing finished job {job_id}: {e}")
                continue

        failed_jobs = queue.failed_job_registry.get_job_ids()
        for job_id in failed_jobs:
            try:
                job = Job.fetch(job_id, connection=redis_conn)

                task_id = None
                if (
                    job.result
                    and isinstance(job.result, dict)
                    and "task_id" in job.result
                ):
                    task_id = job.result["task_id"]
                elif job.meta and "task_id" in job.meta:
                    task_id = job.meta["task_id"]

                if task_id:
                    await update_task_by_task_id(db, task_id, "failed")
                    processed_count += 1

                queue.failed_job_registry.remove(job_id)

            except Exception as e:
                print(f"Error processing failed job {job_id}: {e}")
                continue

        deferred_jobs = queue.deferred_job_registry.get_job_ids()
        for job_id in deferred_jobs:
            try:
                job = Job.fetch(job_id, connection=redis_conn)

                if job.meta and "task_id" in job.meta:
                    task_id = job.meta["task_id"]
                    await update_task_by_task_id(db, task_id, "failed")
                    processed_count += 1

                queue.deferred_job_registry.remove(job_id)

            except Exception as e:
                print(f"Error processing deferred job {job_id}: {e}")
                continue

        canceled_jobs = queue.canceled_job_registry.get_job_ids()
        for job_id in canceled_jobs:
            try:
                job = Job.fetch(job_id, connection=redis_conn)

                if job.meta and "task_id" in job.meta:
                    task_id = job.meta["task_id"]
                    await update_task_by_task_id(db, task_id, "failed")
                    processed_count += 1

                queue.canceled_job_registry.remove(job_id)

            except Exception as e:
                print(f"Error processing canceled job {job_id}: {e}")
                continue

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing jobs: {e}")

    return {"message": f"Processed {processed_count} jobs across all states"}
