import yaml


def update_yolo_model(file_path, new_file_path, new_values_dict):
    # Read the original YAML file
    with open(file_path, 'r') as f:
        data = list(yaml.safe_load_all(f))

    # Find and update the YOLO_MODEL value
    for document in data:
        if document.get('kind', '') == 'Deployment':
            containers = document['spec']['template']['spec']['containers']
            for container in containers:
                if container['name'] == 'yolo-consumer':
                    for env_var in container.get('env', []):
                        if env_var['name'] in new_values_dict.keys():
                            key = env_var['name']
                            new_value = new_values_dict[key]
                            print(f"Updated {key} to {new_value}")
                            env_var['value'] = new_values_dict[key]

    # Save the updated data to a new YAML file
    with open(new_file_path, 'w') as f:
        yaml.dump_all(data, f)
        print(f"Saved new yaml to {new_file_path}")



if __name__ == '__main__':
    # The path to your original YAML file
    original_file_path = 'path/to/original.yaml'
    # The path where you want to save the updated YAML file
    new_file_path = 'path/to/updated.yaml'
    # The new YOLO_MODEL value
    new_model_value = {"YOLO_MODEL": 'new_yolov_value'}

    update_yolo_model("consumer_template.yaml", "experiment_deployment.yaml", new_model_value)
