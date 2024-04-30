import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import os
from glob import glob

'''
Because shop name isn't always available, we will mainly rely on product description to find duplicated, and only remove those with the same shop name
and description
When items are found as duplicates, then we give it popularity of their average due to not knowing how many people were on different sites.

Workflow to follow:
Initialize Firebase: Set up Firebase connection.
Fetch Data: Retrieve already existing data from previous versions from Firestore.
Read and Combine New Data: Load new data from CSV files and combine it.
Process Data: Deduplicate and aggregate combined data.
Update Firestore: Upload the processed data back to Firestore.
 '''
# Get the path to the directory where this script is running
current_file_path = Path(__file__).resolve()

# Traverse up to find the FYP directory (assuming this script is somewhere inside the FYP directory)
fyp_directory = current_file_path.parent
while fyp_directory.name != 'FYP' and fyp_directory.parent != fyp_directory:
    fyp_directory = fyp_directory.parent

# Now append the relative path to the key file within the FYP directory
firebase_key_path = fyp_directory / 'fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'

# Check if the path exists
if not firebase_key_path.exists():
    raise FileNotFoundError(f"Firebase key file not found at {firebase_key_path}")

cred = credentials.Certificate(str(fyp_directory))
firebase_admin.initialize_app(cred)
db = firestore.client()

#Fetch existing product data from Firestore. Return an empty DataFrame with predefined columns if no data exists.
def fetch_data_from_firestore():
    try:
        collections = db.collection('products').stream()
        data = [{'product_id': doc.id, **doc.to_dict()} for doc in collections]
        if not data:
            # Return an empty DataFrame with expected columns if no documents are found
            return pd.DataFrame(columns=['product_id', 'description', 'shop', 'popularity', 'images', 'age'])
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Failed to fetch data from Firestore: {e}")
        return pd.DataFrame(columns=['product_id', 'description', 'shop', 'popularity', 'images', 'age'])


# function to fetch data from csv files and return a dataframe
def combine_and_process_csv_files(directory_path):
    csv_files = glob(os.path.join(directory_path, '*.csv'))
    all_data = pd.DataFrame()

    for file in csv_files:
        print(f"Processing file: {os.path.basename(file)}")  # Print the name of the current file

        df = pd.read_csv(file)
        all_data = pd.concat([all_data, df], ignore_index=True)

    # processed_products = process_products(all_data)
    return all_data

#Merge old and new product data, then deduplicate and process.
def process_products(old_data, new_data):
    if old_data.empty:
        combined_data = new_data
    else:
        combined_data = pd.concat([old_data, new_data], ignore_index=True)
    
    combined_data['shop'] = combined_data['shop'].fillna('None')
    processed_data = combined_data.groupby(['description', 'shop']).agg({
        'product_id': 'first',  # Keep the first product_id encountered
        'images': 'first',  # Keep the first image URL encountered
        'popularity': 'mean',  # Average popularity
        'age': 'max'  # Use the highest age to signify that it is the most recent
    }).reset_index()
    return processed_data

def update_firebase(data):
    """Update Firestore with processed product data."""
    if data.empty:
        print("No data to update in Firestore.")
        return

    for _, row in data.iterrows():
        composite_id = create_composite_id(row['product_id'], row['shop'])
        product_ref = db.collection('products').document(composite_id)
        product_ref.set(row.to_dict(), merge=True)
        print(f"Product added with ID: {composite_id}")

def create_composite_id(product_id, website):
    """Generate a unique document ID based on product_id and website."""
    return f"{product_id}_{website}"

if __name__ == "__main__":
    # Fetch existing data from Firestore
    existing_data = fetch_data_from_firestore()

    # Path to the directory containing new data CSVs
    directory_path = 'path_to_your_directory'
    new_data = combine_and_process_csv_files(directory_path)

    # Process and merge the existing and new data
    processed_data = process_products(existing_data, new_data)

    # Update Firestore with the processed data
    update_firebase(processed_data)