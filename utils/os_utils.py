import json
import os

def save_historical_data_to_file(data, filename="historical_price.json"):
    """
    Saves historical price data to a JSON file.
    
    :param data: The historical price data (dictionary) to save.
    :param filename: The name of the file to store data.
    """
    if data is None:
        print("No data to save.")
        return
    
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def load_historical_data_from_file(filename="historical_price.json"):
    """
    Loads historical price data from a JSON file.

    :param filename: The name of the file to read data from.
    :return: The historical price data in the same format as returned by `get_historical_price`.
    """
    if not os.path.exists(filename):
        print("No stored data found.")
        return None

    try:
        with open(filename, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def save_metrics_to_csv(metrics, token_address, output_dir="metrics"):
    """
    Save collected metrics for a token to a CSV file.
    
    Args:
        metrics (list): List of dictionaries containing metrics for a token.
        token_address (str): Token mint address (e.g., 'tokenA_address').
        output_dir (str): Directory to save CSV files (default: 'metrics').
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Flatten nested dictionaries in metrics
    flat_metrics = []
    for metric in metrics:
        flat_dict = {}
        for key, value in metric.items():
            if isinstance(value, dict):
                # Flatten nested dicts (e.g., 'momentum', 'volatility')
                for sub_key, sub_value in value.items():
                    flat_dict[f"{key}_{sub_key}"] = sub_value
            else:
                flat_dict[key] = value
        flat_metrics.append(flat_dict)
    
    # Create DataFrame
    df = pd.DataFrame(flat_metrics)
    
    # Sanitize token address for filename
    safe_token = "".join(c for c in token_address if c.isalnum() or c in ['_', '-'])
    filename = f"{output_dir}/metrics_{safe_token}.csv"
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"Saved metrics for {token_address} to {filename} ({len(df)} rows)")