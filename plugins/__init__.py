import asyncio
import importlib
import os
import logging
import time
import inspect


async def init(client):
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.ERROR)

    plugins = [
        importlib.import_module(f'.', f'{__name__}.{file[:-3]}')

        for file in os.listdir(os.path.dirname(__file__))

        if file[0].isalpha() and file.endswith('.py')
    ]

    modules = {m.__name__.split('.')[-1]: m for m in plugins}

    to_init = (get_init_coro(plugin, client=client, modules=modules) for plugin in plugins)

    await asyncio.gather(*(filter(None, to_init)))


def get_init_coro(plugin, **kwargs):
    p_init = getattr(plugin, 'init', None)
    if not callable(p_init):
        return

    result_kwargs = {}
    sig = inspect.signature(p_init)
    for param in sig.parameters:
        if param in kwargs:
            result_kwargs[param] = kwargs[param]
        else:
            logging.error('Plugin %s has unknown init parameter %s', plugin.__name__, param.__name__)
            return

    return _init_plugin(plugin, result_kwargs)


async def _init_plugin(plugin, kwargs):
    try:
        logging.warning(f'Loading plugin {plugin.__name__}…')
        start = time.time()
        ret = await plugin.init(**kwargs)
        took = time.time() - start
        logging.warning(f'Loaded plugin {plugin.__name__} (took {took:.2f}s)')
    except Exception:
        logging.exception(f'Failed to load plugin {plugin}')
    else:
        if asyncio.iscoroutinefunction(ret):
            await ret


async def start_plugins(bot, plugins):
    await asyncio.gather(*(_init_plugin(bot, plugin) for plugin in plugins))
