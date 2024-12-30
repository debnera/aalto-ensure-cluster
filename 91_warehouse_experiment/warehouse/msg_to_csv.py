import pandas as pd
import os


class MessageToCSVProcessor:
    def __init__(self, output_folder, name_prefix, save_interval=1000):
        self.messages = []
        self.name_prefix = name_prefix
        self.output_folder = output_folder
        self.save_interval = save_interval
        self.save_counter = 0

    def process_event(self, msg_dict):
        self.messages.append(msg_dict)
        if len(self.messages) % self.save_interval == 0:
            self.save_and_clear()

    def close(self):
        self.save_and_clear()

    def save_and_clear(self):
        if len(self.messages) == 0:
            return
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

        # Save DataFrame to CSV
        df.to_csv(output_csv_file, index=False)


# Example usage
if __name__ == "__main__":
    # Example messages
    to_csv = MessageToCSVProcessor("validate", save_interval=2)
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
