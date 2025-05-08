import pickle
import asyncio
from asyncio import Semaphore

# Save the entire pickle object
def save_pickle(pickle_object, filename):
    with open(filename, 'wb') as f:
        pickle.dump(pickle_object, f)

# Load the entire pickle object
def load_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

async def run_concurrent(funcs, max_concurrent=20):
    semaphore = Semaphore(max_concurrent)

    async def sem_task(f):
        async with semaphore:
            return await f()

    return await asyncio.gather(*(sem_task(f) for f in funcs))
