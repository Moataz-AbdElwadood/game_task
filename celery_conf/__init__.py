from celery import Celery

celery = Celery()  # Create a Celery instance

celery.conf.update(
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
