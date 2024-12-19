import yaml


def update_warehouse_model(file_path, new_file_path, new_values_dict):
    # Read the original YAML file
    with open(file_path, 'r') as f:
        data = list(yaml.safe_load_all(f))

    # Find and update the application values
    for document in data:
        if document.get('kind', '') == 'Deployment':
            containers = document['spec']['template']['spec']['containers']
            for container in containers:
                if container['name'] == 'lidar-worker' or container['name'] == 'lidar-master':
                    # Update all values given as arguments
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
    # Quick testing
    new_model_value = {"KAFKA_SERVERS": 'testestesttestsetsetset'}
    update_warehouse_model("kubernetes_templates/worker_template.yaml", "temp_worker_deployment.yaml", new_model_value)
