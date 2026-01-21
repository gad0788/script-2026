import boto3
import sys
import time

def list_snapshots(profile, region, tag_key, tag_value):
    # Create a session with the specified profile and region
    session = boto3.Session(profile_name=profile, region_name=region)
    
    # Create EC2 client
    ec2 = session.client('ec2')

    # Describe snapshots with the specified tag
    response = ec2.describe_snapshots(
        Filters=[
            {
                'Name': f'tag:{tag_key}',
                'Values': [tag_value]
            }
        ],
        OwnerIds=['self']  # Only list snapshots owned by you
    )

    snapshots = response['Snapshots']

    if not snapshots:
        print("No snapshots found with the specified tag.")
        return []

    print("Snapshots with the specified tag:")
    snapshot_info = {}
    for snapshot in snapshots:
        # Get the Name tag if it exists
        name_tag = next((tag['Value'] for tag in snapshot.get('Tags', []) if tag['Key'] == 'Name'), 'No Name Tag')
        snapshot_info[snapshot['SnapshotId']] = name_tag
        print(f"Name: {name_tag}")

    return snapshot_info

def delete_snapshots(profile, region, snapshot_info):
    # Create a session with the specified profile and region
    session = boto3.Session(profile_name=profile, region_name=region)
    
    # Create EC2 client
    ec2 = session.client('ec2')

    for snapshot_id, name in snapshot_info.items():
        try:
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            print(f"Deleted snapshot: {name} (ID: {snapshot_id})")
        except Exception as e:
            print(f"Error deleting snapshot {name} (ID: {snapshot_id}): {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python list_snapshots.py <profile> <region>")
        sys.exit(1)

    profile = sys.argv[1]
    region = sys.argv[2]
    
    tag_key = 'kubernetes.io/created-for/pvc/namespace'
    tag_value = 'cluster_name' # Replace with your actual cluster name/ name of environment
    
    # List snapshots
    snapshot_info = list_snapshots(profile, region, tag_key, tag_value)

    # Pause for 30 seconds
    total_snapshots = len(snapshot_info)
    if total_snapshots > 0:
        print(f"\nTotal snapshots to be deleted: {total_snapshots}")
        print("Pausing for 30 seconds before deletion...")
        time.sleep(30)

        # Confirmation before deletion
        confirm = input(f"Do you want to delete these {total_snapshots} snapshots? (yes/no): ")
        if confirm.lower() == 'yes':
            delete_snapshots(profile, region, snapshot_info)
        else:
            print("Deletion canceled.")
    else:
        print("No snapshots to delete.")

# run: python snapshot_deletion.py profile eu-west-1