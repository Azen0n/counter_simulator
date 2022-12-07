import asyncio

import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from datatypes import CounterSimulator, Counter

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

counter_simulator = CounterSimulator(wave_max_interval=10, wave_max_size=5)


@app.on_event('startup')
async def startup_event():
    asyncio.create_task(counter_simulator.start())


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    context = {
        'request': request,
        'counter_simulator': counter_simulator,
    }
    return templates.TemplateResponse('index.html', context)


@app.post('/create_counter')
async def create_counter(background_tasks: BackgroundTasks):
    counter = counter_simulator.create_counter(is_on_pause=counter_simulator.is_on_pause)
    counter_simulator.reallocate_queues()
    background_tasks.add_task(counter.run_service)
    return counter


@app.post('/change_number_of_counters')
async def change_number_of_counters(background_tasks: BackgroundTasks, number_of_counters: int = Form(...)):
    if number_of_counters < 0:
        return
    counters = {'action': 'none', 'counters': []}
    if len(counter_simulator.counters) > number_of_counters:
        counters['action'] = 'delete'
        for counter in counter_simulator.counters[number_of_counters:]:
            counters['counters'].append(counter.id)
            remaining_clients = counter_simulator.delete_counter(counter.id)
            counter_simulator.allocate_clients(remaining_clients)
    elif len(counter_simulator.counters) < number_of_counters:
        counters['action'] = 'create'
        for _ in range(number_of_counters - len(counter_simulator.counters)):
            counter = counter_simulator.create_counter(is_on_pause=counter_simulator.is_on_pause)
            counters['counters'].append(counter)
            counter_simulator.reallocate_queues()
        background_tasks.add_task(run_all_services, counters['counters'])
    return counters


async def run_all_services(counters: list[Counter]):
    tasks = [asyncio.create_task(counter.service()) for counter in counters]
    for task in tasks:
        await task


@app.post('/update_counter/{counter_id}')
async def update_counter(counter_id: int, min_time: int = Form(...), max_time: int = Form(...)):
    counter = counter_simulator.find_counter(counter_id)
    if not (1 <= min_time <= max_time and max_time >= 1):
        print('Counter not updated')
        return counter if counter else None
    counter = counter_simulator.find_counter(counter_id)
    if counter:
        counter.update_time(min_time, max_time)
        return counter
    print('Counter not found')
    return


@app.post('/update_counter_simulator')
async def update_counter_simulator(wave_max_size: int = Form(...), wave_max_interval: int = Form(...)):
    if not (wave_max_size >= 0 and wave_max_interval >= 1):
        print('Counter Simulator not updated')
        return
    counter_simulator.update_wave(wave_max_size, wave_max_interval)
    return counter_simulator


@app.delete('/delete_counter/{counter_id}')
async def delete_counter(counter_id: int):
    remaining_clients = counter_simulator.delete_counter(counter_id)
    counter_simulator.allocate_clients(remaining_clients)
    return counter_simulator


@app.get('/fetch')
async def fetch():
    return {'counter_simulator': counter_simulator}


@app.post('/toggle_pause')
async def toggle_pause():
    counter_simulator.is_on_pause = not counter_simulator.is_on_pause
    for counter in counter_simulator.counters:
        counter.is_on_pause = not counter.is_on_pause
    print(f'Counter Simulator {"is on pause" if counter_simulator.is_on_pause else "works again"}')
    return {'is_on_pause': counter_simulator.is_on_pause}


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=1234, reload=True, workers=3)
