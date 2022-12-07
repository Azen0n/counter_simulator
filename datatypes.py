from __future__ import annotations

import random
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import asyncio


@dataclass
class Counter:
    id: UUID = field(default_factory=uuid4)
    min_time: int = 1
    max_time: int = 10
    queue_size: int = 0
    service_times: list[int] = field(default_factory=list)
    is_working: bool = False
    is_on_pause: bool = False

    @property
    def service_time(self) -> int:
        return random.randint(self.min_time, self.max_time)

    @property
    def average_service_time(self) -> float:
        try:
            return sum(self.service_times) / len(self.service_times)
        except ZeroDivisionError:
            return 0

    def update_time(self, min_time: int, max_time: int):
        self.min_time = min_time
        self.max_time = max_time

    async def run_service(self):
        await asyncio.create_task(self.service())

    async def service(self):
        while not self.is_working:
            if self.queue_size > 0:
                service_time = self.service_time
                self.service_times.append(service_time)
                print(f'Counter {self.id} serving a client in {service_time} s...')
                for i in range(service_time):
                    await asyncio.sleep(1)
                    while self.is_on_pause:
                        await asyncio.sleep(1)
                self.queue_size -= 1
                print(f'Counter {self.id} served a client.')
            else:
                await asyncio.sleep(1)
        print(f'Counter {self.id} stopped service.')


@dataclass
class CounterSimulator:
    wave_max_interval: int
    wave_max_size: int
    counters: list[Counter] = field(default_factory=list)
    last_wave_size: int | None = None
    complainers: int = 0
    is_on_pause: bool = False

    def __post_init__(self):
        for _ in range(5):
            self.counters.append(Counter())

    def find_counter(self, counter_id: UUID) -> Counter | None:
        for counter in self.counters:
            if counter.id == counter_id:
                return counter
        return None

    async def start(self):
        start_counters_task = asyncio.create_task(self.start_counters())
        wave_task = asyncio.create_task(self.wave())
        await wave_task
        await start_counters_task

    async def wave(self):
        while True:
            wave_size = random.randint(0, self.wave_max_size)
            self.last_wave_size = wave_size
            self.allocate_clients(wave_size)
            print(f'Allocated {wave_size} clients. Status: {self.status}')
            sleep_time = random.randint(1, self.wave_max_interval)
            for _ in range(sleep_time):
                await asyncio.sleep(1)
                while self.is_on_pause:
                    await asyncio.sleep(1)

    def allocate_clients(self, number_of_clients: int):
        if self.counters:
            number_of_clients += self.complainers
            for i in range(number_of_clients):
                least_busy_counter = self.find_least_busy_counter()
                least_busy_counter.queue_size += 1
            self.complainers = 0
        else:
            self.complainers += number_of_clients

    async def start_counters(self):
        counter_tasks = [asyncio.create_task(counter.service()) for counter in self.counters]
        for task in counter_tasks:
            await task
        print('Counters started.')

    def find_least_busy_counter(self) -> Counter | None:
        sorted_counters = sorted(self.counters, key=lambda x: x.queue_size)
        return sorted_counters[0] if sorted_counters else None

    @property
    def status(self) -> str:
        return ', '.join([f'{counter.queue_size}' for counter in self.counters])

    def create_counter(self):
        counter = Counter()
        self.counters.append(counter)
        return counter

    def update_wave(self, wave_max_size: int, wave_max_interval: int):
        self.wave_max_size = wave_max_size
        self.wave_max_interval = wave_max_interval

    def delete_counter(self, counter_id: UUID) -> int:
        counter = self.find_counter(counter_id)
        self.counters.remove(counter)
        queue_size = counter.queue_size
        counter.is_working = True
        del counter
        return queue_size

    def reallocate_queues(self):
        total_queue_size = sum([counter.queue_size for counter in self.counters])
        average_size = int(total_queue_size / len(self.counters))
        remaining_clients = total_queue_size - (average_size * len(self.counters))
        for counter in self.counters:
            counter.queue_size = average_size
        self.allocate_clients(remaining_clients)
