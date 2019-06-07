import logging

from algernon.aws import lambda_logged
from algernon import ajson

from toll_booth.tasks import review

_task_modules = (review,)


def _find_task(task_name):
    tasks = []
    for task_module in _task_modules:
        task_fn = getattr(task_module, task_name)
        if task_fn:
            tasks.append(task_fn)
    if len(tasks) > 1:
        raise RuntimeError(f'name collision for task_name: {task_name}, found: {tasks}')
    for entry in tasks:
        return entry
    raise NotImplementedError(f'could not find task for task_name: {task_name}')


@lambda_logged
def handler(event, context):
    logging.info(f'received a call to run an auditor task, event/context: {event}/{context}')
    task_name = event['task_name']
    task_kwargs = event['task_kwargs']
    flow_id = event['flow_id']
    task_kwargs['flow_id'] = flow_id
    task_fn = _find_task(task_name)
    results = task_fn(**task_kwargs)
    logging.info(f'completed an auditor task, results: {results}')
    return ajson.dumps(results)
