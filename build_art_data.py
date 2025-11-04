import os
import pandas as pd
from typing import Tuple, Dict, List

def load_data(data_dir: str = '.') -> Dict[str, pd.DataFrame]:
    files = {
        'artist': 'artist.csv',
        'artwork': 'artwork.csv',
        'image_asset': 'image_asset.csv',
        'user': 'user.csv',
        'artwork_financial': 'artwork_financial.csv',
    }
    data = {}
    for key, fname in files.items():
        path = os.path.join(data_dir, fname)
        df = pd.read_csv(path)
        print(f"Loaded {key}: columns={list(df.columns)}")
        data[key] = df
    return data

def validate_links(data: Dict[str, pd.DataFrame]) -> List[str]:
    warnings = []
    # artwork.artist_id → artist.artist_id
    missing_artist = set(data['artwork']['artist_id']) - set(data['artist']['artist_id'])
    if missing_artist:
        warnings.append(f"artwork.artist_id missing in artist.artist_id: {missing_artist}")
    # image_asset.artwork_id → artwork.artwork_id
    missing_artwork_img = set(data['image_asset']['artwork_id']) - set(data['artwork']['artwork_id'])
    if missing_artwork_img:
        warnings.append(f"image_asset.artwork_id missing in artwork.artwork_id: {missing_artwork_img}")
    # artwork.image_primary_id → image_asset.image_id
    missing_img_primary = set(data['artwork']['image_primary_id']) - set(data['image_asset']['image_id'])
    if missing_img_primary:
        warnings.append(f"artwork.image_primary_id missing in image_asset.image_id: {missing_img_primary}")
    # artwork_financial.artwork_id → artwork.artwork_id
    missing_artwork_fin = set(data['artwork_financial']['artwork_id']) - set(data['artwork']['artwork_id'])
    if missing_artwork_fin:
        warnings.append(f"artwork_financial.artwork_id missing in artwork.artwork_id: {missing_artwork_fin}")
    return warnings

def merge_data(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    # Merge artwork with artist
    df = pd.merge(data['artwork'], data['artist'], left_on='artist_id', right_on='artist_id', suffixes=('_artwork', '_artist'))
    # Merge artwork with image_asset (primary image)
    df = pd.merge(df, data['image_asset'], left_on='image_primary_id', right_on='image_id', suffixes=('', '_image'))
    # Merge artwork with financials (may be multiple per artwork)
    df = pd.merge(df, data['artwork_financial'], left_on='artwork_id', right_on='artwork_id', how='left', suffixes=('', '_financial'))
    return df

def analyze_data(merged_df: pd.DataFrame) -> pd.DataFrame:
    # Count artworks per artist
    count_per_artist = merged_df.groupby('artist_id').size().rename('artwork_count')
    # Total and average financial values per artist
    financial = merged_df.groupby('artist_id')['price_amount'].agg(['sum', 'mean']).rename(columns={'sum': 'total_price', 'mean': 'avg_price'})
    # Merge with artist name
    artist_names = merged_df.groupby('artist_id')['name'].first()
    summary = pd.concat([artist_names, count_per_artist, financial], axis=1).reset_index()
    return summary

def main():
    data = load_data()
    warnings = validate_links(data)
    if warnings:
        print("Validation Warnings:")
        for w in warnings:
            print("-", w)
    else:
        print("All key relationships validated.")
    merged_df = merge_data(data)
    summary_df = analyze_data(merged_df)
    # Output directories
    out_dir = 'out'
    os.makedirs(out_dir, exist_ok=True)
    merged_df.to_csv(os.path.join(out_dir, 'artworks_enriched.csv'), index=False)
    summary_df.to_csv(os.path.join(out_dir, 'summary_by_artist.csv'), index=False)
    print("\nSummary by artist:")
    print(summary_df)
    print(f"\nSaved enriched data to {os.path.join(out_dir, 'artworks_enriched.csv')}")
    print(f"Saved summary to {os.path.join(out_dir, 'summary_by_artist.csv')}")

if __name__ == "__main__":
    main()
