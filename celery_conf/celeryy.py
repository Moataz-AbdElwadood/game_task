from celery import Celery

celery = Celery()  # Create a Celery instance
celery.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/0",
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'check-task-queue': {
            'task': 'tasks.check_expired_tasks',
            'schedule': 30.0,  # Runs every 30 seconds
        },
    },
    include=['tasks']
)



def make_celery(app):
    """
    Configure the Celery instance using the Flask app.
    """
    celery.conf.update(app.config)
    
    # Bind Flask app context to Celery tasks
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


