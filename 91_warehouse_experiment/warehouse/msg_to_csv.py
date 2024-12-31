import os

import pandas as pd


class MessageToCSVProcessor:
    def __init__(self, output_folder, name_prefix, save_interval=1000, verbose=False):
        self.messages = []
        self.name_prefix = name_prefix
        self.output_folder = output_folder
        self.save_interval = save_interval
        self.save_counter = 0
        self.verbose = verbose

    def process_event(self, msg_dict):
        self.messages.append(msg_dict)
        if self.verbose:
            print(f"Processed event: {msg_dict}")
        if len(self.messages) % self.save_interval == 0:
            self.save_and_clear()

    def close(self):
        if self.verbose:
            print("Closing and saving remaining messages.")
        self.save_and_clear()

    def save_and_clear(self):
        if len(self.messages) == 0:
            if self.verbose:
                print("No messages to save. Skipping.")
            return
        if self.verbose:
            print(
                f"Saving {len(self.messages)} messages to file: {self.output_folder}/{self.name_prefix}_{self.save_counter}.csv")
        self.save_to_csv(f"{self.output_folder}/{self.name_prefix}_{self.save_counter}.csv")
        self.save_counter += 1
        self.messages = []

    def save_to_csv(self, output_csv_file):
        """
        Save provided JSON messages to a CSV file.

        Args:
            output_csv_file (str): Path to the output CSV file.
        """

        # Convert the list of dictionaries into a DataFrame
        df = pd.DataFrame(self.messages)

        # Flatten dictionaries within the messages (e.g., `timestamps`)
        if 'timestamps' in df.columns:
            timestamps_df = pd.json_normalize(df['timestamps'])
            df = pd.concat([df.drop(columns=['timestamps']), timestamps_df], axis=1)

        # Ensure the output file directory exists
        os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)

        # Save DataFrame to CSV with explicit file flush
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as f:
            df.to_csv(f, index=False)
            f.flush()
        if self.verbose:
            print(f"File saved: {output_csv_file}")


# Example usage
if __name__ == "__main__":
    # Example messages
    to_csv = MessageToCSVProcessor("validate", "test", save_interval=2, verbose=True)
    for i in range(10):
        msg = {
            'timestamps': {
                'idle': 1.2,
                'pre': 0.0,
                'inf': 2.3,
                'post': 0.0,
                'queue': 0.1,
                'start_time': "2023-01-01T12:00:00",
                'end_time': "2023-01-01T12:00:03"
            },
            'id': f"msg_{i}",
            'errors': None,
            'source': "192.168.1.1",
        }
        to_csv.process_event(msg)
    to_csv.close()
