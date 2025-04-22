import asyncio
from multiprocessing import Pool
from actions.tradingEngine import TradingEngine
from API.API_utils import fetch_complete_test_data
from utils.os_utils import load_historical_data_from_file, save_historical_data_to_file
from testing.plotter import PricePlotter
from testing.find_points import PointFinder
from analytics.time_utils import get_interval_in_minutes
import random
import time

REFRESH_INTERVAL = "5m"
INDICATOR_WINDOW = 80
FETCHING_SPAN_IN_DAYS = 200
OHLCV = False
RAW_DATA_PATH = "historical_data/"

async def fetch_new_data_point(token):
    await asyncio.sleep(0.5)  # Placeholder  - later interval conversion needed
    return {"price": 100, "unixTime": int(time.time() * 1000)}  # Add timestamp

def process_historical_data(args):
    interval, historical_data, testing_mode, start_idx, end_idx = args
    engine = TradingEngine(interval, historical_data[:start_idx])
    plotter = PricePlotter(engine)
    
    if testing_mode:
        for i in range(start_idx, end_idx if end_idx is not None else len(historical_data)):
            engine.add_new_price_point(historical_data[i])
            plotter.plot_live()
        point_finder = PointFinder(engine.metric_collector.metrics)
        point_finder.evaluate_zone_settings(price_increase=1.5, price_decrease=0.5)
        targets = point_finder.find_all_significant_price_increases(price_increase=1.5)
        similars_index = point_finder.find_all_significant_price_decreases(price_decrease=0.5)
        return engine, targets, similars_index
    return engine, None, None

async def live_monitoring(token, trading_engine):
    """Fetch data every 5 minutes exactly, processing in parallel."""
    interval_seconds = 300  # 5 minutes
    last_fetch_time = asyncio.get_event_loop().time()  # Start time

    while True:
        # Calculate time until next fetch
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - last_fetch_time
        sleep_time = max(0, interval_seconds - elapsed)
        await asyncio.sleep(sleep_time)

        # Fetch new data point
        new_point = await fetch_new_data_point(token)
        last_fetch_time = asyncio.get_event_loop().time()  # Update after fetch
        print(f"Fetched data for {token} at {new_point['unixTime'] / 1000:.0f}s")

        # Process in a thread (non-blocking)
        asyncio.create_task(
            asyncio.to_thread(trading_engine.metric_collector.add_new_price_point_and_calculate_metrics, new_point)
        )

async def initialize_token_environment(testing_mode, token, wallet):
    print(f"Starting environment for {token}")
    
    # Fetch historical data
    historical_data = None
    if testing_mode:
        print(f"Fetching data for token: {token}")
        try:
            historical_data = load_historical_data_from_file(
                filename=f"{RAW_DATA_PATH}historical_price_{token}_{REFRESH_INTERVAL}_{FETCHING_SPAN_IN_DAYS}_{OHLCV}.json"
            )
        except Exception as e:
            print(f"No data found for token {token}. Fetching from API.")
    
    if not historical_data:
        historical_data = await asyncio.to_thread(
            fetch_complete_test_data, token, REFRESH_INTERVAL, FETCHING_SPAN_IN_DAYS, ohlcv=OHLCV
        )

    if historical_data:
        save_historical_data_to_file(
            historical_data,
            filename=f"{RAW_DATA_PATH}historical_price_{token}_{REFRESH_INTERVAL}_{FETCHING_SPAN_IN_DAYS}_{OHLCV}.json"
        )
        print(f"Data saved for token: {token}")

    # Process historical data in a separate process
    starting_index = 50 if testing_mode else None
    end_index = None
    with Pool(1) as pool:
        tradingEngine, targets, similars_index = await asyncio.to_thread(
            pool.apply, 
            process_historical_data, 
            ((REFRESH_INTERVAL, historical_data["data"]["items"], testing_mode, starting_index, end_index),)
        )

    if testing_mode:
        print(f"Analyzed {(len(tradingEngine.metric_collector.metrics) * get_interval_in_minutes(REFRESH_INTERVAL)) / 60} hours of data for {token}")
        plotter = PricePlotter(tradingEngine)
        plotter.add_backtesting_points(targets, similars_index)
        try:
            plotter.plot_static()
        except Exception as e:
            print(e)

        # plotter.plot_live()  # only for testing implementation in this way. TODO: change that shit!
    else:
        # Start live monitoring as a separate task
        await live_monitoring(token, tradingEngine)


