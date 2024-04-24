import pytest
from unittest.mock import patch, MagicMock
import sys
print(sys.path)
from scripts.dataProcessing.deduplication import fetch_data_from_firestore, process_products

# Example test for fetch_data_from_firestore
@patch('your_script.firestore')
def test_fetch_data_from_firestore(mock_firestore):
    mock_firestore.client().collection().stream.return_value = [MagicMock(id='1', to_dict=lambda: {'product_id': '1', 'description': 'Product 1'})]
    result = fetch_data_from_firestore()
    assert not result.empty and result.iloc[0]['product_id'] == '1'

# Example test for process_products
def test_process_products():
    old_data = pd.DataFrame({
        'description': ['item1', 'item2'],
        'shop': ['shop1', 'shop2'],
        'popularity': [10, 20],
        'product_id': ['1', '2'],
        'images': ['url1', 'url2'],
        'age': [1, 2]
    })
    new_data = pd.DataFrame({
        'description': ['item1', 'item3'],
        'shop': ['shop1', 'shop3'],
        'popularity': [15, 30],
        'product_id': ['1', '3'],
        'images': ['url1', 'url3'],
        'age': [2, 3]
    })
    expected_data = {
        'description': ['item1', 'item2', 'item3'],
        'shop': ['shop1', 'shop2', 'shop3'],
        'popularity': [12.5, 20, 30],  # Averaging test
        'product_id': ['1', '2', '3'],
        'images': ['url1', 'url2', 'url3'],
        'age': [2, 2, 3]
    }
    processed = process_products(old_data, new_data)
    pd.testing.assert_frame_equal(processed, pd.DataFrame(expected_data))
